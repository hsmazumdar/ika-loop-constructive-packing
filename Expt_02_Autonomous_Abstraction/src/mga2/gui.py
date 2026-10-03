"""Observable demonstration UI.

Manual play uses a separate session and does not write scientific training checkpoints.
Descriptions come from the live AST and logs.
"""

from __future__ import annotations

import json
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from mga2.environment import Action, PackingEnv
from mga2.inventory import Inventory
from mga2.pieces import BOARD_SIZE, PIECE_COLORS, PIECE_TYPES
from mga2.render import save_boards
from mga2.selection import Agent, make_ledger, new_library

CELL = 28
ROOT = Path(__file__).resolve().parents[2]


def _default_config() -> dict:
    path = ROOT / "configs" / "default.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"board_size": 10, "budgets": {"physical_actions": 100}, "memory": {"stm_bytes": 65536, "ltm_bytes": 262144}}


class DemoApp:
    def __init__(self, root: tk.Tk, config: dict | None = None) -> None:
        self.root = root
        self.config = config or _default_config()
        self.root.title("MGA Expt-2 demonstration (manual session)")
        self.mode = tk.StringVar(value="hierarchical_library")
        self.speed = tk.IntVar(value=200)
        self.running = False
        self.selected_type = tk.StringVar(value="A")
        self.rotation = tk.IntVar(value=0)
        self.ltm = new_library(self.config)
        self.env = PackingEnv(budget=int(self.config.get("budgets", {}).get("physical_actions", 100)))
        self.agent = Agent(self.mode.get(), self.config, self.ltm, frozen=False)
        self.agent.begin_box(0, "demo")
        self.ledger = make_ledger(self.config)
        self.rngs = self._rngs()
        self._build()
        self.refresh()

    def _rngs(self):
        import random

        return random.Random(0), random.Random(1), random.Random(2)

    def _build(self) -> None:
        top = ttk.Frame(self.root)
        top.pack(fill="x")
        ttk.Label(top, text="Manual demonstration session. This memory is not a scientific checkpoint.").pack(side="left", padx=6)
        boards = ttk.Frame(self.root)
        boards.pack(fill="both", expand=True)
        left = ttk.Frame(boards)
        left.pack(side="left", padx=6, pady=6)
        ttk.Label(left, text="Real board").pack(anchor="w")
        self.real = tk.Canvas(left, width=CELL * BOARD_SIZE, height=CELL * BOARD_SIZE, bg="#f4f7fb", highlightthickness=1)
        self.real.pack()
        self.real.bind("<Button-1>", self._click_place)
        right = ttk.Frame(boards)
        right.pack(side="left", padx=6, pady=6)
        ttk.Label(right, text="SIMULATION").pack(anchor="w")
        self.sim = tk.Canvas(right, width=CELL * BOARD_SIZE, height=CELL * BOARD_SIZE, bg="#f7f1e8", highlightthickness=1)
        self.sim.pack()
        side = ttk.Frame(boards)
        side.pack(side="left", fill="both", expand=True, padx=6)
        self.status = tk.StringVar()
        ttk.Label(side, textvariable=self.status, justify="left").pack(anchor="w")
        ttk.Label(side, text="STM candidates").pack(anchor="w")
        self.stm_list = tk.Listbox(side, height=6, width=42)
        self.stm_list.pack(fill="x")
        self.stm_list.bind("<<ListboxSelect>>", self._show_selected)
        ttk.Label(side, text="LTM library").pack(anchor="w")
        self.ltm_list = tk.Listbox(side, height=6, width=42)
        self.ltm_list.pack(fill="x")
        self.ltm_list.bind("<<ListboxSelect>>", self._show_selected)
        self.detail = tk.Text(side, height=10, width=46, wrap="word")
        self.detail.pack(fill="both", expand=True)
        ttk.Label(side, text="Timeline").pack(anchor="w")
        self.timeline = tk.Listbox(side, height=6, width=42)
        self.timeline.pack(fill="x")
        controls = ttk.Frame(self.root)
        controls.pack(fill="x", padx=6, pady=6)
        ttk.Button(controls, text="Pause", command=self.pause).pack(side="left")
        ttk.Button(controls, text="Internal step", command=self.internal_step).pack(side="left")
        ttk.Button(controls, text="Physical step", command=self.physical_step).pack(side="left")
        ttk.Button(controls, text="Run", command=self.run).pack(side="left")
        ttk.Scale(controls, from_=20, to=800, variable=self.speed, orient="horizontal", length=120).pack(side="left", padx=6)
        ttk.Button(controls, text="New box", command=self.new_box).pack(side="left")
        ttk.Button(controls, text="Reset learning", command=self.reset_learning).pack(side="left")
        ttk.Button(controls, text="Undo", command=self.manual_undo).pack(side="left")
        ttk.Button(controls, text="Submit", command=self.manual_submit).pack(side="left")
        ttk.Button(controls, text="Snapshot", command=self.snapshot).pack(side="left")
        ttk.Button(controls, text="Save demo", command=self.save_demo).pack(side="left")
        ttk.Button(controls, text="Load demo", command=self.load_demo).pack(side="left")
        type_row = ttk.Frame(self.root)
        type_row.pack(fill="x", padx=6, pady=4)
        ttk.Label(type_row, text="Manual type").pack(side="left")
        ttk.Combobox(type_row, textvariable=self.selected_type, values=list(PIECE_TYPES), width=4, state="readonly").pack(side="left")
        ttk.Label(type_row, text="rotation").pack(side="left")
        ttk.Spinbox(type_row, from_=0, to=3, textvariable=self.rotation, width=4).pack(side="left")
        ttk.Combobox(type_row, textvariable=self.mode, values=["primitive", "search_only", "flat_library", "hierarchical_library", "engineered_reference"], width=22, state="readonly").pack(side="left", padx=8)
        ttk.Button(type_row, text="Apply mode", command=self.apply_mode).pack(side="left")

    def _draw(self, canvas: tk.Canvas, env: PackingEnv | None) -> None:
        canvas.delete("all")
        for y in range(BOARD_SIZE):
            for x in range(BOARD_SIZE):
                label = ""
                if env is not None and env.cells[y][x] is not None:
                    label = env.cells[y][x][0]
                color = PIECE_COLORS.get(label, "#ffffff") if label else "#ffffff"
                canvas.create_rectangle(x * CELL, y * CELL, (x + 1) * CELL, (y + 1) * CELL, fill=color, outline="#c5d0de")
                if label:
                    canvas.create_text(x * CELL + CELL / 2, y * CELL + CELL / 2, text=label, fill="#102033")

    def refresh(self) -> None:
        self._draw(self.real, self.env)
        self._draw(self.sim, self.agent.simulation_env)
        inv = "unlimited" if self.env.inventory.unlimited else " ".join(
            f"{k}{v}" for k, v in self.env.inventory.as_dict().items() if v
        )
        decision = self.agent.last_decision
        self.status.set(
            f"score {self.env.score}/100  best {self.env.best_score}  blanks {self.env.blanks}\n"
            f"physical {self.env.actions_used}/{self.env.budget}  evals {self.ledger.candidate_evals}  "
            f"model {self.ledger.model_transitions}  think {self.ledger.think_batches}  "
            f"macros {self.ledger.macro_invocations}\n"
            f"inventory {inv or '(empty)'}\n"
            f"choice {decision.get('source')}  reason {decision.get('reason')}  "
            f"ucb {decision.get('ucb')}  op {decision.get('op_id', '')}"
        )
        self.stm_list.delete(0, "end")
        for op in self.agent.stm.candidates.values():
            self.stm_list.insert("end", f"{op.op_id} {op.source} d={op.depth}")
        self.ltm_list.delete(0, "end")
        for op in self.ltm.ops.values():
            self.ltm_list.insert("end", f"{op.op_id} {op.status} uses={op.stats.get('real_uses')}")
        self.timeline.delete(0, "end")
        for event in self.agent.events[-12:]:
            self.timeline.insert("end", f"{event.get('type')} {event.get('op_id', '')} {event.get('reject_reason', event.get('reason', ''))}")

    def _selected_op(self):
        for box, pool in ((self.stm_list, self.agent.stm.candidates), (self.ltm_list, self.ltm.ops)):
            sel = box.curselection()
            if not sel:
                continue
            label = box.get(sel[0])
            op_id = label.split()[0]
            if op_id in pool:
                return pool[op_id]
        return None

    def _show_selected(self, _event=None) -> None:
        op = self._selected_op()
        self.detail.delete("1.0", "end")
        if op is None:
            return
        text = (
            f"id {op.op_id}\nstatus {op.status}\nsource {op.source}\nprovenance {op.provenance}\n"
            f"parents {op.parents}\ndepth {op.depth}\nbytes {op.logical_bytes()}\n"
            f"inventory {op.inventory_counts}\n"
            f"real uses {op.stats.get('real_uses')} sim uses {op.stats.get('sim_uses')}\n"
            f"tasks {op.stats.get('real_task_ids')}\norigins {op.stats.get('origins')}\n"
            f"utility_sum {op.stats.get('utility_sum')} paired {op.stats.get('paired_utility_sum')}\n"
            f"AST {json.dumps(op.ast, sort_keys=True)}\n"
            f"expansion {json.dumps(op.primitive_sequence)}\n"
        )
        self.detail.insert("1.0", text)

    def pause(self) -> None:
        self.running = False

    def apply_mode(self) -> None:
        self.pause()
        self.ltm = new_library(self.config)
        self.agent = Agent(self.mode.get(), self.config, self.ltm, frozen=False)
        self.new_box()

    def new_box(self) -> None:
        self.pause()
        self.env = PackingEnv(budget=int(self.config.get("budgets", {}).get("physical_actions", 100)))
        self.ledger = make_ledger(self.config)
        self.agent.begin_box(0, "demo")
        self.refresh()

    def reset_learning(self) -> None:
        self.pause()
        self.ltm = new_library(self.config)
        self.agent = Agent(self.mode.get(), self.config, self.ltm, frozen=False)
        self.new_box()

    def physical_step(self) -> None:
        if self.env.terminal:
            self.refresh()
            return
        # One dispatcher decision. A library THINK may not place a piece.
        before = self.env.actions_used
        self.agent.decide_and_act(self.env, self.ledger, *self.rngs)
        if self.env.actions_used == before and not self.env.terminal:
            self.agent.decide_and_act(self.env, self.ledger, *self.rngs)
        self.refresh()

    def internal_step(self) -> None:
        """One mental step. The real board is not changed."""
        if self.env.terminal:
            return
        mask = self.env.mask
        self.agent.simulation_env = self.env.clone()
        if self.agent.mode in {"flat_library", "hierarchical_library"}:
            self.agent._think_library(self.env, self.ledger, self.rngs[1], self.rngs[2])
        else:
            from mga2.simulation import lookahead_first_action

            action = lookahead_first_action(
                self.env,
                self.ledger,
                self.rngs[1],
                self.agent.lookahead_depth,
                self.agent.lookahead_width,
                self.agent.weights,
                self.agent.exam_limit,
            )
            if action is not None:
                self.agent.simulation_env.step(action)
        if self.env.mask != mask:
            raise RuntimeError("internal step changed the real board")
        self.refresh()

    def run(self) -> None:
        self.running = True
        self._tick()

    def _tick(self) -> None:
        if not self.running or self.env.terminal:
            self.running = False
            self.refresh()
            return
        self.physical_step()
        self.root.after(int(self.speed.get()), self._tick)

    def _click_place(self, event) -> None:
        x, y = event.x // CELL, event.y // CELL
        self.env.step(Action.place(self.selected_type.get(), int(self.rotation.get()), x, y))
        self.ledger.physical = self.env.actions_used
        self.refresh()

    def manual_undo(self) -> None:
        self.env.step(Action.undo())
        self.ledger.physical = self.env.actions_used
        self.refresh()

    def manual_submit(self) -> None:
        self.env.step(Action.submit())
        self.refresh()

    def snapshot(self) -> None:
        out = ROOT / "results" / "gui_demo"
        out.mkdir(parents=True, exist_ok=True)
        sim = self.agent.simulation_env.occupancy_grid() if self.agent.simulation_env else [[""] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        path = out / "snapshot.png"
        save_boards(self.env.occupancy_grid(), sim, path, footer=self.status.get().replace("\n", " | "))
        messagebox.showinfo("Snapshot", str(path))

    def save_demo(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".json", initialdir=str(ROOT / "results"))
        if not path:
            return
        payload = {"ltm": self.ltm.to_dict(), "note": "manual demonstration session"}
        Path(path).write_text(json.dumps(payload), encoding="utf-8")

    def load_demo(self) -> None:
        path = filedialog.askopenfilename(initialdir=str(ROOT / "results"))
        if not path:
            return
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        from mga2.ltm import LongTermMemory

        self.ltm = LongTermMemory.from_dict(payload["ltm"])
        self.agent = Agent(self.mode.get(), self.config, self.ltm, frozen=False)
        self.new_box()


def launch() -> None:
    root = tk.Tk()
    DemoApp(root)
    root.mainloop()
