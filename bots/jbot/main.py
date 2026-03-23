"""Starter bot - a simple example to demonstrate usage of the Controller API.

Each unit gets its own Player instance; the engine calls run() once per round.
Use Controller.get_entity_type() to branch on what kind of unit you are.

This bot:
  - Core: spawns up to 3 builder bots on random adjacent tiles
  - Builder bot: builds a harvester on any adjacent ore tile, then moves in a
    random direction (laying a road first so the tile is passable), and places
    a marker recording the current round number
"""

import random

from cambc import Controller, Direction, EntityType, Environment, Position

DIRECTIONS = [d for d in Direction if d != Direction.CENTRE]

class Player:
    def __init__(self):
        self.num_spawned = 0
        self.target = (0, 0)
        self.core_pos = (0, 0)
        self.ti_poses = []  # list of known titanium ore positions
        self.ax_poses = []  # list of known axionite ore positions
        self.wall_poses = []  # list of known wall positions
        self.searched = False  # whether we've done a search for ore yet (for the core)

    def run(self, ct: Controller) -> None:
        etype = ct.get_entity_type()
        if etype == EntityType.CORE:

            # Record the core's position and nearby titanium and axionite ore positions and wall positions.

            if not self.searched:
                self.core_pos = ct.get_position()
                for tile in ct.get_nearby_tiles():
                    if ct.get_tile_env(tile).name == "ORE_TITANIUM":
                        self.ti_poses.append(tile)
                    if ct.get_tile_env(tile).name == "ORE_AXIONITE":
                        self.ax_poses.append(tile)
                    if ct.get_tile_env(tile).name == "WALL":
                        self.wall_poses.append(tile)
                self.searched = True

            # Then, if we have any known titanium ore positions, try to spawn a builder bot at position closest to the ore.
            
            if self.ti_poses != []:
                ti = self.ti_poses[0]
                dir = self.core_pos.direction_to(ti)
                spawn_pos = self.core_pos.add(dir)
                if ct.can_spawn(spawn_pos):
                    ct.spawn_builder(spawn_pos)
                    self.num_spawned += 1
                    self.ti_poses.pop(0)
                else:
                    ct.draw_indicator_dot((2,1), 255, 0, 0)

        elif etype == EntityType.BUILDER_BOT:

            # Check nearby tiles for ore and record their positions.

            for tile in ct.get_nearby_tiles():
                if ct.get_tile_env(tile).name == "ORE_TITANIUM":
                    self.ti_poses.append(tile)
                if ct.get_tile_env(tile).name == "ORE_AXIONITE":
                    self.ax_poses.append(tile)
                if ct.get_tile_env(tile).name == "WALL":
                    self.wall_poses.append(tile)
            
            # set target to the closest known titanium ore position, and move towards it, building a conveyor if possible. If we are adjacent to the target ore, build a harvester on it. Finally, place a marker in a random adjacent tile.

            self.target = self.ti_poses[0]
            dir = ct.get_position().direction_to(self.target)

            
            move_pos = ct.get_position().add(dir)
            if ct.can_build_conveyor(move_pos, dir.opposite()):
                ct.build_conveyor(move_pos, dir.opposite())
            if ct.can_move(dir):
                ct.move(dir)

            for d in Direction:
                check_pos = ct.get_position().add(d)
                if ct.can_build_harvester(check_pos):
                    ct.build_harvester(check_pos)
                    break

            marker_pos = ct.get_position().add(random.choice(DIRECTIONS))
            if ct.can_place_marker(marker_pos):
                ct.place_marker(marker_pos, marker_pos[0])
