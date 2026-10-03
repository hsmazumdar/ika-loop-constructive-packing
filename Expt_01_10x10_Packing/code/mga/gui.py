"""Instructive Tkinter desktop app for MGA Expt-1.

Simulation logic lives in mga.environment / mga.agent. This module only draws
and dispatches user or scheduled actions on the UI thread.
"""

from __future__ import annotations

import json
import random
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

from mga.agent import MODES, PackingAgent
from mga.environment import Action, PackingEnv
from mga.experiment import load_config
from mga.memory import LongTermMemory, config_hash
from mga.paths import DATA_DIR, RESULTS_DIR, SNAPSHOTS_DIR
from mga.pieces import (
    BOARD_SIZE,
    PIECE_COLORS,
    PIECE_TYPES,
    PIECES,
    catalogue_hash,
    in_bounds,
    orientation,
    placed_cells,
)
from mga.render import save_populated_canvas

BG = "#e8eef6"
NAVY = "#1b365d"
CARD = "#ffffff"
MUTED = "#5b6b80"
ACCENT = "#2f6fed"


class BoardCanvas(tk.Canvas):
    def __init__(self, master, cell=36, **kwargs):
        self.cell = cell
        self.label_w = 22
        w = self.label_w + BOARD_SIZE * cell + 8
        h = self.label_w + BOARD_SIZE * cell + 8
        super().__init__(
            master,
            width=w,
            height=h,
            bg=CARD,
            highlightthickness=0,
            **kwargs,
        )
        self.env: PackingEnv | None = None
        self.preview_cells = None
        self.preview_ok = False
        self.bind("<Motion>", self._on_motion)
        self.bind("<Leave>", lambda e: self._clear_preview())
        self.bind("<Button-1>", self._on_click)
        self.anchor_callback = None
        self.hover_xy = None

    def _origin(self) -> tuple[int, int]:
        return self.label_w, self.label_w

    def cell_at(self, event) -> tuple[int, int] | None:
        ox, oy = self._origin()
        x = (event.x - ox) // self.cell
        y = (event.y - oy) // self.cell
        if 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
            return int(x), int(y)
        return None

    def _on_motion(self, event) -> None:
        if self.anchor_callback:
            self.anchor_callback("hover", self.cell_at(event))

    def _on_click(self, event) -> None:
        if self.anchor_callback:
            self.anchor_callback("click", self.cell_at(event))

    def _clear_preview(self) -> None:
        self.preview_cells = None
        if self.env is not None:
            self.redraw(self.env)

    def set_preview(self, cells, ok: bool) -> None:
        self.preview_cells = cells
        self.preview_ok = ok
        if self.env is not None:
            self.redraw(self.env)

    def redraw(self, env: PackingEnv) -> None:
        self.env = env
        self.delete("all")
        ox, oy = self._origin()
        c = self.cell
        self.create_rectangle(0, 0, int(self["width"]), int(self["height"]), fill=CARD, outline="")
        for i in range(BOARD_SIZE):
            self.create_text(
                ox + i * c + c / 2,
                oy - 10,
                text=str(i + 1),
                fill=NAVY,
                font=("Segoe UI", 8, "bold"),
            )
            self.create_text(
                ox - 12,
                oy + i * c + c / 2,
                text=str(i + 1),
                fill=NAVY,
                font=("Segoe UI", 8, "bold"),
            )
        for y in range(BOARD_SIZE):
            for x in range(BOARD_SIZE):
                x0, y0 = ox + x * c, oy + y * c
                cell = env.cells[y][x]
                if cell is None:
                    fill = "#ffffff"
                    self.create_rectangle(x0, y0, x0 + c, y0 + c, fill=fill, outline="#c5d0de")
                else:
                    ptype, _iid = cell
                    self.create_rectangle(
                        x0, y0, x0 + c, y0 + c, fill=PIECE_COLORS[ptype], outline="#dfe7f0"
                    )
                    self.create_text(
                        x0 + c / 2,
                        y0 + c / 2,
                        text=ptype,
                        fill="#102033",
                        font=("Segoe UI", 10, "bold"),
                    )
        for inst in env.stack:
            self._outline(inst.cells, ox, oy, c)
        if self.preview_cells:
            color = "#1b9c5a" if self.preview_ok else "#d64545"
            for x, y in self.preview_cells:
                if 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
                    x0, y0 = ox + x * c, oy + y * c
                    self.create_rectangle(
                        x0 + 3,
                        y0 + 3,
                        x0 + c - 3,
                        y0 + c - 3,
                        outline=color,
                        width=2,
                    )

    def _outline(self, cells, ox, oy, c) -> None:
        cellset = set(cells)
        for x, y in cells:
            x0, y0 = ox + x * c, oy + y * c
            if (x, y - 1) not in cellset:
                self.create_line(x0, y0, x0 + c, y0, fill=NAVY, width=3)
            if (x, y + 1) not in cellset:
                self.create_line(x0, y0 + c, x0 + c, y0 + c, fill=NAVY, width=3)
            if (x - 1, y) not in cellset:
                self.create_line(x0, y0, x0, y0 + c, fill=NAVY, width=3)
            if (x + 1, y) not in cellset:
                self.create_line(x0 + c, y0, x0 + c, y0 + c, fill=NAVY, width=3)


