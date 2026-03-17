
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

    def run(self, ct: Controller) -> None:
        etype = ct.get_entity_type()
        if etype == EntityType.CORE:
            if self.num_spawned < 3:
                # Get map dimensions and check if edge is visible
                map_width = ct.get_map_width()
                map_height = ct.get_map_height()
                can_see_edge = any(pos.x == 0 or pos.x == map_width - 1 or pos.y == 0 or pos.y == map_height - 1 for pos in ct.get_nearby_tiles())
                
                # Collect ore and wall positions within vision
                ore_positions = []
                wall_positions = []
                for pos in ct.get_nearby_tiles():
                    env = ct.get_tile_env(pos)
                    if env in (Environment.ORE_TITANIUM, Environment.ORE_AXIONITE):
                        ore_positions.append(pos)
                    elif env == Environment.WALL:
                        wall_positions.append(pos)
                
                # Get possible spawn positions
                possible_spawns = []
                for d in DIRECTIONS:
                    spawn_pos = ct.get_position().add(d)
                    if ct.can_spawn(spawn_pos):
                        possible_spawns.append(spawn_pos)
                
                if possible_spawns:
                    # Calculate scores for each spawn position
                    best_spawns = []
                    min_score = float('inf')
                    for spawn_pos in possible_spawns:
                        # Ore distance
                        ore_dist = min(spawn_pos.distance_squared(ore) for ore in ore_positions) if ore_positions else 0
                        
                        # Edge distance (squared to nearest edge)
                        edge_dist = min(spawn_pos.x, map_width - 1 - spawn_pos.x, spawn_pos.y, map_height - 1 - spawn_pos.y) ** 2
                        
                        # Wall penalty: penalize if nearest wall is within 2 tiles (dist_sq <= 4)
                        wall_penalty = 0
                        if wall_positions:
                            min_wall_dist = min(spawn_pos.distance_squared(pos) for pos in wall_positions)
                            if min_wall_dist <= 4:
                                wall_penalty = 1000
                        
                        # Score: lower is better (close to ore, far from edge, not next to walls)
                        if can_see_edge:
                            score = ore_dist + wall_penalty - edge_dist
                        else:
                            score = ore_dist + wall_penalty
                        
                        if score < min_score:
                            min_score = score
                            best_spawns = [spawn_pos]
                        elif score == min_score:
                            best_spawns.append(spawn_pos)
                    
                    spawn_pos = random.choice(best_spawns)
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
