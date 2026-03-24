"""gbot - A smart Battlecode bot using a Core Master Brain and Marker Communication.

Because each bot runs in an isolated context without shared memory, we use 
the game engine's markers (32-bit integers) to communicate.
- The Core acts as the Master Brain, reading intel markers dropped by bots in its vision.
- The Core writes Directive markers around its base for newly spawned bots to read.
- Bots explore, find ores, and drop Intel markers back near the base for the Core.
"""

from cambc import Controller, Direction, EntityType, Environment, Position
import random

# --- CONFIGURATION ---
MAP_WIDTH = 50
MAP_HEIGHT = 50
TOTAL_TILES = MAP_WIDTH * MAP_HEIGHT

# --- PROTOCOL CONSTANTS ---
# We pack our data into the 32-bit marker integer:
# Bit 31 (1 bit): Message Type (0 = Intel from Bot, 1 = Directive from Core)
# Bits 27-30 (4 bits): POI Type (0=Titanium, 1=Axionite)
# Bits 21-26 (6 bits): X coordinate (0-63, safely covers the max 50x50 map)
# Bits 15-20 (6 bits): Y coordinate
# Bits 0-14  (15 bits): Round number (0-2000)

TYPE_INTEL = 0
TYPE_DIRECTIVE = 1

POI_TITANIUM = 1
POI_AXIONITE = 2

DIRECTIONS = [d for d in Direction if d != Direction.CENTRE]


