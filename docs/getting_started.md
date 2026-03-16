Getting Started — Battlecode workspace

This guide walks you through a practical, modular workflow for developing bots in this repository. Follow sections in order to get a working dev environment, a minimal bot, and best practices for performance and maintainability.

1) Quick setup

- Create and activate a Python virtualenv (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

- Install the Battlecode CLI `cambc` (see top-level README for quick commands):

```bash
pip install cambc
# or using pipx
python -m pip install --user pipx && python -m pipx ensurepath
pipx install cambc
```

- Verify the CLI:

```bash
cambc --help
```

2) Repo layout (recommended)

- `bots/` — one folder per bot/strategy (e.g. `bots/example_bot/`). Keep each bot self-contained.
- `tools/` — helper scripts (replays, converters, visualisers).
- `docs/` — reference notes and CLI docs ([docs/cli_ref.md](docs/cli_ref.md)).
- `knowledge.md` — short spec summary.
- `README.md` — high-level quickstart.

3) Minimal development loop

- Implement your bot entrypoint as `run(c)` in a file like `bots/your_bot/bot.py`.
- Run locally:

```bash
cambc run --bot-path ./bots/your_bot
```

- For accurate performance testing (Graviton3 hardware parity):

```bash
cambc test-run --bot-path ./bots/your_bot
```

4) Modular code architecture (follow the PDF’s guidance)

- Split code by concern (examples):
  - `bots/<bot>/entry.py` — minimal `run(c)` wrapper and per-unit dispatch.
  - `bots/<bot>/units/*.py` — per-unit logic modules (e.g., `builder.py`, `turret.py`).
  - `bots/<bot>/core/*.py` — shared core utilities (pathfinding, map caching).
  - `bots/<bot>/comm/*.py` — marker/encoding helpers for unit coordination.
  - `bots/<bot>/config.py` — constants, tuneable params.

- Keep modules small and focused. Export tiny, well-typed functions rather than monolithic classes.

- Per-unit instance pattern: treat each unit as a thin runner that calls into pure functions/strategies, passing only IDs and primitive state.

5) Per-round performance practices

- Budgeting:
  - Each unit has 2 ms per round (+5% buffer). Avoid heavy work in `run()`.
  - Use `cambc test-run` to measure execution time on target hardware.

- Minimise allocations:
  - Reuse lists and simple caches across rounds (module-level or persistent maps keyed by entity id).
  - Avoid constructing complex objects for every query; prefer raw tuples and primitive types.

- ID-first API:
  - Use entity IDs with controller getters (e.g., `c.get_hp(id)`) rather than building wrappers each round.

- Time-slicing strategies:
  - Spread expensive computations across rounds using deterministic scheduling (e.g., run heavy map analysis every N rounds, not every round).

6) Coordination primitives

- Markers: pack small messages into markers for cheap communication; each unit can place one marker per round within action radius.
- Conventions: design compact marker encoding (bitfields, small integers) and document formats in `comm/` module.

7) Debugging & observability

- Use `print()` for per-unit stdout captured in replays; use `stderr` for local real-time logs.
- Visual overlays:

```python
c.draw_indicator_line(pos_a, pos_b, r, g, b)
c.draw_indicator_dot(pos, r, g, b)
```

- Keep debug overlays conditional (toggle via `config.DEBUG`) to avoid replay clutter.

8) Testing & CI ideas

- Local smoke: `cambc run` for rapid iteration.
- Performance/regression: `cambc test-run` in CI matrix (small number of maps/time limits).
- Suggested GitHub Actions job:

```yaml
# example job snippet
jobs:
  test-run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install cambc
        run: pip install cambc
      - name: Run test-run
        run: cambc test-run --bot-path ./bots/example_bot
```

9) Examples & templates

- Keep `bots/example_bot/` as a minimal, well-documented template. Expand with modules as you build complexity.

10) Next steps (recommended)

- Add a `bots/<bot>/tests/` folder with small, deterministic unit tests for pure functions (pathfinding, marker encoding).
- Create a CI job for `cambc test-run` to catch regressions early.
- Build a small replay visualiser script in `tools/` to aggregate `print()` logs per unit.

References

- Official spec overview: https://docs.battlecode.cam/spec/overview
- Project README: [README.md](README.md)
