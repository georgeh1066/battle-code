**Project Overview**

- **Purpose:** A workspace for developing Cambridge Battlecode bots: strategies, team bots, and utilities.
- **This repo:** contains starter code, docs, and examples for running and testing bots locally and on the ladder.

**Getting Started**

- **Prereqs:** Install the Battlecode toolchain (see official docs). Recommended: Python 3.10+, `cambc` CLI.
- **Run locally:** Use `cambc run` for quick local runs, and `cambc test-run` to test on the same AWS Graviton3 hardware used for ladder matches.
- **Quick test:** `cambc test-run --bot your_bot` (adjust flags per your local setup).

**Repository Layout**

- **/bots/**: (suggested) each bot in its own subfolder with an entrypoint
- **/tools/**: runner scripts, helpers, visualisers
- **README.md**: this file
- **knowledge.md**: concise rules, constraints, and tips (auto-generated)

**Key Constraints (short)**

- **CPU:** 2 ms per unit per round (+5% buffer). Exceeding this interrupts execution.
- **Memory:** 1 GB per bot process.
- **Map:** rectangular grid, 20×20 to 50×50, symmetric by reflection or rotation.

**Development workflow**

- Create a new bot folder under /bots/ with a minimal entrypoint that implements `run()` for your units.
- Use logging (`print()`) for per-unit stdout (captured in replays) and `stderr` for real-time local debugging.
- Keep per-round work small and deterministic; avoid heavy allocations in the hot path.

**Testing & Debugging**

- Use `cambc test-run` to validate performance on target hardware emulation.
- Use `c.draw_indicator_line()` and `c.draw_indicator_dot()` for visual debug overlays saved in replays.

**Resources & Links**

- Official spec overview: https://docs.battlecode.cam/spec/overview
- Project guide (reference PDF included in this repo)

**Install `cambc` (quick outline)**

- Ensure Python 3.10+ is installed and create a virtualenv (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

- Install `cambc` (if available via pip) or follow the official docs if not:

```bash
pip install cambc
# or using pipx:
python -m pip install --user pipx && python -m pipx ensurepath
pipx install cambc
```

- Verify installation:

```bash
cambc --help
```

- Run a local quick test (adjust flags to your setup):

```bash
cambc run --bot-path ./bots/example_bot
cambc test-run --bot-path ./bots/example_bot
```

If `cambc` installation differs on your system, follow the official instructions: https://docs.battlecode.cam/spec/overview

**Contributing**

- Add issues or PRs for new bot templates, CI, or helper tools.
- Keep example bots minimal and well-documented.

**Files created**

- See [README.md](README.md) and [knowledge.md](knowledge.md).
