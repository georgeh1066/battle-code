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

# non-centre directions
DIRECTIONS = [d for d in Direction if d != Direction.CENTRE]

class Player:
    def __init__(self):
        self.num_spawned = 0 # number of builder bots spawned so far (core)
        self.target = (0, 0)
        self.core_pos = (0, 0)
        self.ti_pos = []
        self.ax_pos = []

    def run(self, ct: Controller) -> None:
        etype = ct.get_entity_type()
        if etype == EntityType.CORE:
            if ct.get_current_round() == 1:
                ct.draw_indicator_dot((1,1), 0, 0, 0)
                self.core_pos = ct.get_position()
                for tile in ct.get_nearby_tiles():
                    # ct.draw_indicator_dot(tile, 0, 255, 0)
                    if ct.get_tile_env(tile).name == "ORE_TITANIUM":
                        self.ti_pos.append(tile)
                        ct.draw_indicator_dot(tile, 0, 0, 255)
            
            if self.ti_pos != []:
                ct.draw_indicator_dot((1,2), 0, 255, 0)
                ti = self.ti_pos[0]
                dir = self.core_pos.direction_to(ti)
                spawn_pos = self.core_pos.add(dir)
                if ct.can_spawn(spawn_pos):
                    ct.spawn_builder(spawn_pos)
                    self.num_spawned += 1
                    self.ti_pos.pop(0)
                else:
                    ct.draw_indicator_dot((2,1), 255, 0, 0)
                # rel_pos = (tit[0] - self.core_pos[0], tit[1] - self.core_pos[1])
                

                    
                        
            # t = ct.get_cpu_time_elapsed()
            # ct.draw_indicator_dot((1,1), t, t, t)
            # if self.num_spawned < 3:
                # if we haven't spawned 3 builder bots yet, try to spawn one on a random tile
            #     spawn_pos = ct.get_position().add(random.choice(DIRECTIONS))
            #     if ct.can_spawn(spawn_pos):
            #         ct.spawn_builder(spawn_pos)
            #         self.num_spawned += 1
        elif etype == EntityType.BUILDER_BOT:
            for tile in ct.get_nearby_tiles():
                # ct.draw_indicator_dot(tile, 0, 255, 0)
                if ct.get_tile_env(tile).name == "ORE_TITANIUM":
                    self.ti_pos.append(tile)
                    ct.draw_indicator_dot(tile, 0, 0, 255)
                if ct.get_tile_env(tile).name == "ORE_AXIONITE":
                    self.ax_pos.append(tile)
            
            self.target = self.ti_pos[0]
            dir = ct.get_position().direction_to(self.target)

            
            move_pos = ct.get_position().add(dir)
            # we need to place a conveyor or road to stand on, before we can move onto a tile
            if ct.can_build_road(move_pos):
                ct.build_road(move_pos)
            if ct.can_move(dir):
                ct.move(dir)
            # if ct.can_build_bridge(ct.get_position(), ct.get_position().add(dir).add(dir)):
            #     ct.build_bridge(ct.get_position(), ct.get_position().add(dir).add(dir))

            
            # if we are adjacent to an ore tile, build a harvester on it
            for d in Direction:
                check_pos = ct.get_position().add(d)
                if ct.can_build_harvester(check_pos):
                    ct.build_harvester(check_pos)
                    break

            # place a marker on an adjacent tile with the current round number
            marker_pos = ct.get_position().add(random.choice(DIRECTIONS))
            if ct.can_place_marker(marker_pos):
                ct.place_marker(marker_pos, marker_pos[0])
