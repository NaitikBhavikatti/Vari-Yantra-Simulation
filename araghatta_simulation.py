"""Interactive Araghatta (water wheel) simulation.

Run in VS Code with:
    python araghatta_simulation.py

This version uses only Python's built-in Tkinter module.
"""

from __future__ import annotations

import math
import random
import time
import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk


TAU = math.tau


@dataclass
class SplashParticle:
    x: float
    y: float
    vx: float
    vy: float
    life: float


class AraghattaSimulation(tk.Tk):
    """A desktop version of the shared Araghatta canvas simulation."""

    BG = "#F8FAFD"
    PANEL = "#FFFFFF"
    TEXT = "#1B1C1D"
    MUTED = "#444746"
    PRIMARY = "#0B57D0"
    WOOD_DARK = "#5C3A21"
    WOOD_MID = "#8B5A2B"
    WOOD_LIGHT = "#CD853F"
    WATER = "#0288D1"
    WATER_LIGHT = "#B3E5FC"
    CLAY = "#A0522D"
    CLAY_DARK = "#5C2C16"

    def __init__(self) -> None:
        super().__init__()
        self.title("Araghatta (Water Wheel) Simulation")
        self.minsize(850, 650)
        self.geometry("1100x760")
        self.configure(background=self.BG)

        self.speed = tk.IntVar(value=6)
        self.bucket_count = tk.IntVar(value=8)
        self.volume = tk.IntVar(value=5)
        self.playing = True
        self.angle = 0.0
        self.last_frame = time.perf_counter()
        self.splash_particles: list[SplashParticle] = []

        self._make_ui()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.after(16, self.animate)

    def _make_ui(self) -> None:
        header = tk.Frame(self, bg=self.PANEL, padx=20, pady=14)
        header.pack(fill="x")

        tk.Label(
            header,
            text="Araghatta (Water Wheel) Simulation",
            font=("Segoe UI", 17, "bold"),
            bg=self.PANEL,
            fg=self.TEXT,
        ).pack(anchor="w")
        tk.Label(
            header,
            text="Adjust the wheel settings to see how they affect water flow.",
            font=("Segoe UI", 10),
            bg=self.PANEL,
            fg=self.MUTED,
        ).pack(anchor="w", pady=(2, 0))

        controls = tk.Frame(self, bg=self.PANEL, padx=20, pady=10)
        controls.pack(fill="x", pady=(1, 0))
        controls.grid_columnconfigure(1, weight=1)
        controls.grid_columnconfigure(3, weight=1)

        self._add_slider(controls, "RPM", self.speed, 1, 20, 0, 0)
        self._add_slider(controls, "Bucket Count", self.bucket_count, 4, 12, 0, 2)
        self._add_slider(controls, "Capacity (L)", self.volume, 2, 10, 1, 0)

        buttons = tk.Frame(controls, bg=self.PANEL)
        buttons.grid(row=1, column=2, columnspan=2, sticky="ew", padx=(25, 0), pady=(6, 8))
        buttons.grid_columnconfigure(0, weight=1)
        buttons.grid_columnconfigure(1, weight=1)

        self.play_button = tk.Button(
            buttons,
            command=self.toggle_play,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            bg=self.PRIMARY,
            fg="white",
            activebackground="#0A45B4",
            activeforeground="white",
            padx=12,
            pady=6,
        )
        self.play_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        tk.Button(
            buttons,
            text="Reset",
            command=self.reset,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            bg="#E9EBF0",
            fg=self.TEXT,
            activebackground="#DEE1E3",
            padx=12,
            pady=6,
        ).grid(row=0, column=1, sticky="ew", padx=(5, 0))

        dashboard = tk.Frame(self, bg=self.BG, padx=20, pady=12)
        dashboard.pack(fill="x")
        self.lpm_label = self._hud_card(dashboard, "Flow Rate (L/min)")
        self.lpm_label.master.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.lph_label = self._hud_card(dashboard, "Flow Rate (L/hr)")
        self.lph_label.master.pack(side="left", fill="x", expand=True, padx=(6, 0))

        canvas_holder = tk.Frame(self, bg=self.PANEL, padx=10, pady=10)
        canvas_holder.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.canvas = tk.Canvas(canvas_holder, bg="#FFFFFF", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _event: self.draw())

        for variable in (self.speed, self.bucket_count, self.volume):
            variable.trace_add("write", self.update_hud)
        self.update_hud()
        self._update_play_button()

    def _add_slider(
        self,
        parent: tk.Frame,
        title: str,
        variable: tk.IntVar,
        minimum: int,
        maximum: int,
        row: int,
        column: int,
    ) -> None:
        label = tk.Label(
            parent,
            text=title,
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Segoe UI", 10, "bold"),
        )
        label.grid(row=row, column=column, sticky="w", pady=(4, 0))
        value = tk.Label(
            parent,
            textvariable=variable,
            width=3,
            anchor="e",
            bg=self.PANEL,
            fg=self.PRIMARY,
            font=("Segoe UI", 10, "bold"),
        )
        value.grid(row=row, column=column + 1, sticky="e", padx=(8, 12), pady=(4, 0))
        slider = ttk.Scale(
            parent,
            from_=minimum,
            to=maximum,
            orient="horizontal",
            command=lambda raw_value, var=variable: var.set(round(float(raw_value))),
        )
        slider.set(variable.get())
        slider.grid(row=row + 1, column=column, columnspan=2, sticky="ew", padx=(0, 12), pady=(0, 8))

    def _hud_card(self, parent: tk.Frame, title: str) -> tk.Label:
        card = tk.Frame(parent, bg="#E8F0FE", padx=16, pady=10)
        tk.Label(
            card,
            text=title,
            font=("Segoe UI", 9),
            bg="#E8F0FE",
            fg=self.MUTED,
        ).pack(anchor="w")
        value = tk.Label(
            card,
            font=("Segoe UI", 20, "bold"),
            bg="#E8F0FE",
            fg="#041E49",
        )
        value.pack(anchor="w")
        return value

    def update_hud(self, *_unused: object) -> None:
        litres_per_minute = self.speed.get() * self.bucket_count.get() * self.volume.get()
        self.lpm_label.configure(text=f"{litres_per_minute:,}")
        self.lph_label.configure(text=f"{litres_per_minute * 60:,}")

    def toggle_play(self) -> None:
        self.playing = not self.playing
        self._update_play_button()

    def _update_play_button(self) -> None:
        self.play_button.configure(text="❚❚  Pause" if self.playing else "▶  Play")

    def reset(self) -> None:
        self.speed.set(6)
        self.bucket_count.set(8)
        self.volume.set(5)
        self.playing = True
        self.angle = 0.0
        self.splash_particles.clear()
        self._update_play_button()
        self.draw()

    def animate(self) -> None:
        now = time.perf_counter()
        dt = min(now - self.last_frame, 0.05)
        self.last_frame = now
        if self.playing:
            rotations_per_second = self.speed.get() / 60
            self.angle = (self.angle + rotations_per_second * TAU * dt) % TAU
        self.draw(dt)
        self.after(16, self.animate)

    @staticmethod
    def _rotated_rectangle(
        center_x: float, center_y: float, width: float, height: float, angle: float
    ) -> list[float]:
        """Return four canvas points for a rectangle rotated about its centre."""
        points: list[float] = []
        cosine, sine = math.cos(angle), math.sin(angle)
        for x, y in ((-width / 2, -5), (width / 2, -5), (width / 2, height - 5), (-width / 2, height - 5)):
            points.extend((center_x + x * cosine - y * sine, center_y + x * sine + y * cosine))
        return points

    def draw(self, dt: float = 0.0) -> None:
        canvas = self.canvas
        width, height = canvas.winfo_width(), canvas.winfo_height()
        if width < 20 or height < 20:
            return
        canvas.delete("all")

        # Geometry layout — matched to the shared browser simulation.
        wheel_x = width * 0.42
        wheel_y = height * 0.48
        wheel_r = min(width, height) * 0.32
        rim_thickness = 12
        pool_y = wheel_y + wheel_r * 0.45
        trough_x = wheel_x + wheel_r * 0.35
        trough_y = wheel_y - wheel_r * 0.65
        trough_w = width * 0.38
        trough_h = 18

        # 1. Wooden A-frame support.
        self._line(wheel_x - wheel_r * 0.7, pool_y + 40, wheel_x, wheel_y, self.WOOD_DARK, 14)
        self._line(wheel_x, wheel_y, wheel_x + wheel_r * 0.7, pool_y + 40, self.WOOD_DARK, 14)
        self._line(wheel_x - wheel_r * 0.4, wheel_y + wheel_r * 0.4,
                   wheel_x + wheel_r * 0.4, wheel_y + wheel_r * 0.4, self.WOOD_DARK, 10)

        # 2. Raised collector trough and its support.
        canvas.create_rectangle(trough_x + 60, trough_y + trough_h, trough_x + 76, height,
                                fill=self.WOOD_MID, outline="")
        canvas.create_polygon(
            trough_x, trough_y, trough_x + trough_w, trough_y + 12,
            trough_x + trough_w, trough_y + 12 + trough_h, trough_x, trough_y + trough_h,
            fill=self.WOOD_DARK, outline=""
        )
        canvas.create_polygon(
            trough_x + 5, trough_y + 4, trough_x + trough_w - 2, trough_y + 14,
            trough_x + trough_w - 2, trough_y + trough_h + 6, trough_x + 5, trough_y + trough_h - 5,
            fill=self.WATER, outline=""
        )

        # 3. Water reservoir and its moving surface.
        canvas.create_rectangle(0, pool_y, width, height, fill="#6FC4F0", outline="")
        wave: list[float] = []
        for x in range(0, width + 20, 20):
            wave.extend((x, pool_y + math.sin(x * 0.05 + self.angle * 4) * 3))
        canvas.create_line(*wave, fill=self.WATER_LIGHT, width=3, smooth=True)

        # 4. Wheel rims, spokes, and hub.
        canvas.create_oval(wheel_x - wheel_r, wheel_y - wheel_r, wheel_x + wheel_r, wheel_y + wheel_r,
                           outline=self.WOOD_MID, width=rim_thickness)
        for radius in (wheel_r - rim_thickness / 2, wheel_r + rim_thickness / 2, wheel_r * 0.4):
            canvas.create_oval(wheel_x - radius, wheel_y - radius, wheel_x + radius, wheel_y + radius,
                               outline=self.WOOD_DARK, width=3 if radius == wheel_r * 0.4 else 6)

        spoke_count = max(self.bucket_count.get(), 6)
        for index in range(spoke_count):
            spoke_angle = self.angle + index * TAU / spoke_count
            self._line(
                wheel_x + math.cos(spoke_angle) * wheel_r * 0.4,
                wheel_y + math.sin(spoke_angle) * wheel_r * 0.4,
                wheel_x + math.cos(spoke_angle) * wheel_r,
                wheel_y + math.sin(spoke_angle) * wheel_r,
                self.WOOD_LIGHT,
                6,
            )
        canvas.create_oval(wheel_x - 22, wheel_y - 22, wheel_x + 22, wheel_y + 22,
                           fill=self.WOOD_DARK, outline="")
        canvas.create_oval(wheel_x - 8, wheel_y - 8, wheel_x + 8, wheel_y + 8,
                           fill="white", outline="")

        # 5. Clay buckets: fill at the bottom, lift on the left, tip into the trough at the top.
        bucket_width = 22 + self.volume.get() * 1.5
        bucket_height = 26 + self.volume.get() * 1.8
        pouring_origin: tuple[float, float] | None = None
        for index in range(self.bucket_count.get()):
            bucket_angle = (self.angle + index * TAU / self.bucket_count.get()) % TAU
            bucket_x = wheel_x + math.cos(bucket_angle) * wheel_r
            bucket_y = wheel_y + math.sin(bucket_angle) * wheel_r
            normalized = bucket_angle
            fill_ratio = self._bucket_fill_ratio(normalized)
            tip_angle = 0.0
            if 1.25 * math.pi <= normalized <= 1.6 * math.pi:
                tip_angle = (normalized - 1.25 * math.pi) * 1.5
            self._draw_bucket(bucket_x, bucket_y, bucket_width, bucket_height, tip_angle, fill_ratio)
            if self.playing and 1.3 * math.pi <= normalized <= 1.58 * math.pi:
                pouring_origin = (bucket_x, bucket_y)

        # 6. The pouring stream and splash particles.
        if pouring_origin is not None:
            source_x, source_y = pouring_origin
            self._quadratic_line(source_x, source_y, source_x + 15, trough_y - 10,
                                 trough_x + 25, trough_y + 6, self.WATER_LIGHT, 3 + self.volume.get() * 0.5)
            if random.random() < 0.6:
                self.splash_particles.append(
                    SplashParticle(
                        trough_x + 20 + (random.random() - 0.5) * 15,
                        trough_y + 5,
                        (random.random() - 0.5) * 40,
                        -random.random() * 30 - 10,
                        0.3,
                    )
                )

        # 7. Water leaving the collector trough on the right.
        if self.playing:
            exit_x, exit_y = trough_x + trough_w, trough_y + 14
            canvas.create_polygon(
                exit_x - 5, exit_y, exit_x + 15, exit_y + 30, exit_x + 20, height,
                exit_x + 5, height, exit_x, exit_y + 30,
                fill="#2196D3", outline=""
            )

        # 8. Update and draw splash particles.
        for particle in self.splash_particles[:]:
            particle.x += particle.vx * dt
            particle.y += particle.vy * dt
            particle.vy += 200 * dt
            particle.life -= dt
            if particle.life <= 0:
                self.splash_particles.remove(particle)
                continue
            canvas.create_oval(particle.x - 2.5, particle.y - 2.5, particle.x + 2.5, particle.y + 2.5,
                               fill=self.WATER_LIGHT, outline="")

        self._tag(wheel_x - wheel_r * 0.6, pool_y + 25, "Water Source (Vari)", self.PRIMARY)
        self._tag(trough_x + trough_w * 0.4, trough_y - 18, "Collector Trough", "#146C2E")

    @staticmethod
    def _bucket_fill_ratio(angle: float) -> float:
        if 0.35 * math.pi <= angle <= 1.3 * math.pi:
            return 1.0
        if 1.3 * math.pi <= angle <= 1.58 * math.pi:
            return 1.0 - (angle - 1.3 * math.pi) / (0.28 * math.pi)
        return 0.0

    def _draw_bucket(
        self, x: float, y: float, width: float, height: float, tip_angle: float, fill_ratio: float
    ) -> None:
        canvas = self.canvas
        canvas.create_polygon(*self._rotated_rectangle(x, y, width, height, tip_angle),
                              fill=self.CLAY, outline=self.CLAY_DARK, width=2)
        if fill_ratio > 0.05:
            # Water sits in the lower part of the bucket.  It follows the bucket as it tips.
            water_height = (height - 4) * fill_ratio
            water_center_y = height - 5 - water_height / 2
            cosine, sine = math.cos(tip_angle), math.sin(tip_angle)
            corners: list[float] = []
            for local_x, local_y in ((-width / 2 + 2, water_center_y - water_height / 2),
                                     (width / 2 - 2, water_center_y - water_height / 2),
                                     (width / 2 - 2, water_center_y + water_height / 2),
                                     (-width / 2 + 2, water_center_y + water_height / 2)):
                corners.extend((x + local_x * cosine - local_y * sine, y + local_x * sine + local_y * cosine))
            canvas.create_polygon(*corners, fill=self.WATER, outline="")
        # Bucket rim and mounting pin.
        rim = self._rotated_rectangle(x, y - 5, width + 4, 4, tip_angle)
        canvas.create_polygon(*rim, fill=self.WOOD_DARK, outline="")
        canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill=self.WOOD_DARK, outline="")

    def _line(self, x1: float, y1: float, x2: float, y2: float, colour: str, line_width: float) -> None:
        self.canvas.create_line(x1, y1, x2, y2, fill=colour, width=line_width, capstyle="round")

    def _quadratic_line(
        self, x0: float, y0: float, x1: float, y1: float, x2: float, y2: float, colour: str, line_width: float
    ) -> None:
        points: list[float] = []
        for step in range(21):
            t = step / 20
            inverse = 1 - t
            points.extend((
                inverse * inverse * x0 + 2 * inverse * t * x1 + t * t * x2,
                inverse * inverse * y0 + 2 * inverse * t * y1 + t * t * y2,
            ))
        self.canvas.create_line(*points, fill=colour, width=line_width, smooth=True, capstyle="round")

    def _tag(self, x: float, y: float, text: str, colour: str) -> None:
        tag = self.canvas.create_text(x, y, text=text, fill=colour, font=("Segoe UI", 9, "bold"), anchor="center")
        x1, y1, x2, y2 = self.canvas.bbox(tag)
        rectangle = self.canvas.create_rectangle(x1 - 6, y1 - 3, x2 + 6, y2 + 3, fill="white", outline="#DCDDE5")
        self.canvas.tag_lower(rectangle, tag)


if __name__ == "__main__":
    AraghattaSimulation().mainloop()
