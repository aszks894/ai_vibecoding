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
        self.round_reward = 1
        self.round_number = 1
        self.store_open = False
        self.store_view = "shop"
        self.collection_page = 0
        self.store_message = "Choose a prize with 1, 2, or 3."
        self.collection: list[str] = []
        self.store_items = [
            {"name": "plush", "price": 12, "color": "#9ec0d6", "symbol": "🐻‍❄️"},
            {"name": "star plush", "price": 8, "color": "#9ec0d6", "symbol": "★"},
            {"name": "random shi", "price": 5, "color": "#9ec0d6", "symbol": "?"},
        ]
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
        self.message = "Move with ← →   •   Press SPACE to grab!"
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
        self.root.bind("<Prior>", lambda _event: self.change_collection_page(-1))
        self.root.bind("<Next>", lambda _event: self.change_collection_page(1))
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
        self.round_number = 1
        self.message = "Fresh toys! Move with ← → and press SPACE."
        self.draw()

    def drop_claw(self, _event: tk.Event | None = None) -> None:
        if self.claw_state == "ready" and not self.store_open:
            self.claw_state = "lowering"
            self.target = None
            self.message = "try to get smth (u probably wont i rigged the machine)"

    def toggle_store(self, _event: tk.Event | None = None) -> None:
        if self.claw_state != "ready":
            return
        if self.store_open and self.store_view == "collection":
            self.store_view = "shop"
        elif self.store_open:
            self.store_open = False
        else:
            self.store_open = True
            self.store_view = "shop"
            self.store_message = "Choose a prize with 1, 2, or 3."
        self.draw()

    def open_collection(self, _event: tk.Event | None = None) -> None:
        if self.claw_state != "ready":
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
            self.store_message = f"Need {price - self.coins} more coins to buy {name} why so broke"
        else:
            self.coins -= price
            self.collection.append(name)
            self.collection_page = (len(self.collection) - 1) // 9
            self.store_message = f"u bought {name} open ur collection to see it"
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
                        self.message = "skill issue"
                        self.claw_state = "yeeting"
                    else:
                        self.carrying = self.target
                        self.message = "You got something(no you didnt this is pixels)"
                        self.claw_state = "raising"
                else:
                    self.carrying = None
                    self.message = "u suck haha"
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
                    self.round_number += 1
                    self.prizes = self._make_prizes()
                self.message = "here u go"
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
        if self.store_view == "collection":
            self.draw_collection()
        else:
            self.draw_shop()
        return

    def draw_shop(self) -> None:
        c = self.canvas
        c.create_text(400, 155, text="PRIZE SHOP", fill=PALETTE["ink"],
                      font=("Trebuchet MS", 23, "bold"))
        c.create_text(400, 183, text=f"You have {self.coins} coins",
                      fill=PALETTE["ink"], font=("Trebuchet MS", 12, "bold"))
        for index, item in enumerate(self.store_items):
            top = 204 + index * 72
            center_y = top + 33
            c.create_rectangle(139, top, 661, top + 65, fill=PALETTE["white"],
                               outline=PALETTE["lavender"], width=2)
            self.draw_item_art(item, 178, center_y, 0.72)
            c.create_text(225, center_y - 8, anchor="w", text=f"{index + 1}. {item['name']}",
                          fill=PALETTE["ink"], font=("Trebuchet MS", 13, "bold"))
            c.create_text(225, center_y + 15, anchor="w", text=f"Price: {item['price']} coins",
                          fill=PALETTE["ink"], font=("Trebuchet MS", 10))
        c.create_text(400, 431, text=self.store_message, fill=PALETTE["ink"],
                      font=("Trebuchet MS", 10, "bold"))
        c.create_text(400, 463, text="1 / 2 / 3: BUY     C: VIEW COLLECTION",
                      fill=PALETTE["ink"], font=("Trebuchet MS", 11, "bold"))
        c.create_text(400, 487, text="S or Esc: close shop",
                      fill=PALETTE["ink"], font=("Trebuchet MS", 10))

    def draw_collection(self) -> None:
        c = self.canvas
        total = len(self.collection)
        pages = max(1, (total + 8) // 9)
        c.create_text(400, 155, text="collection", fill=PALETTE["ink"],
                      font=("Trebuchet MS", 23, "bold"))
        c.create_text(400, 183, text=f"{total} prize{'s' if total != 1 else ''} collected",
                      fill=PALETTE["ink"], font=("Trebuchet MS", 12, "bold"))
        start = self.collection_page * 9
        shown = self.collection[start:start + 9]
        for index, name in enumerate(shown):
            row, col = divmod(index, 3)
            x = 211 + col * 189
            y = 245 + row * 82
            item = next(prize for prize in self.store_items if prize["name"] == name)
            c.create_rectangle(x - 82, y - 30, x + 82, y + 32,
                               fill=PALETTE["white"], outline=PALETTE["lavender"], width=2)
            self.draw_item_art(item, x, y - 2, 0.62)
            c.create_text(x, y + 37, text=name, fill=PALETTE["ink"],
                          font=("Trebuchet MS", 9, "bold"))
        if not shown:
            c.create_text(400, 315, text="hey broke person",
                          fill=PALETTE["ink"], font=("Trebuchet MS", 12, "bold"))
        c.create_text(400, 464, text=f"Page {self.collection_page + 1} of {pages}   |   {total} total prizes",
                      fill=PALETTE["ink"], font=("Trebuchet MS", 10, "bold"))
        c.create_text(400, 487, text="Page Up / Page Down: browse   S: SHOP   Esc: close",
                      fill=PALETTE["ink"], font=("Trebuchet MS", 10, "bold"))

    def draw_item_art(self, item: dict[str, object], x: float, y: float, scale: float = 1.0) -> None:
        c = self.canvas
        name = str(item["name"])
        color = str(item["color"])
        if name == "plush":
            c.create_polygon(x - 17 * scale, y - 12 * scale,
                             x - 21 * scale, y - 31 * scale,
                             x - 7 * scale, y - 21 * scale,
                             fill=color, outline=PALETTE["ink"], width=2)
            c.create_polygon(x + 17 * scale, y - 12 * scale,
                             x + 21 * scale, y - 31 * scale,
                             x + 7 * scale, y - 21 * scale,
                             fill=color, outline=PALETTE["ink"], width=2)
            c.create_oval(x - 24 * scale, y - 23 * scale,
                          x + 24 * scale, y + 24 * scale,
                          fill=color, outline=PALETTE["ink"], width=2)
            eye_r = 2.5 * scale
            c.create_oval(x - 10 * scale - eye_r, y - 5 * scale - eye_r,
                          x - 10 * scale + eye_r, y - 5 * scale + eye_r, fill=PALETTE["ink"])
            c.create_oval(x + 10 * scale - eye_r, y - 5 * scale - eye_r,
                          x + 10 * scale + eye_r, y - 5 * scale + eye_r, fill=PALETTE["ink"])
            c.create_arc(x - 11 * scale, y - 1 * scale, x + 11 * scale, y + 16 * scale,
                         start=205, extent=130, style=tk.ARC, outline=PALETTE["ink"], width=2)
            for tooth_x in (-4, 0, 4):
                c.create_polygon(x + tooth_x * scale, y + 8 * scale,
                                 x + (tooth_x + 2) * scale, y + 13 * scale,
                                 x + (tooth_x + 4) * scale, y + 8 * scale,
                                 fill=PALETTE["white"], outline="")
        elif name == "Pastel star plush":
            import math
            points = []
            for point in range(10):
                angle = -math.pi / 2 + point * math.pi / 5
                radius = (25 if point % 2 == 0 else 12) * scale
                points.extend((x + math.cos(angle) * radius, y + math.sin(angle) * radius))
            c.create_polygon(*points, fill=color, outline=PALETTE["ink"], width=2)
            c.create_oval(x - 3 * scale, y - 5 * scale, x + 3 * scale, y + 1 * scale,
                          fill=PALETTE["ink"], outline="")
            c.create_oval(x + 7 * scale, y - 5 * scale, x + 13 * scale, y + 1 * scale,
                          fill=PALETTE["ink"], outline="")
        else:
            c.create_oval(x - 19 * scale, y - 25 * scale, x + 19 * scale, y + 25 * scale,
                          fill=color, outline=PALETTE["ink"], width=2)
            c.create_arc(x - 19 * scale, y - 3 * scale, x + 19 * scale, y + 11 * scale,
                         start=180, extent=180, style=tk.ARC, outline=PALETTE["ink"], width=2)
            c.create_oval(x - 3 * scale, y - 5 * scale, x + 3 * scale, y + 1 * scale,
                          fill=PALETTE["ink"], outline="")
            c.create_oval(x + 7 * scale, y - 5 * scale, x + 13 * scale, y + 1 * scale,
                          fill=PALETTE["ink"], outline="")

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
        c.create_text(400, 145,
                      text=f"ROUND {self.round_number}  |  Clear every toy to earn {self.round_reward} coins",
                      fill=PALETTE["ink"], font=("Trebuchet MS", 10, "bold"))
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
        c.create_text(400, 564, text="ARROWS MOVE   SPACE GRAB   S SHOP   C COLLECTION   R RESET",
                      fill=PALETTE["ink"], font=("Trebuchet MS", 9, "bold"))


def main() -> None:
    root = tk.Tk()
    ClawMachine(root)
    root.mainloop()


if __name__ == "__main__":
    main()
