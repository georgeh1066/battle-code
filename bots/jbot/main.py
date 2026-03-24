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
        self.prev_targets = []
        self.enemy_core_list = []  # list of possible enemy core positions based on our core position and map size, for builder bots to target if we haven't found any ore yet
        self.core_pos = (0, 0)
        self.ti_poses = []  # list of known titanium ore positions
        self.ax_poses = []  # list of known axionite ore positions
        self.wall_poses = []  # list of known wall positions
        self.searched = False  # whether we've done a search for ore yet (for the core)
        self.change_target = True  # whether builder bots should change target.

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

            if not self.searched:
                for unit in ct.get_nearby_units(1):
                    if ct.get_entity_type(unit) == EntityType.CORE:
                        self.core_pos = ct.get_position(unit)
                        self.enemy_core_list = self.find_core(self.core_pos, (ct.get_map_width(), ct.get_map_height()))
                        self.searched = True
                

            # Check nearby tiles for ore and record their positions.

            for tile in ct.get_nearby_tiles():
                if ct.get_tile_env(tile).name == "ORE_TITANIUM":
                    self.ti_poses.append(tile)
                if ct.get_tile_env(tile).name == "ORE_AXIONITE":
                    self.ax_poses.append(tile)
                if ct.get_tile_env(tile).name == "WALL":
                    self.wall_poses.append(tile)
                if tile == self.target:
                    building_id = ct.get_tile_building_id(tile)
                    if ct.get_entity_type(building_id) != EntityType.CORE:
                        self.change_target = True

            if self.change_target:
                for i in range(len(self.enemy_core_list)):
                    if self.enemy_core_list[i] not in self.prev_targets:
                        self.target = self.enemy_core_list[i]
                        self.prev_targets.append(self.target)
                        self.change_target = False
                        break
            dir = ct.get_position().direction_to(self.target)

            
            move_pos = ct.get_position().add(dir)
            if ct.can_move(dir):
                ct.move(dir)
            if ct.can_build_road(move_pos):
                ct.build_road(move_pos)
            else:
                dir = dir.rotate_right()
                move_pos = ct.get_position().add(dir)
                if ct.can_move(dir):
                    ct.move(dir)
                if ct.can_build_road(move_pos):
                    ct.build_road(move_pos)
                else:
                    dir = dir.rotate_right()
                    move_pos = ct.get_position().add(dir)
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
    
    
    def find_core(self, cpos, map_size):

        #finds the 3 possible enemy core positions based on allied core position and map size.

        horiz_pos = Position(map_size[0]-1-cpos[0], cpos[1])
        vert_pos = Position(cpos[0], map_size[1]-1-cpos[1])
        rot_pos = Position(map_size[0]-1-cpos[0], map_size[1]-1-cpos[1])
        candidates = [horiz_pos, vert_pos, rot_pos]

        return candidates