class Player:
    def __init__(self):
        # We use a 1D bytearray for incredibly fast C-level map representation.
        # Indices are y * MAP_WIDTH + x.
        # 0 = Unknown, 1 = Empty, 2 = Wall, 3 = Titanium, 4 = Axionite
        self.map_env = bytearray(TOTAL_TILES)

        self.num_spawned = 0
        
        # We store known targets separately for easy iteration (avoiding full map sweeps)
        self.known_titanium = set()
        self.known_axionite = set()
        
        # Unit State
        self.my_core_pos = None
        self.current_directive = None
        self.path_history = set()
        self.map_w = None
        self.map_h = None

    def encode_marker(self, msg_type: int, poi_type: int, x: int, y: int, round_num: int) -> int:
        """Pack data into a 32-bit integer for marker communication."""
        val = 0
        val |= (msg_type & 0x1) << 31
        val |= (poi_type & 0xF) << 27
        val |= (x & 0x3F) << 21
        val |= (y & 0x3F) << 15
        val |= (round_num & 0x7FFF)
        return val

    def decode_marker(self, val: int) -> tuple[int, int, int, int, int]:
        """Unpack data from a 32-bit integer marker."""
        msg_type = (val >> 31) & 0x1
        poi_type = (val >> 27) & 0xF
        x = (val >> 21) & 0x3F
        y = (val >> 15) & 0x3F
        round_num = val & 0x7FFF
        return msg_type, poi_type, x, y, round_num

    def run(self, c: Controller) -> None:
        """The main entrypoint called by the engine every round. 
        Guarded heavily against the 2ms time limit.
        """
        if self.map_w is None:
            self.map_w = c.get_map_width()
            self.map_h = c.get_map_height()
            
        etype = c.get_entity_type()
        
        if etype == EntityType.CORE:
            self.run_core(c)
        elif etype == EntityType.BUILDER_BOT:
            self.run_bot(c)
            
        # Best practice: if you add more computation later, always
        # have a sanity check on c.get_cpu_time_elapsed() to exit 
        # before you breach the 2000μs (2ms) limit and get terminated!

    def run_core(self, c: Controller):
        """The Core acts as the centralized Master Brain."""
        if self.my_core_pos is None:
            self.my_core_pos = c.get_position()
            
        current_round = c.get_current_round()
        
        # 1. READ INTEL FROM BOTS
        # Core has a massive vision radius (r² = 36). It can see bots dropping markers
        # when they return into its vision radius.
        for entity_id in c.get_nearby_entities():
            if c.get_entity_type(entity_id) == EntityType.MARKER:
                if c.get_team(entity_id) == c.get_team():
                    val = c.get_marker_value(entity_id)
                    msg_type, poi_type, x, y, timestamp = self.decode_marker(val)
                    
                    # Listen to our bots reporting back.
                    if msg_type == TYPE_INTEL:
                        if poi_type == POI_TITANIUM:
                            self.known_titanium.add((x, y))
                        elif poi_type == POI_AXIONITE:
                            self.known_axionite.add((x, y))

        # 2. WRITE DIRECTIVES TO NEWLY SPAWNED BOTS
        # If we know of titanium, tell our bots to mine it!
        if self.known_titanium and c.get_action_cooldown() == 0:
            target_x, target_y = list(self.known_titanium)[0] # Just grab the first one
            directive_val = self.encode_marker(TYPE_DIRECTIVE, POI_TITANIUM, target_x, target_y, current_round)
            
            # Place it around our core space so new bots spawn on/near it
            if c.can_place_marker(self.my_core_pos):
                c.place_marker(self.my_core_pos, directive_val)
                
        # 3. SPAWN BOTS
        if self.num_spawned < 3 and c.get_action_cooldown() == 0:
            for d in DIRECTIONS:
                spawn_pos = self.my_core_pos.add(d)
                if c.can_spawn(spawn_pos):
                    c.spawn_builder(spawn_pos)
                    self.num_spawned += 1
                    break
                    
    def run_bot(self, c: Controller):
        """The Worker Bot logic: explore, report, harvest."""
        my_pos = c.get_position()
        current_round = c.get_current_round()
        
        # 1. READ NEARBY TILES AND UPDATE OUR INTERNAL MAP
        for tile in c.get_nearby_tiles():
            env = c.get_tile_env(tile)
            idx = tile.y * self.map_w + tile.x
            
            if env == Environment.ORE_TITANIUM:
                self.map_env[idx] = 3
                if (tile.x, tile.y) not in self.known_titanium:
                    self.known_titanium.add((tile.x, tile.y))
                    
                    # If we found NEW Titanium, we drop a marker (Intel) for the Core.
                    # As a simplistic approach for the template, we just drop it right away. 
                    # Advanced logic would have the bot walk back to the Core's vision first.
                    intel_val = self.encode_marker(TYPE_INTEL, POI_TITANIUM, tile.x, tile.y, current_round)
                    if c.can_place_marker(my_pos):
                        c.place_marker(my_pos, intel_val)
                        
            elif env == Environment.ORE_AXIONITE:
                self.map_env[idx] = 4
            elif env == Environment.WALL:
                self.map_env[idx] = 2
            elif env == Environment.EMPTY:
                self.map_env[idx] = 1
                
        # 2. READ DIRECTIVES FROM CORE
        # Check an immediately close radius to see if the core gave us a mission.
        for entity_id in c.get_nearby_entities(dist_sq=2):
            if c.get_entity_type(entity_id) == EntityType.MARKER:
                if c.get_team(entity_id) == c.get_team():
                    val = c.get_marker_value(entity_id)
                    msg_type, poi_type, x, y, timestamp = self.decode_marker(val)
                    
                    # Accept new valid directive missions
                    if msg_type == TYPE_DIRECTIVE:
                        self.current_directive = (x, y)
                        c.draw_indicator_line(my_pos, Position(x, y), 255, 0, 0)
        
        # 3. MOVE (Pathing)
        if c.get_move_cooldown() == 0:
            if self.current_directive:
                dir_to_target = my_pos.direction_to(Position(self.current_directive[0], self.current_directive[1]))
            else:
                # Excel Iterative Heat Diffusion (9x9 Local Grid)
                grid_in = {}
                grid_out = {}
                
                # Record our trail
                my_tuple = (my_pos.x, my_pos.y)
                self.path_history.add(my_tuple)
                
                # 1. Build initial 9x9 input grid from vision bounds (+/- 4)
                for dx in range(-4, 5):
                    for dy in range(-4, 5):
                        # Restrict to strictly visual bounds (r^2 <= 20)
                        if dx*dx + dy*dy > 20: continue
                        
                        gx = my_pos.x + dx
                        gy = my_pos.y + dy
                        
                        heat = 0.0
                        if gx < 0 or gx >= self.map_w or gy < 0 or gy >= self.map_h:
                            heat = 9.0  # Map Bounds act as walls
                        else:
                            idx = gy * self.map_w + gx
                            env_val = self.map_env[idx]
                            
                            if env_val == 2: # Wall
                                heat = 9.0
                            elif env_val == 3 or env_val == 4: # Resource (Attraction)
                                pos = Position(gx, gy)
                                b_id = c.get_tile_building_id(pos) if c.is_in_vision(pos) else None
                                heat = -5.0 if b_id is None else 2.0
                            elif (gx, gy) in self.path_history:
                                heat = 9.0
                                
                        grid_in[(dx, dy)] = heat
                        grid_out[(dx, dy)] = heat
                
                # 2. Run Nate's formula 3 times (Iterative Calculation)
                for _ in range(3):
                    new_out = {}
                    for (dx, dy), in_heat in grid_in.items():
                        neighbor_sum = 0.0
                        for ndx in (-1, 0, 1):
                            for ndy in (-1, 0, 1):
                                if ndx == 0 and ndy == 0: continue
                                neighbor_sum += grid_out.get((dx+ndx, dy+ndy), 0.0)
                        
                        # Your exact cell input formula!
                        new_out[(dx, dy)] = in_heat * 0.8 + neighbor_sum * 0.1
                    grid_out = new_out
                    
                # 3. Choose the adjacent tile with the lowest diffused heat
                lowest_heat = float('inf')
                dir_to_target = None
                
                for d in DIRECTIONS:
                    dx, dy = d.delta()
                    gx = my_pos.x + dx
                    gy = my_pos.y + dy
                    
                    if gx < 0 or gx >= self.map_w or gy < 0 or gy >= self.map_h:
                        continue
                    if self.map_env[gy * self.map_w + gx] == 2: # Wall
                        continue
                        
                    heat = grid_out.get((dx, dy), 999.0)
                    if heat < lowest_heat:
                        lowest_heat = heat
                        dir_to_target = d
                        
                if dir_to_target is None:
                    dir_to_target = random.choice(DIRECTIONS)
                
            move_pos = my_pos.add(dir_to_target)
            
            # Auto-build roads to make it passable (need to fix to not build on resources)
            if c.can_build_road(move_pos):
                c.build_road(move_pos)
                
            if c.can_move(dir_to_target):
                c.move(dir_to_target)

        # 4. ACTIONS (Harvesting)
        if c.get_action_cooldown() == 0:
            for d in DIRECTIONS:
                check_pos = my_pos.add(d)
                if c.can_build_harvester(check_pos):
                    c.build_harvester(check_pos)
                    
                    # If we reached our goal, clear the directive
                    if self.current_directive == (check_pos.x, check_pos.y):
                        self.current_directive = None
                    break
