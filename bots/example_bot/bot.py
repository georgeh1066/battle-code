"""Example Battlecode bot template (Python).

This is a minimal starting point. Replace placeholder calls with the
correct Controller API usage from the official spec.

The engine calls `run(c)` each round for each unit controlled by this
bot. Keep per-round work small to stay within the 2ms limit.
"""

from typing import List


def run(c):
    """Entry point called each round with controller `c`.

    `c` exposes the Controller API (see docs). This template shows basic
    patterns: iterating nearby entities, placing a marker, and a simple
    cooldown-aware action.
    """

    # Example: iterate nearby entities and log harvesters
    try:
        for eid in c.get_nearby_entities():
            if c.get_entity_type(eid) == c.EntityType.HARVESTER:
                pos = c.get_position(eid)
                print(f"Saw harvester {eid} at {pos}")

        # Example: place a marker at unit position (pseudo-code)
        my_pos = c.get_position(c.get_my_id())
        # Marker payloads and API vary; replace with actual call:
        # c.place_marker(my_pos, some_marker_value)

    except Exception as e:
        # Keep exceptions from crashing the agent process.
        # stderr is useful for local debugging.
        import sys
        print("Error in run:", e, file=sys.stderr)


if __name__ == "__main__":
    print("This file is a bot template. Run it via the Battlecode runner.")
