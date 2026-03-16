Example bot template

This folder contains a minimal Python bot example.

Run with `cambc` (see top-level README for install):

```bash
# from repo root
cambc run --bot-path ./bots/example_bot
```

Edit `bot.py` to implement your bot logic. Keep `run(c)` fast and avoid
large allocations inside the per-round hot path.
