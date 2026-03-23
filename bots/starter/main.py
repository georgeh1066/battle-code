
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
import sys

from cambc import Controller, Direction, EntityType, Environment, Position

# non-centre directions
DIRECTIONS = [d for d in Direction if d != Direction.CENTRE]

class Player:
    def __init__(self):
        self.num_spawned = 0  # number of builder bots spawned so far (core)

        # Vision state (refreshed each turn)
        self.visible_positions: set[Position] = set()
        self.env_map: dict[Position, Environment] = {}
        self.ti_ore_positions = []  # positions of titanium ore tiles within vision
        self.ax_ore_positions = []  # positions of axionite ore tiles within vision
        self.wall_positions = []  # positions of wall tiles within vision

    def run(self, ct: Controller) -> None:
        # Refresh vision each turn; used by both core and builder logic
        self.UpdateMapVision(ct)

        etype = ct.get_entity_type()

        # core logic
        if etype == EntityType.CORE:
            if self.num_spawned < 3:
                # Get map dimensions and check if edge is visible
                map_width = ct.get_map_width()
                map_height = ct.get_map_height()
                can_see_edge = any(
                    pos.x == 0
                    or pos.x == map_width - 1
                    or pos.y == 0
                    or pos.y == map_height - 1
                    for pos in self.visible_positions
                )

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

                    ore_positions = self.ti_ore_positions + self.ax_ore_positions
               

                    for spawn_pos in possible_spawns:
                        # Ore distance
                        ore_dist = min(spawn_pos.distance_squared(o) for o in ore_positions) if ore_positions else 0

                        # Edge distance (squared to nearest edge)
                        edge_dist = min(
                            spawn_pos.x,
                            map_width - 1 - spawn_pos.x,
                            spawn_pos.y,
                            map_height - 1 - spawn_pos.y,
                        ) ** 2

                        # Wall penalty: penalize if nearest wall is within 2 tiles (dist_sq <= 4)
                        wall_penalty = 0
                        if self.wall_positions:
                            min_wall_dist = min(spawn_pos.distance_squared(w) for w in self.wall_positions)
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

        # bot logic
        elif etype == EntityType.BUILDER_BOT:
            # if we are adjacent to an ore tile, build a harvester on it
            for d in Direction:
                check_pos = ct.get_position().add(d)
                if ct.can_build_harvester(check_pos):
                    ct.build_harvester(check_pos)
                    break

            ore_positions = self.ti_ore_positions + self.ax_ore_positions
            # Visualize ore positions (debug)
            
            start = ct.get_position()
            next_pos = self._find_path_to_nearest_goal(ct, start, ore_positions)
            
            if next_pos:
                # Build road if next_pos is not passable (to allow movement through it)
                if not ct.is_tile_passable(next_pos):
                    if ct.can_build_road(next_pos):
                        ct.build_road(next_pos)
                
                move_dir = start.direction_to(next_pos)
                if ct.can_move(move_dir):
                    ct.move(move_dir)
            else:
                # No closer neighbors; search for new ore
                new_ore = self._find_new_ore_to_explore(ct, start, ore_positions)
                if new_ore:
                    move_dir = start.direction_to(new_ore)
                    move_pos = start.add(move_dir)
                    if not ct.is_tile_passable(move_pos):
                        if ct.can_build_road(move_pos):
                            ct.build_road(move_pos)
                    if ct.can_move(move_dir):
                        ct.move(move_dir)
                else:
                    # fallback movement
                    move_dir = random.choice(DIRECTIONS)
                    move_pos = ct.get_position().add(move_dir)
                    if not ct.is_tile_passable(move_pos):
                        if ct.can_build_road(move_pos):
                            ct.build_road(move_pos)
                    if ct.can_move(move_dir):
                        ct.move(move_dir)

    
    
    def UpdateMapVision(self, ct: Controller):
        # Collect ore and wall positions within vision (cleared each turn)
        self.visible_positions = set(ct.get_nearby_tiles())
        self.env_map = {pos: ct.get_tile_env(pos) for pos in self.visible_positions}

        self.ti_ore_positions = []
        self.ax_ore_positions = []
        self.wall_positions = []

        for pos, env in self.env_map.items():
            if env == Environment.ORE_TITANIUM:
                # Only add if no building (harvester) already on it
                if ct.get_tile_building_id(pos) is None:
                    self.ti_ore_positions.append(pos)
            elif env == Environment.ORE_AXIONITE:
                # Only add if no building (harvester) already on it
                if ct.get_tile_building_id(pos) is None:
                    self.ax_ore_positions.append(pos)
            elif env == Environment.WALL:
                self.wall_positions.append(pos)

    def _find_path_to_nearest_goal(self, ct: Controller, start: Position, goals: list[Position]) -> Position | None:
        for ore_pos in goals:
                ct.draw_indicator_dot(ore_pos, 0, 0, 255)

        
        if not goals:
            return None
        
        # Distance from current position to nearest ore
        current_dist_to_ore = min(start.distance_squared(g) for g in goals)
        
        best_neighbour = None
        min_dist = float('inf')
        for d in DIRECTIONS:
            neighbour = start.add(d)
            if self.env_map.get(neighbour) == Environment.WALL:
                continue
            
            # Check if passable; if not, check if we can build a road
            if not ct.is_tile_passable(neighbour):
                if not ct.can_build_road(neighbour):
                    continue
                # Can build road; consider this neighbor as buildable
            
            dist = min(neighbour.distance_squared(g) for g in goals)
            # Only consider this neighbor if it actually gets closer to ore
            if dist < current_dist_to_ore and dist < min_dist:
                min_dist = dist
                best_neighbour = neighbour
        print(start, best_neighbour, goals)
        
        if best_neighbour:
            return best_neighbour
        
        # Greedy pathfinding failed; use bug navigation to navigate around obstacles
        return self._bug_nav_around_obstacle(ct, start, goals)


    def _bug_nav_around_obstacle(self, ct: Controller, start: Position, goals: list[Position]) -> Position | None:
        """Navigate around obstacles using a bug algorithm (right-hand wall following).
        
        When direct greedy path is blocked, rotate around obstacles in a pattern to find a way through.
        """
        if not goals:
            return None
        
        nearest_goal = min(goals, key=lambda g: start.distance_squared(g))
        
        # Try neighbors in rotational pattern (right-hand rule-like approach)
        # Prioritize: passable toward ore > buildable toward ore > passable > buildable
        candidates = []
        
        for d in DIRECTIONS:
            neighbor = start.add(d)
            
            # Skip walls
            if self.env_map.get(neighbor) == Environment.WALL:
                continue
            
            is_passable = ct.is_tile_passable(neighbor)
            can_build = ct.can_build_road(neighbor) if not is_passable else False
            
            # Skip if neither passable nor buildable
            if not is_passable and not can_build:
                continue
            
            dist = neighbor.distance_squared(nearest_goal)
            current_dist = start.distance_squared(nearest_goal)
            
            # Categorize neighbor
            if is_passable:
                if dist < current_dist:
                    # Passable and gets closer: highest priority
                    candidates.append((0, dist, neighbor))
                else:
                    # Passable but not closer: medium priority
                    candidates.append((2, dist, neighbor))
            elif can_build:
                if dist < current_dist:
                    # Buildable and gets closer: high priority
                    candidates.append((1, dist, neighbor))
                else:
                    # Buildable but not closer: lower priority
                    candidates.append((3, dist, neighbor))
        
        # Sort by priority, then by distance
        if candidates:
            candidates.sort(key=lambda x: (x[0], x[1]))
            return candidates[0][2]
        
        return None

    def _find_new_ore_to_explore(self, ct: Controller, start: Position, known_ore: list[Position]) -> Position | None:
        """Explore toward map center when all visible ore is blocked. Pick a neighbor that moves toward center."""
        map_width = ct.get_map_width()
        map_height = ct.get_map_height()
        map_center = Position(map_width // 2, map_height // 2)
        
        # Find the best neighbor that moves toward map center
        best_neighbor = None
        min_dist_to_center = float('inf')
        
        for d in DIRECTIONS:
            neighbor = start.add(d)
            if self.env_map.get(neighbor) == Environment.WALL:
                continue
            if not ct.is_tile_passable(neighbor):
                continue
            
            dist = neighbor.distance_squared(map_center)
            if dist < min_dist_to_center:
                min_dist_to_center = dist
                best_neighbor = neighbor
        
        return best_neighbor
       