class CatalogueCanvas(tk.Canvas):
    def __init__(self, master, on_select, **kwargs):
        super().__init__(master, width=280, height=280, bg=CARD, highlightthickness=0, **kwargs)
        self.on_select = on_select
        self.selected = "A"
        self.bind("<Button-1>", self._click)
        self.redraw()

    def _click(self, event) -> None:
        col = event.x // 70
        row = event.y // 70
        idx = row * 4 + col
        if 0 <= idx < 16:
            self.selected = PIECE_TYPES[idx]
            self.redraw()
            self.on_select(self.selected)

    def redraw(self) -> None:
        self.delete("all")
        self.create_rectangle(0, 0, 280, 280, fill=CARD, outline="")
        for i, name in enumerate(PIECE_TYPES):
            gx, gy = i % 4, i // 4
            x0, y0 = gx * 70, gy * 70
            border = ACCENT if name == self.selected else "#d5deea"
            width = 3 if name == self.selected else 1
            self.create_rectangle(x0 + 4, y0 + 4, x0 + 66, y0 + 66, outline=border, width=width, fill="#f8fbff")
            cells = orientation(PIECES[name], 0)
            max_x = max(c[0] for c in cells) + 1
            max_y = max(c[1] for c in cells) + 1
            scale = 44 / max(max_x, max_y, 3)
            sx = x0 + 10
            sy = y0 + 12
            for cx, cy in cells:
                self.create_rectangle(
                    sx + cx * scale,
                    sy + cy * scale,
                    sx + cx * scale + scale * 0.9,
                    sy + cy * scale + scale * 0.9,
                    fill=PIECE_COLORS[name],
                    outline=NAVY,
                )
            self.create_text(x0 + 58, y0 + 14, text=name, fill=NAVY, font=("Segoe UI", 8, "bold"))


