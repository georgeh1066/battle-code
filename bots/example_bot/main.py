"""Example Battlecode bot template (Python).

This is a minimal starting point. Replace placeholder calls with the
correct Controller API usage from the official spec.

The engine calls `run(c)` each round for each unit controlled by this
bot. Keep per-round work small to stay within the 2ms limit.
"""

import random

from cambc import Controller, Direction, EntityType, Environment, Position

# non-centre directions
DIRECTIONS = [d for d in Direction if d != Direction.CENTRE]

class Player:
    def __init__(self):
        self.num_spawned = 0 # number of builder bots spawned so far (core)

    def run(self, ct: Controller) -> None:
        etype = ct.get_entity_type()
        if etype == EntityType.CORE:
            if self.num_spawned < 3:
                # if we haven't spawned 3 builder bots yet, try to spawn one on a random tile
                spawn_pos = ct.get_position().add(random.choice(DIRECTIONS))
                if ct.can_spawn(spawn_pos):
                    ct.spawn_builder(spawn_pos)
                    self.num_spawned += 1
        elif etype == EntityType.BUILDER_BOT:
            # if we are adjacent to an ore tile, build a harvester on it
            for d in Direction:
                check_pos = ct.get_position().add(d)
                if ct.can_build_harvester(check_pos):
                    ct.build_harvester(check_pos)
                    break
            
            # move in a random direction
            move_dir = random.choice(DIRECTIONS)
            move_pos = ct.get_position().add(move_dir)
            # we need to place a conveyor or road to stand on, before we can move onto a tile
            if ct.can_build_road(move_pos):
                ct.build_road(move_pos)
            if ct.can_move(move_dir):
                ct.move(move_dir)

            # place a marker on an adjacent tile with the current round number
            marker_pos = ct.get_position().add(random.choice(DIRECTIONS))
            if ct.can_place_marker(marker_pos):
                ct.place_marker(marker_pos, ct.get_current_round())