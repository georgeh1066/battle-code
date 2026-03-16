**Battlecode Knowledge (Concise)**

- **Setting / Objective:** Collect and refine axionite and titanium; destroy the enemy core or win via tiebreakers after 2000 rounds.
- **Map:** Rectangular grid (20×20 to 50×50). Maps are symmetric (reflection or rotation).

- **Resources:** Axionite (refined) and titanium. Harvesters mine ore automatically; conveyors deliver resources to cores.

- **Units & Buildings:**
  - **Core:** central building; action radius √8 (r² = 8) from centre.
  - **Builder bot:** mobile unit (only mobile unit). Has move and action cooldowns.
  - **Turrets:** multiple attack types (gunner, sentinel, breach, launcher) with varying stats.
  - **Harvesters:** not units — automatic resource collectors.

- **Action & Vision:** Units have vision and action radii. Most units action radius = √2 (r² = 2). Use these ranges for building/marker placement.

- **Markers:** Each unit may place one marker per round within action radius. You can overwrite friendly markers, not enemy markers.

- **Entity IDs:** All entities have integer IDs. Use the Controller API getters (e.g., `c.get_hp(id)`, `c.get_position(id)`) — ID-based API is faster.

- **Cooldowns:** Action and move cooldowns are integers that tick down each round. Actions/movement only when cooldown = 0.

- **Computation limits:** 2 ms CPU per unit per round with a 5% buffer; exceed -> interrupted. Local runner (`cambc run`) does NOT enforce time limits; use `cambc test-run` to emulate contest hardware.

- **Memory limit:** 1 GB per bot process.

- **Self-destruct:** Units may self-destruct. Builder bots deal 20 damage to their tile on self-destruct.

- **Win tiebreakers (if both cores alive at 2000 rounds):**
  1. Axionite delivered
  2. Titanium delivered
  3. Harvesters alive
  4. Axionite stored
  5. Titanium stored
  6. Coinflip

- **Debugging tips:**
  - `print()` (stdout) is captured in replays per unit.
  - `stderr` prints to console in real time for local runs.
  - Use `c.draw_indicator_line()` / `c.draw_indicator_dot()` for visual overlays in replays.

- **Practical tips:**
  - Profile per-round runtime; avoid large allocations inside `run()`.
  - Use markers and simple emergent protocols for coordination.
  - Prefer ID-based queries and minimal object construction.

- **Docs:** See the full spec: https://docs.battlecode.cam/spec/overview
