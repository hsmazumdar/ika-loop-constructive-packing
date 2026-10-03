"""GPU placement workspace.

The catalogue is 100 cells, so the working tensors are small. They stay on the
CUDA device for candidate scoring and for the teacher beam. Peak allocated
bytes are reported. No dummy allocation is used to inflate memory use.
"""

from __future__ import annotations

from mga3.pieces import ALL_PLACEMENTS, BOARD_SIZE, N_CELLS, PIECE_TYPES


class PlacementWorkspace:
    def __init__(self, device: str = "cuda") -> None:
        import torch

        self.torch = torch
        if device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("config requested cuda but torch.cuda.is_available() is false")
        self.device = torch.device(device if device == "cuda" or device == "cpu" else "cpu")
        n = len(ALL_PLACEMENTS)
        masks = torch.zeros((n, N_CELLS), dtype=torch.float32, device=self.device)
        neigh = torch.zeros((n, N_CELLS), dtype=torch.float32, device=self.device)
        areas = torch.zeros(n, dtype=torch.float32, device=self.device)
        types = torch.zeros(n, dtype=torch.long, device=self.device)
        boundary = torch.zeros(n, dtype=torch.float32, device=self.device)
        type_index = {name: i for i, name in enumerate(PIECE_TYPES)}
        for i, placement in enumerate(ALL_PLACEMENTS):
            for x, y in placement.cells:
                masks[i, y * BOARD_SIZE + x] = 1.0
            bit = placement.neighbor_mask
            while bit:
                b = bit & -bit
                bit ^= b
                neigh[i, b.bit_length() - 1] = 1.0
            areas[i] = float(placement.area)
            types[i] = type_index[placement.piece_type]
            boundary[i] = float(placement.boundary_contacts)
        self.masks = masks
        self.neigh = neigh
        self.areas = areas
        self.types = types
        self.boundary = boundary
        self.gpu_ops = 0
        self.type_index = type_index

    def memory_bytes(self) -> int:
        if self.device.type != "cuda":
            return 0
        return int(self.torch.cuda.memory_allocated(self.device))

    def device_name(self) -> str:
        if self.device.type != "cuda":
            return "cpu"
        return str(self.torch.cuda.get_device_name(self.device))

    def score_indices(self, board_mask: int, indices: list[int]) -> tuple[list[bool], list[float]]:
        """Charge the caller once per index. This computes only those rows."""
        if not indices:
            return [], []
        torch = self.torch
        board = torch.zeros(N_CELLS, dtype=torch.float32, device=self.device)
        bit = board_mask
        while bit:
            b = bit & -bit
            bit ^= b
            board[b.bit_length() - 1] = 1.0
        idx = torch.tensor(indices, dtype=torch.long, device=self.device)
        sub = self.masks.index_select(0, idx)
        nb = self.neigh.index_select(0, idx)
        overlap = torch.mv(sub, board) > 0.5
        contact = torch.mv(nb, board)
        self.gpu_ops += 1
        return [bool(v) for v in overlap.detach().cpu().tolist()], [float(v) for v in contact.detach().cpu().tolist()]

    def beam_fill(
        self,
        inventory: dict[str, int],
        trajectories: int,
        seed: int,
        max_steps: int = 24,
    ) -> list[dict]:
        """Greedy beam on CUDA. Returns the best trajectory if it places anything."""
        torch = self.torch
        generator = torch.Generator(device="cpu")
        generator.manual_seed(int(seed))
        n_place = self.masks.shape[0]
        boards = torch.zeros((trajectories, N_CELLS), dtype=torch.float32, device=self.device)
        counts = torch.tensor(
            [int(inventory.get(name, 0)) for name in PIECE_TYPES],
            dtype=torch.long,
            device=self.device,
        ).unsqueeze(0).repeat(trajectories, 1)
        alive = torch.ones(trajectories, dtype=torch.bool, device=self.device)
        picks: list = []
        for _ in range(max_steps):
            if not bool(alive.any()):
                break
            overlap = torch.matmul(boards, self.masks.T)
            type_ok = counts[:, self.types] > 0
            legal = (overlap <= 0.5) & type_ok & alive.unsqueeze(1)
            contact = torch.matmul(boards, self.neigh.T)
            noise = torch.rand((trajectories, n_place), generator=generator).to(self.device)
            score = self.areas.unsqueeze(0) + 0.15 * contact + 0.35 * noise + 0.01 * self.boundary.unsqueeze(0)
            score = score.masked_fill(~legal, -1.0e9)
            best = score.max(dim=1).values
            choice = score.argmax(dim=1)
            can = best > -1.0e8
            chosen = self.masks.index_select(0, choice)
            boards = torch.where(can.unsqueeze(1), torch.clamp(boards + chosen, max=1.0), boards)
            t_idx = self.types.index_select(0, choice)
            rows = torch.arange(trajectories, device=self.device)
            counts[rows, t_idx] -= can.long()
            alive = alive & can
            picks.append(choice.detach().cpu())
            self.gpu_ops += 1
        filled = boards.sum(dim=1).detach().cpu()
        if filled.numel() == 0:
            return []
        best_i = int(filled.argmax())
        placed = []
        for step_choices in picks:
            index = int(step_choices[best_i])
            # A dead trajectory repeats the last argmax of an all-masked row (0).
            placed.append(index)
        # Trim trailing steps that did not increase this trajectory. Reconstruct
        # by replaying indices until a placement would overlap or exhaust inventory.
        return self._replay_indices(inventory, placed)

    def _replay_indices(self, inventory: dict[str, int], indices: list[int]) -> list[dict]:
        from mga3.pieces import ALL_PLACEMENTS

        remaining = {t: int(inventory.get(t, 0)) for t in PIECE_TYPES}
        mask = 0
        out = []
        for index in indices:
            placement = ALL_PLACEMENTS[index]
            if remaining.get(placement.piece_type, 0) <= 0:
                break
            if placement.mask & mask:
                break
            remaining[placement.piece_type] -= 1
            mask |= placement.mask
            out.append(
                {
                    "type": placement.piece_type,
                    "rotation": placement.rotation,
                    "x": placement.x,
                    "y": placement.y,
                    "cells": [list(c) for c in placement.cells],
                }
            )
        return out