class MGAApp(tk.Tk):
    def __init__(self, start_demo: bool = False) -> None:
        super().__init__()
        self.title("MGA  ·  Expt-1: 10×10 Packing")
        self.configure(bg=BG)
        self.geometry("1280x860")
        self.minsize(1100, 760)
        start_demo = bool(start_demo)

        self.config_data = load_config()
        self.cfg_hash = config_hash(self.config_data)
        self.mode = tk.StringVar(value="both")
        self.seed = tk.IntVar(value=11)
        self.speed_ms = tk.IntVar(value=80)
        self.rotation = tk.IntVar(value=0)
        self.selected_piece = "A"
        self.play_mode = tk.StringVar(value="manual")
        self.env = PackingEnv(budget=int(self.config_data["action_budget"]))
        self.ltm_store: dict[str, LongTermMemory] = {m: self._fresh_ltm() for m in MODES}
        self.agent = self._make_agent(self.mode.get())
        self.rng = random.Random(self.seed.get())
        self.running = False
        self.paused = True
        self.episode_index = 1
        self.train_scores: list[float] = []
        self.status = tk.StringVar(value="Manual mode. Choose a piece, a rotation, then click an anchor cell.")
        self._tick_job = None

        self._build()
        self._refresh()
        if start_demo:
            self.speed_ms.set(70)
            self.mode.set("both")
            self.play_mode.set("training")
            self.status.set("Demo: autonomous packing with STM+LTM. Pause stops before the next action.")
            self.after(400, self.start)

    def _fresh_ltm(self) -> LongTermMemory:
        ltm = LongTermMemory(
            capacity=int(self.config_data["ltm_capacity"]),
            coefficient=float(self.config_data["ltm_coefficient"]),
            shrinkage_k=int(self.config_data["ltm_shrinkage_k"]),
        )
        ltm.config_hash = self.cfg_hash
        ltm.catalogue_hash = catalogue_hash()
        return ltm

    def _make_agent(self, mode: str) -> PackingAgent:
        agent = PackingAgent(mode=mode, config=self.config_data, ltm=self.ltm_store[mode])
        agent.begin_box()
        return agent

    def _build(self) -> None:
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=18, pady=(12, 4))
        tk.Label(
            header,
            text="MGA  /  MEMORY-GUIDED ASSEMBLY",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w")
        tk.Label(
            header,
            text="Expt-1: 10 × 10 Packing",
            bg=BG,
            fg=NAVY,
            font=("Segoe UI", 22, "bold"),
        ).pack(anchor="w")
        tk.Label(
            header,
            text="One agent  ·  16 piece types  ·  four rotations  ·  100-action budget  ·  score = occupied cells",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9),
        ).pack(anchor="w")

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=18, pady=8)

        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="both", expand=True)
        self.board = BoardCanvas(left, cell=38)
        self.board.pack(anchor="nw")
        self.board.anchor_callback = self._on_board_event

        self.score_var = tk.StringVar()
        tk.Label(
            left,
            textvariable=self.score_var,
            bg=BG,
            fg=NAVY,
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w", pady=(10, 0))
        self.meta_var = tk.StringVar()
        tk.Label(left, textvariable=self.meta_var, bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w")

        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=(16, 0))
        tk.Label(right, text="PIECE CATALOGUE  A–P", bg=BG, fg=NAVY, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.catalogue = CatalogueCanvas(right, on_select=self._on_piece)
        self.catalogue.pack(anchor="nw", pady=(4, 8))

        rot = tk.Frame(right, bg=BG)
        rot.pack(anchor="w", pady=(0, 8))
        tk.Label(rot, text="Rotation", bg=BG, fg=NAVY, font=("Segoe UI", 9, "bold")).pack(side="left")
        for k, label in enumerate(("0°", "90°", "180°", "270°")):
            tk.Radiobutton(
                rot,
                text=label,
                value=k,
                variable=self.rotation,
                bg=BG,
                command=self._clear_hover,
                font=("Segoe UI", 9),
            ).pack(side="left", padx=4)

        help_txt = (
            "Choose piece → rotate → click the top-left anchor of the rotated bounding box.\n"
            "Green preview = legal. Red = outside the box or overlap. UNDO and invalid PLACE both cost an action.\n"
            "STM remembers rejected placements inside this box. LTM stores local pattern statistics across boxes.\n"
            "New Box keeps LTM. Reset Run clears learned LTM for the selected mode. Manual play does not train LTM."
        )
        tk.Label(right, text=help_txt, bg=BG, fg=MUTED, justify="left", font=("Segoe UI", 8)).pack(anchor="w")

        stats = tk.LabelFrame(right, text="Run state", bg=BG, fg=NAVY, font=("Segoe UI", 9, "bold"))
        stats.pack(fill="x", pady=8)
        self.stats_var = tk.StringVar()
        tk.Label(stats, textvariable=self.stats_var, bg=BG, fg="#243447", justify="left", font=("Consolas", 9)).pack(
            anchor="w", padx=8, pady=6
        )

        controls = tk.Frame(self, bg=BG)
        controls.pack(fill="x", padx=18, pady=(0, 6))
        ttk.Label(controls, text="Mode").pack(side="left")
        mode_box = ttk.Combobox(controls, textvariable=self.mode, values=list(MODES), width=8, state="readonly")
        mode_box.pack(side="left", padx=6)
        mode_box.bind("<<ComboboxSelected>>", lambda e: self._on_mode_change())

        ttk.Label(controls, text="Seed").pack(side="left", padx=(10, 0))
        ttk.Entry(controls, textvariable=self.seed, width=6).pack(side="left", padx=4)

        ttk.Label(controls, text="Control").pack(side="left", padx=(12, 4))
        ttk.Combobox(
            controls,
            textvariable=self.play_mode,
            values=("manual", "training"),
            width=10,
            state="readonly",
        ).pack(side="left")

        for text, cmd in (
            ("Start", self.start),
            ("Pause", self.pause),
            ("Single Step", self.single_step),
            ("New Box", self.new_box),
            ("Reset Run", self.reset_run),
            ("Undo", self.manual_undo),
            ("Submit", self.manual_submit),
            ("Save Snapshot", self.save_snapshot),
        ):
            ttk.Button(controls, text=text, command=cmd).pack(side="left", padx=3)

        ttk.Label(controls, text="Speed (ms)").pack(side="left", padx=(12, 4))
        ttk.Scale(controls, from_=10, to=400, variable=self.speed_ms, orient="horizontal", length=140).pack(
            side="left"
        )

        status = tk.Frame(self, bg="#d9e3f0")
        status.pack(fill="x", side="bottom")
        tk.Label(
            status,
            textvariable=self.status,
            bg="#d9e3f0",
            fg=NAVY,
            anchor="w",
            font=("Segoe UI", 9),
        ).pack(fill="x", padx=12, pady=4)

        plot_frame = tk.Frame(self, bg=BG)
        plot_frame.pack(fill="both", expand=True, padx=18, pady=(0, 8))
        self._init_plot(plot_frame)
        self.bind("<space>", lambda e: self.single_step())
        self.bind("<p>", lambda e: self.pause())
        self.bind("<s>", lambda e: self.start())
        self.bind("<n>", lambda e: self.new_box())
        self.bind("<r>", lambda e: self._rotate_next())
        self.bind("<u>", lambda e: self.manual_undo())
        self.focus_set()

    def _init_plot(self, parent) -> None:
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.figure import Figure

        self.figure = Figure(figsize=(11.5, 2.1), dpi=90)
        self.figure.patch.set_facecolor(BG)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("#f7fafc")
        self.ax.set_title("Training terminal scores (rolling mean window = 10)", loc="left", color=NAVY, fontsize=9)
        self.ax.set_ylim(0, 100)
        self.ax.set_xlim(1, 20)
        self.plot_canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.plot_canvas.get_tk_widget().pack(fill="both", expand=True)

    def _on_piece(self, name: str) -> None:
        self.selected_piece = name
        self.status.set(f"Selected piece {name}. Pick a rotation, then click a board anchor.")

    def _clear_hover(self) -> None:
        self.board.preview_cells = None
        self._refresh()

    def _on_board_event(self, kind: str, xy) -> None:
        if self.play_mode.get() != "manual":
            return
        if xy is None:
            self.board.preview_cells = None
            self.board.redraw(self.env)
            return
        x, y = xy
        cells = placed_cells(self.selected_piece, self.rotation.get(), x, y)
        ok = self.env._can_place_cells(cells) and not self.env.terminal
        if kind == "hover":
            self.board.set_preview(cells if in_bounds(cells) or cells else cells, ok)
            return
        self._manual_place(x, y)

    def _manual_place(self, x: int, y: int) -> None:
        if self.env.terminal:
            self.status.set("Box is finished. Click New Box to start another (LTM is kept).")
            return
        result = self.env.step(Action.place(self.selected_piece, self.rotation.get(), x, y))
        extra = "valid" if result.accepted else "rejected (still cost 1 action)"
        self.status.set(
            f"PLACE {self.selected_piece} rot={self.rotation.get() * 90}° at ({x+1},{y+1}) {extra}. "
            f"Score {result.score}/100, actions {result.actions_used}/100."
        )
        self._refresh()

    def manual_undo(self) -> None:
        if self.play_mode.get() != "manual":
            self.status.set("Undo in training is chosen by the agent.")
            return
        result = self.env.step(Action.undo())
        self.status.set(f"UNDO {result.reason}. Score {result.score}/100.")
        self._refresh()

    def manual_submit(self) -> None:
        if self.play_mode.get() != "manual":
            return
        result = self.env.step(Action.submit())
        self.status.set(f"SUBMIT. Terminal score {result.score}/100. Manual episodes do not update LTM.")
        self._refresh()

    def _on_mode_change(self) -> None:
        self.pause()
        mode = self.mode.get()
        self.agent = self._make_agent(mode)
        self.env.reset_box()
        self.agent.begin_box()
        self.train_scores = []
        self.episode_index = 1
        self.rng = random.Random(self.seed.get())
        self.status.set(
            f"Switched to isolated mode '{mode}'. This mode has its own LTM table; nothing is shared."
        )
        self._refresh()

    def start(self) -> None:
        if self.play_mode.get() != "training":
            self.play_mode.set("training")
        self.running = True
        self.paused = False
        self.status.set("Training: one autonomous agent, successive boxes. Pause stops before the next action.")
        self._schedule()

    def pause(self) -> None:
        self.paused = True
        self.running = False
        if self._tick_job is not None:
            self.after_cancel(self._tick_job)
            self._tick_job = None
        self.status.set("Paused. The next action will not run until Start or Single Step.")

    def single_step(self) -> None:
        self.play_mode.set("training")
        self.paused = True
        self.running = False
        self._agent_action()

    def new_box(self) -> None:
        self.pause()
        self.env.reset_box()
        self.agent.begin_box()
        self.episode_index += 1
        self.status.set("New Box: board, stack, STM and action counters cleared. LTM retained.")
        self._refresh()

    def reset_run(self) -> None:
        if not messagebox.askyesno(
            "Reset Run",
            "Clear learned LTM for the current mode, the board, STM, scores and episode index?",
        ):
            return
        self.pause()
        mode = self.mode.get()
        self.ltm_store[mode] = self._fresh_ltm()
        self.agent = self._make_agent(mode)
        self.env.reset_box()
        self.train_scores = []
        self.episode_index = 1
        self.rng = random.Random(self.seed.get())
        self.status.set(f"Reset Run: learned LTM for mode '{mode}' discarded. Other modes are untouched.")
        self._refresh()

    def save_snapshot(self) -> None:
        SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        path = filedialog.asksaveasfilename(
            initialdir=str(SNAPSHOTS_DIR),
            defaultextension=".png",
            filetypes=[("PNG image", "*.png")],
            initialfile="snapshot.png",
        )
        if not path:
            return
        png = Path(path)
        save_populated_canvas(self.env, png, extra=f"mode={self.mode.get()}  seed={self.seed.get()}")
        json_path = png.with_suffix(".json")
        json_path.write_text(json.dumps(self.env.snapshot(), indent=2), encoding="utf-8")
        self.status.set(f"Saved {png.name} and {json_path.name}. Score {self.env.score}/100.")

    def _schedule(self) -> None:
        if self.paused or not self.running:
            return
        self._agent_action()
        delay = max(10, int(self.speed_ms.get()))
        self._tick_job = self.after(delay, self._schedule)

    def _agent_action(self) -> None:
        if self.env.terminal:
            self.train_scores.append(self.env.score)
            self._update_plot()
            self.env.reset_box()
            self.agent.begin_box()
            self.episode_index += 1
            self.status.set(f"Box finished. Starting box {self.episode_index} (LTM retained).")
            self._refresh()
            return
        occupied_before = self.env.occupied
        mask_before = self.env.mask
        action = self.agent.select(self.env, self.rng)
        result = self.env.step(action)
        if self.play_mode.get() == "training" and result.accepted and action.kind.value == "PLACE":
            self.agent.after_step(self.env, action, occupied_before, mask_before)
        if self.env.terminal:
            self.agent.end_box(self.env)
        self.status.set(
            f"{action.kind.value} {action.as_dict()} → {result.reason}  "
            f"score {result.score}/100  actions {result.actions_used}/100"
        )
        self._refresh()

    def _rotate_next(self) -> None:
        self.rotation.set((self.rotation.get() + 1) % 4)
        self.status.set(f"Rotation {self.rotation.get() * 90}°")

    def _update_plot(self) -> None:
        self.ax.clear()
        self.ax.set_facecolor("#f7fafc")
        ys = self.train_scores
        xs = list(range(1, len(ys) + 1))
        if ys:
            self.ax.plot(xs, ys, color="#9bb4d0", lw=1, label="terminal score")
            window = 10
            if len(ys) >= 1:
                means = []
                for i in range(len(ys)):
                    sl = ys[max(0, i + 1 - window) : i + 1]
                    means.append(sum(sl) / len(sl))
                self.ax.plot(xs, means, color=ACCENT, lw=2, label="rolling mean W=10")
        self.ax.set_ylim(0, 100)
        self.ax.set_xlim(1, max(20, len(ys)))
        self.ax.set_title("Training terminal scores (rolling mean window = 10)", loc="left", color=NAVY, fontsize=9)
        self.ax.legend(loc="lower right", fontsize=8)
        self.figure.tight_layout()
        self.plot_canvas.draw_idle()

    def _refresh(self) -> None:
        self.board.redraw(self.env)
        self.score_var.set(f"SCORE  {self.env.score}/100")
        last = self.env.last_action or {}
        self.meta_var.set(
            f"{self.env.blanks} blank cells   ·   episode {self.episode_index}   ·   "
            f"actions {self.env.actions_used}/100   ·   last {last.get('kind', '—')}"
        )
        mem = self.agent.memory_stats()
        self.stats_var.set(
            f"mode={self.mode.get():<5}  seed={self.seed.get():<5}  control={self.play_mode.get()}\n"
            f"invalid={self.env.invalid_attempts:<4}  undos={self.env.undos:<4}  "
            f"terminal={str(self.env.terminal):<5}  reason={self.env.termination_reason or '—'}\n"
            f"STM entries={mem['stm_entries']:<4}  LTM entries={mem['ltm_entries']:<5}  "
            f"LTM hits={mem['ltm_hits']} / lookups={mem['ltm_lookups']}\n"
            f"LTM bytes={mem['memory_serialized_bytes']}"
        )


def main(argv: list[str] | None = None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    start_demo = "--demo" in argv or "-d" in argv
    app = MGAApp(start_demo=start_demo)
    app.mainloop()


if __name__ == "__main__":
    main()
