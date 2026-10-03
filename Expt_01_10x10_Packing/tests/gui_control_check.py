"""Headless-ish GUI control check: invoke the same callbacks the buttons use."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

from mga.gui import MGAApp
from mga.paths import SNAPSHOTS_DIR


def main() -> None:
    app = MGAApp()
    app.update()
    app.catalogue.on_select("F")
    app.rotation.set(1)
    app._manual_place(0, 0)
    app.update()
    assert app.env.occupied > 0
    app.manual_undo()
    app.update()
    assert app.env.occupied == 0
    app._manual_place(0, 0)
    app.manual_submit()
    assert app.env.terminal
    app.new_box()
    assert not app.env.terminal
    app.mode.set("stm")
    app._on_mode_change()
    app.play_mode.set("training")
    app.single_step()
    app.update()
    png = SNAPSHOTS_DIR / "gui_control_check.png"
    from mga.render import save_populated_canvas

    save_populated_canvas(app.env, png, extra="GUI control-check snapshot")
    app.destroy()
    print(f"GUI callbacks ok; snapshot {png}")


if __name__ == "__main__":
    main()
