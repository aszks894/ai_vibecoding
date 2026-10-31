"""Pastel Pocket Claw: a small virtual claw machine made with Tkinter."""

from __future__ import annotations

import random
import tkinter as tk


WIDTH = 800
HEIGHT = 600
PALETTE = {
    "ink": "#55465e",
    "pink": "#d3edf3",
    "pink_dark": "#94c0e9",
    "lavender": "#b2c8e4",
    "blue": "#b8d5dd",
    "mint": "#bddae8",
    "cream": "#fff8ed",
    "glass": "#f5fbff",
    "gold": "#75b0f4",
    "white": "#ffffff",
    "shadow": "#56595a",
}


class ClawMachine:
    """Draw and run the claw-machine game on a Tkinter canvas."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Pastel Pocket Claw")
        self.root.resizable(False, False)
        self.canvas = tk.Canvas(
            root, width=WIDTH, height=HEIGHT, bg=PALETTE["cream"],
            highlightthickness=0,
        )
        self.canvas.pack()

        self.score = 0
        self.message = "Move with ← →   •   Press SPACE to grab!"
        self.claw_x = 390
        self.claw_y = 175
        self.claw_state = "ready"
        self.target: dict[str, object] | None = None
        self.carrying: dict[str, object] | None = None
        self.prizes = self._make_prizes()
        self.held: set[str] = set()
        self.root.bind("<KeyPress-Left>", lambda _event: self.held.add("left"))
        self.root.bind("<KeyRelease-Left>", lambda _event: self.held.discard("left"))
        self.root.bind("<KeyPress-Right>", lambda _event: self.held.add("right"))
        self.root.bind("<KeyRelease-Right>", lambda _event: self.held.discard("right"))
        self.root.bind("<space>", self.drop_claw)
        self.root.bind("r", self.reset)
        self.root.bind("R", self.reset)
        self.draw()
        self.tick()

    @staticmethod
    def _make_prizes() -> list[dict[str, object]]:
        prizes = []
        choices = [
            ("#517BB3", "★"), ("#7ab0e2", "★"), ("#5d7aa5", "★"),
            ("#3843a3", "★"), ("#0b488d", "★"), ("#7cb1ff", "★"),
        ]
        for _ in range(13):
            color, symbol = random.choice(choices)
            prizes.append({
                "x": random.randint(105, 695),
                "y": random.randint(405, 495),
                "color": color,
                "symbol": symbol,
                "size": random.randint(22, 29),
            })
        return prizes

    def reset(self, _event: tk.Event | None = None) -> None:
        if self.claw_state != "ready":
            return
        self.score = 0
        self.prizes = self._make_prizes()
        self.message = "Fresh toys! Move with ← → and press SPACE."
        self.draw()

    def drop_claw(self, _event: tk.Event | None = None) -> None:
        if self.claw_state == "ready":
            self.claw_state = "lowering"
            self.target = None
            self.message = "try to get smth (u probably wont i rigged the machine)"

    def tick(self) -> None:
        if self.claw_state == "ready":
            if "left" in self.held:
                self.claw_x = max(95, self.claw_x - 5)
            if "right" in self.held:
                self.claw_x = min(705, self.claw_x + 5)
        elif self.claw_state == "lowering":
            self.claw_y = min(465, self.claw_y + 7)
            if self.claw_y >= 455:
                nearby = [p for p in self.prizes if abs(float(p["x"]) - self.claw_x) < 52]
                self.target = min(nearby, key=lambda p: abs(float(p["x"]) - self.claw_x)) if nearby else None
                if self.target:
                    self.carrying = self.target
                    self.prizes.remove(self.target)
                    self.message = "You got something(no you didnt this is pixels)"
                else:
                    self.carrying = None
                    self.message = "u suck haha"
                self.claw_state = "raising"
        elif self.claw_state == "raising":
            self.claw_y = max(175, self.claw_y - 7)
            if self.claw_y <= 175:
                self.claw_state = "returning" if self.carrying else "ready"
        elif self.claw_state == "returning":
            self.claw_x += 7
            if self.claw_x >= 690:
                self.claw_x = 690
                self.claw_state = "delivering"
        elif self.claw_state == "delivering":
            self.claw_y = min(515, self.claw_y + 8)
            if self.claw_y >= 515:
                self.carrying = None
                self.score += 1
                self.message = "here u go"
                self.claw_state = "raising"

        self.draw()
        self.root.after(25, self.tick)

    def draw_prize(self, prize: dict[str, object], x: float | None = None, y: float | None = None) -> None:
        px = float(prize["x"]) if x is None else x
        py = float(prize["y"]) if y is None else y
        size = int(prize["size"])
        color = str(prize["color"])
        symbol = str(prize["symbol"])
        self.canvas.create_oval(px - size, py - size + 4, px + size, py + size + 4,
                                fill=PALETTE["shadow"], outline="")
        self.canvas.create_oval(px - size, py - size, px + size, py + size,
                                fill=color, outline=PALETTE["white"], width=2)
        self.canvas.create_text(px, py, text=symbol, fill=PALETTE["white"],
                                font=("Segoe UI Symbol", size, "bold"))

    def draw_claw(self) -> None:
        c = self.canvas
        c.create_line(self.claw_x, 88, self.claw_x, self.claw_y - 14,
                      fill=PALETTE["ink"], width=3)
        c.create_oval(self.claw_x - 11, self.claw_y - 17, self.claw_x + 11,
                      self.claw_y + 5, fill=PALETTE["gold"], outline=PALETTE["ink"], width=2)
        c.create_line(self.claw_x, self.claw_y, self.claw_x - 18,
                      self.claw_y + 22, fill=PALETTE["ink"], width=4,
                      smooth=True, capstyle=tk.ROUND)
        c.create_line(self.claw_x, self.claw_y, self.claw_x + 18,
                      self.claw_y + 22, fill=PALETTE["ink"], width=4,
                      smooth=True, capstyle=tk.ROUND)
        c.create_arc(self.claw_x - 24, self.claw_y + 8, self.claw_x + 24,
                     self.claw_y + 43, start=200, extent=140, style=tk.ARC,
                     outline=PALETTE["ink"], width=4)

    def draw(self) -> None:
        c = self.canvas
        c.delete("all")
        # Cabinet body and marquee.
        c.create_rectangle(35, 24, 765, 576, fill=PALETTE["pink"], outline="")
        c.create_rectangle(49, 38, 751, 562, fill=PALETTE["cream"], outline="")
        c.create_rectangle(72, 50, 728, 110, fill=PALETTE["lavender"], outline="")
        c.create_text(400, 80, text="✦  PASTEL POCKET CLAW  ✦", fill=PALETTE["white"],
                      font=("Trebuchet MS", 23, "bold"))

        # Glass playfield.
        c.create_rectangle(83, 125, 717, 500, fill=PALETTE["glass"],
                           outline=PALETTE["pink_dark"], width=4)
        c.create_rectangle(86, 128, 714, 497, outline=PALETTE["white"], width=2)
        c.create_line(100, 155, 100, 370, fill=PALETTE["white"], width=5)
        c.create_line(112, 155, 112, 300, fill=PALETTE["white"], width=2)
        # Prize shelf and chute.
        c.create_rectangle(92, 497, 708, 511, fill=PALETTE["pink_dark"], outline="")
        c.create_rectangle(630, 479, 705, 535, fill=PALETTE["blue"],
                           outline=PALETTE["pink_dark"], width=3)
        c.create_text(668, 520, text="PRIZE", fill=PALETTE["ink"],
                      font=("Trebuchet MS", 9, "bold"))

        for prize in self.prizes:
            self.draw_prize(prize)
        if self.carrying:
            self.draw_prize(self.carrying, self.claw_x, self.claw_y + 38)
        self.draw_claw()

        # Control panel.
        c.create_rectangle(83, 525, 717, 551, fill=PALETTE["mint"], outline="")
        c.create_text(300, 538, text=self.message, fill=PALETTE["ink"],
                      font=("Trebuchet MS", 11, "bold"))
        c.create_text(664, 539, text=f"★  {self.score}", fill=PALETTE["ink"],
                      font=("Trebuchet MS", 14, "bold"))
        c.create_text(400, 564, text="← → MOVE     SPACE GRAB     R NEW GAME",
                      fill=PALETTE["ink"], font=("Trebuchet MS", 10, "bold"))


def main() -> None:
    root = tk.Tk()
    ClawMachine(root)
    root.mainloop()


if __name__ == "__main__":
    main()
