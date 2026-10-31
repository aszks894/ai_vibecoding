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
        self.root.title("Ur Not Gonna Win")
        self.root.resizable(False, False)
        self.canvas = tk.Canvas(
            root, width=WIDTH, height=HEIGHT, bg=PALETTE["cream"],
            highlightthickness=0,
        )
        self.canvas.pack()

        self.score = 0
        self.coins = 0
        self.round_reward = 10
        self.round_number = 1
        self.store_open = False
        self.store_view = "shop"
        self.collection_page = 0
        self.store_message = "Choose a prize with 1, 2, or 3."
        self.collection: list[str] = []
        self.store_items = [
            {"name": "Labubu plush", "price": 12, "color": "#9ed6a5", "symbol": "☺"},
            {"name": "Pastel star plush", "price": 8, "color": "#f3c9dc", "symbol": "★"},
            {"name": "Lucky prize capsule", "price": 5, "color": "#c8b4e8", "symbol": "?"},
        ]
        self.message = "Move with ← →   •   Press SPACE to grab!"
        self.claw_x = 390
        self.claw_y = 175
        self.claw_state = "ready"
        self.target: dict[str, object] | None = None
        self.carrying: dict[str, object] | None = None
        self.yeeting: dict[str, object] | None = None
        self.yeet_vx = 0.0
        self.yeet_vy = 0.0
        self.yeet_bounces = 0
        self.prizes = self._make_prizes()
        self.held: set[str] = set()
        self.root.bind("<KeyPress-Left>", lambda _event: self.held.add("left"))
        self.root.bind("<KeyRelease-Left>", lambda _event: self.held.discard("left"))
        self.root.bind("<KeyPress-Right>", lambda _event: self.held.add("right"))
        self.root.bind("<KeyRelease-Right>", lambda _event: self.held.discard("right"))
        self.root.bind("<space>", self.drop_claw)
        self.root.bind("s", self.toggle_store)
        self.root.bind("S", self.toggle_store)
        self.root.bind("c", self.open_collection)
        self.root.bind("C", self.open_collection)
        self.root.bind("[", lambda _event: self.change_collection_page(-1))
        self.root.bind("]", lambda _event: self.change_collection_page(1))
        self.root.bind("<Escape>", self.close_store)
        for item_key in ("1", "2", "3"):
            self.root.bind(item_key, lambda _event, key=item_key: self.buy_item(int(key) - 1))
        self.root.bind("r", self.reset)
        self.root.bind("R", self.reset)
        self.draw()
        self.tick()

    @staticmethod
    def _make_prizes() -> list[dict[str, object]]:
        prizes = []
        choices = [
            ("#517BB3", "★"), ("#7ab0e2", "★"), ("#5d7aa5", "★"),
            ("#8fb2da", "★"), ("#4f7eb3", "★"), ("#7cb1ff", "★"),
        ]
        for _ in range(13):
            color, symbol = random.choice(choices)
            size = random.randint(22, 29)
            # Try random positions, accepting only spots with room around them.
            for _attempt in range(100):
                x = random.randint(114 + size, 686 - size)
                y = random.randint(405 + size, 468)
                spaced_out = all(
                    ((x - float(other["x"])) ** 2 + (y - float(other["y"])) ** 2)
                    >= (size + int(other["size"]) + 3) ** 2
                    for other in prizes
                )
                if spaced_out:
                    break
            else:
                # If the playfield is crowded, skip this toy rather than overlap it.
                continue
            prizes.append({
                "x": x,
                "y": y,
                "color": color,
                "symbol": symbol,
                "size": size,
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
        if self.claw_state == "ready" and not self.store_open:
            self.claw_state = "lowering"
            self.target = None
            self.message = "try to get smth (u probably wont i rigged the machine)"

    def toggle_store(self, _event: tk.Event | None = None) -> None:
        if self.claw_state != "ready":
            self.message = "Wait for the round to finish before shopping."
            return
        self.store_open = not self.store_open
        self.store_view = "shop"
        self.store_message = "Choose a prize with 1, 2, or 3."
        self.draw()

    def open_collection(self, _event: tk.Event | None = None) -> None:
        if self.claw_state != "ready":
            self.message = "Finish this round before opening the collection."
            return
        self.store_open = True
        self.store_view = "collection"
        self.draw()

    def change_collection_page(self, direction: int) -> None:
        if not self.store_open or self.store_view != "collection":
            return
        max_page = max(0, (len(self.collection) - 1) // 9)
        self.collection_page = max(0, min(max_page, self.collection_page + direction))
        self.draw()

    def close_store(self, _event: tk.Event | None = None) -> None:
        if self.store_open:
            self.store_open = False
            self.draw()

    def buy_item(self, item_index: int) -> None:
        if not self.store_open or self.store_view != "shop":
            return
        item = self.store_items[item_index]
        price = int(item["price"])
        name = str(item["name"])
        if self.coins < price:
            self.store_message = f"Need {price - self.coins} more coins to buy {name}."
        else:
            self.coins -= price
            self.collection.append(name)
            self.collection_page = (len(self.collection) - 1) // 9
            self.store_message = f"Bought {name}! Open Collection to see it."
        self.draw()

    def tick(self) -> None:
        if self.store_open:
            self.draw()
            self.draw_store()
            self.root.after(25, self.tick)
            return
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
                    self.prizes.remove(self.target)
                    if random.random() < 0.30:
                        self.yeeting = self.target
                        self.yeet_vx = random.choice([-1, 1]) * random.uniform(4.0, 6.0)
                        self.yeet_vy = random.uniform(-8.0, -6.5)
                        self.yeet_bounces = 0
                        self.message = "The claw tossed the toy! Try again."
                        self.claw_state = "yeeting"
                    else:
                        self.carrying = self.target
                        self.message = "Toy grabbed! Delivering it to the chute."
                        self.claw_state = "raising"
                else:
                    self.carrying = None
                    self.message = "No toy grabbed. Move over a prize and retry."
                    self.claw_state = "raising"
        elif self.claw_state == "raising":
            self.claw_y = max(175, self.claw_y - 7)
            if self.claw_y <= 175:
                if self.carrying:
                    self.claw_state = "returning"
                else:
                    self.claw_state = "ready"
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
                if not self.prizes:
                    self.coins += self.round_reward
                    self.message = f"Round {self.round_number} cleared! +{self.round_reward} coins. New pile!"
                    self.round_number += 1
                    self.prizes = self._make_prizes()
                else:
                    self.message = "Toy delivered! Keep clearing the prize pile."
                self.claw_state = "raising"
        elif self.claw_state == "yeeting":
            if self.yeeting:
                self.yeet_vy += 0.34
                new_x = float(self.yeeting["x"]) + self.yeet_vx
                left_edge, right_edge = 114, 686
                if new_x < left_edge or new_x > right_edge:
                    self.yeet_vx *= -0.45
                    new_x = max(left_edge, min(right_edge, new_x))
                self.yeeting["x"] = new_x
                self.yeeting["y"] = float(self.yeeting["y"]) + self.yeet_vy
                if float(self.yeeting["y"]) >= 468:
                    self.yeeting["y"] = 468
                    if self.yeet_bounces == 0 and abs(self.yeet_vy) > 2.5:
                        self.yeet_vy *= -0.22
                        self.yeet_vx *= 0.72
                        self.yeet_bounces += 1
                    else:
                        self.yeet_vy = 0
                        self.yeeting["x"] = max(left_edge, min(right_edge, float(self.yeeting["x"])))
                        self.prizes.append(self.yeeting)
                        self.yeeting = None
                        self.claw_state = "raising"

        self.draw()
        self.root.after(25, self.tick)

    def draw_store(self) -> None:
        c = self.canvas
        c.create_rectangle(108, 120, 692, 515, fill=PALETTE["ink"],
                           outline=PALETTE["white"], width=3)
        c.create_rectangle(116, 128, 684, 507, fill=PALETTE["cream"], outline="")
        c.create_text(400, 157, text="PRIZE SHOP", fill=PALETTE["ink"],
                      font=("Trebuchet MS", 24, "bold"))
        c.create_text(400, 188,
                      text=f"Coins: {self.coins}     |     Prizes collected: {len(self.collection)}",
                      fill=PALETTE["ink"], font=("Trebuchet MS", 12, "bold"))
        for index, item in enumerate(self.store_items):
            y = 225 + index * 67
            c.create_rectangle(143, y - 25, 657, y + 25, fill=PALETTE["white"],
                               outline=PALETTE["lavender"], width=2)
            c.create_oval(157, y - 17, 191, y + 17, fill=str(item["color"]),
                          outline=PALETTE["lavender"], width=2)
            c.create_text(174, y, text=str(item["symbol"]), fill=PALETTE["white"],
                          font=("Trebuchet MS", 16, "bold"))
            c.create_text(204, y, anchor="w", text=f"{index + 1}. {item['name']}",
                          fill=PALETTE["ink"], font=("Trebuchet MS", 13, "bold"))
            c.create_text(639, y, anchor="e", text=f"{item['price']} coins",
                          fill=PALETTE["ink"], font=("Trebuchet MS", 12, "bold"))
        c.create_text(400, 448, text=self.store_message, fill=PALETTE["ink"],
                      font=("Trebuchet MS", 11, "bold"))
        owned = ", ".join(self.collection[-3:]) if self.collection else "Nothing yet — win coins and pick a prize!"
        if len(owned) > 66:
            owned = owned[:63] + "..."
        c.create_text(400, 473, text=f"Collection: {owned}", fill=PALETTE["ink"],
                      font=("Trebuchet MS", 10))
        c.create_text(400, 492, text="Press 1 / 2 / 3 to buy   |   S or Esc to close",
                      fill=PALETTE["ink"], font=("Trebuchet MS", 10, "bold"))

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
        c.create_text(400, 80, text="definitely not rigged claw machine", fill=PALETTE["white"],
                      font=("Trebuchet MS", 19, "bold"))

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
        if self.yeeting:
            self.draw_prize(self.yeeting)
        if self.carrying:
            self.draw_prize(self.carrying, self.claw_x, self.claw_y + 38)
        self.draw_claw()

        # Control panel.
        c.create_rectangle(83, 525, 717, 551, fill=PALETTE["mint"], outline="")
        status = self.message
        c.create_text(98, 538, text=status, anchor="w", fill=PALETTE["ink"],
                      font=("Trebuchet MS", 10, "bold"))
        c.create_text(558, 539, text=f"COINS {self.coins}", anchor="e", fill=PALETTE["ink"],
                      font=("Trebuchet MS", 11, "bold"))
        c.create_text(702, 539, text=f"SCORE {self.score}", anchor="e", fill=PALETTE["ink"],
                      font=("Trebuchet MS", 11, "bold"))
        c.create_text(400, 564, text="LEFT / RIGHT MOVE   SPACE GRAB   S SHOP   R RESET",
                      fill=PALETTE["ink"], font=("Trebuchet MS", 10, "bold"))


def main() -> None:
    root = tk.Tk()
    ClawMachine(root)
    root.mainloop()


if __name__ == "__main__":
    main()
