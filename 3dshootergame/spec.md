# Project Specification: Basic 3D FPS Prototype (spec.md)

## 1. Objective & Overview
The goal of this project is to build a functional, single-player **3D First-Person Shooter (FPS) prototype** featuring standard movement, basic shooting mechanics, a simple enemy AI loop, and win/loss states. This file serves as the strict contract for the minimum viable product (MVP).

## 2. Core Mechanics & Scope

### Player Movement & Perspective
* **View:** Locked first-person perspective using a standard camera setup attached to the player capsule.
* **Controls:**
  * `W, A, S, D` for omnidirectional movement.
  * `Spacebar` for a basic jump.
  * `Mouse Movement` for look/aim controls (clamped vertically to prevent flipping).
  * `Left Click` to fire weapon.
* **Physics:** Standard gravity applied when falling or jumping. Collision detection on walls and floor.

### Weapon & Shooting Mechanics
* **Weapon Model:** A simple static placeholder mesh positioned on the bottom right of the player’s screen.
* **Shooting Logic:** Hitscan system utilizing raycasting from the center of the camera view.
* **Visuals & Audio:** 
  * Spawn a simple crosshair visual element in the center of the UI.
  * Draw a brief tracer line or impact spark when a shot hits an object.
* **Ammo System:** Unlimited ammunition for the prototype phase (no reload mechanic required).

### Enemy System & AI
* **Enemy Primitive:** Simple 3D shapes (e.g., Red Capsules or Cubes) acting as enemies.
* **AI Behavior:** 
  * **Idle:** Wait until the player enters a defined detection radius.
  * **Chase:** Lock orientation toward the player and move continuously toward them at a set speed.
  * **Attack:** Inflict damage to the player over time when within a close melee-range threshold.
* **Enemy Health:** Enemies have 100 HP. They take a fixed amount of damage per hitscan impact and disappear (destroy object) when HP hits 0.

## 3. UI, Health, and Game States

### User Interface (UI) Canvas
* **Crosshair:** Centered on-screen indicator.
* **Health Bar:** A simple graphical slider or text element showing current Player Health.
* **Enemy Counter:** Text displaying the remaining number of active enemies in the level.

### Game States & Loop
* **Initialization:** Player spawns at `Point A`. Three (3) enemies spawn at pre-designated points across the level.
* **Player Damage:** Player starts with 100 HP. Taking damage reduces this number.
* **Lose Condition:** Player HP reaches 0 → Trigger "Game Over" UI screen with a "Restart" button.
* **Win Condition:** Enemy Counter reaches 0 → Trigger "Victory" UI screen with a "Restart" button.

## 4. Technical Constraints & Architecture

* **Performance Targets:** Maintain 60 FPS on standard desktop hardware using low-poly assets.
* **Architecture:** Separate the Player Controller logic from the Game Manager/State logic.
* **Scale & Environment:** A simple gray-box arena composed of a floor plane, 4 perimeter walls, and a few basic primitives (Cubes/Cylinders) acting as static cover obstacles.

## 5. Acceptance Criteria
1. The game boots directly into a playable 3D gray-box environment.
2. The player can look around smoothly, move, jump, and collide properly with obstacles.
3. Clicking fires a raycast that reliably prints a hit confirmation and damages enemies.
4. Enemies accurately track, move toward, and reduce the player's health when close.
5. Defeating all enemies displays the Victory screen; dying displays the Game Over screen. Both screens must successfully reset the scene when clicking "Restart".
