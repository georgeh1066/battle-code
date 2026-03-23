import json
import os
import sys

from cambc import Controller, Direction, EntityType, Environment, Position

# Non-centre directions
DIRECTIONS = [d for d in Direction if d != Direction.CENTRE]
CORE_OFFSETS = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]

# ==== MARKER PROTOCOL ====
MSG_TYPE_MASK = 0b1111
PAYLOAD_MASK = 0b11 << 4
X_COORD_MASK = 0b111111 << 6
Y_COORD_MASK = 0b111111 << 12

MSG_ORE_FOUND = 1
MSG_CORE_POS = 2

def encode_marker(msg_type, payload, x, y):
    val = msg_type & MSG_TYPE_MASK
    val |= (payload << 4) & PAYLOAD_MASK
    val |= (x << 6) & X_COORD_MASK
    val |= (y << 12) & Y_COORD_MASK
    return val

def decode_marker(val):
    msg_type = val & MSG_TYPE_MASK
    payload = (val & PAYLOAD_MASK) >> 4
    x = (val & X_COORD_MASK) >> 6
    y = (val & Y_COORD_MASK) >> 12
    return msg_type, payload, x, y

# Load weights globally
WEIGHTS_FILE = os.path.join(os.path.dirname(__file__), "weights.json")
try:
    with open(WEIGHTS_FILE, "r") as f:
        WEIGHTS = json.load(f)
except FileNotFoundError:
    print(f"Warning: could not find {WEIGHTS_FILE}, using defaults", file=sys.stderr)
    WEIGHTS = {
        "spawn_ore_weight": 30.0,
        "spawn_proximity_weight": 20.0,
        "spawn_congestion_penalty": -6.0,
        "builder_early_game_cap": 4,
        "builder_mid_game_cap": 6,
        "reserve_titanium": 30,
        "ore_repulsion_weight": 5.0
    }

def nearest_dist(pos, ore_set):
    if not ore_set:
        return 999
    return min(max(abs(pos.x - x), abs(pos.y - y)) for (x, y) in ore_set)

class Player:
    def __init__(self):
        self.task = "explore"
        self.known_ti = set()
        self.known_ax = set()
        self.core_pos = None

    def run(self, c: Controller) -> None:
        try:
            self._run_internal(c)
        except Exception as e:
            import traceback
            traceback.print_exc(file=sys.stderr)
    
    def _run_internal(self, c: Controller) -> None:
        etype = c.get_entity_type()
            
        # Update known ore (every unit sweeps vision and markers)
        self.update_environment(c)

        if etype == EntityType.CORE:
            self.core_pos = c.get_position()
            self.run_core(c)
        elif etype == EntityType.BUILDER_BOT:
            self.run_builder(c)

        # Evaluator checkpoint: on the final round, report score to stderr
        if c.get_current_round() >= 1999 and etype == EntityType.CORE:
            ti, ax = c.get_global_resources()
            scale = c.get_scale_percent()
            builder_count = sum(1 for uid in c.get_nearby_units(900) if c.get_entity_type(uid) == EntityType.BUILDER_BOT and c.get_team(uid) == c.get_team())
            fitness = (ax * 3) + ti + (builder_count * 10)
            print(f"FITNESS|{c.get_team()}|{fitness}|TI:{ti}|AX:{ax}", file=sys.stderr)
    
    def update_environment(self, c: Controller):
        my_pos = c.get_position()
        
        # Read markers first
        for eid in c.get_nearby_entities():
            if c.get_entity_type(eid) == EntityType.MARKER and c.get_team(eid) == c.get_team():
                val = c.get_marker_value(eid)
                msg_type, payload, x, y = decode_marker(val)
            if msg_type == MSG_ORE_FOUND:
                if payload == 0: self.known_ti.add((x, y))
                elif payload == 1: self.known_ax.add((x, y))
            elif msg_type == MSG_CORE_POS:
                self.core_pos = Position(x, y)

        # Broadcast core pos
        if c.get_entity_type() == EntityType.CORE:
            val = encode_marker(MSG_CORE_POS, 0, my_pos.x, my_pos.y)
            if c.can_place_marker(my_pos, val): c.place_marker(my_pos, val)

        for p in c.get_nearby_tiles():
            env = c.get_tile_env(p)
            if env == Environment.ORE_TITANIUM:
                self.known_ti.add((p.x, p.y))
                val = encode_marker(MSG_ORE_FOUND, 0, p.x, p.y)
                if c.can_place_marker(p, val): c.place_marker(p, val)
            elif env == Environment.ORE_AXIONITE:
                self.known_ax.add((p.x, p.y))
                val = encode_marker(MSG_ORE_FOUND, 1, p.x, p.y)
                if c.can_place_marker(p, val): c.place_marker(p, val)

    def run_core(self, c: Controller):
        # Count allied builders currently alive by querying the Controller itself
        builder_count = sum(1 for uid in c.get_nearby_units(900) if c.get_entity_type(uid) == EntityType.BUILDER_BOT and c.get_team(uid) == c.get_team())
                
        if self.should_spawn_builder(c, builder_count):
            candidates = self.choose_spawn_tile(c)
            if candidates:
                c.spawn_builder(candidates[0][1])

    def should_spawn_builder(self, c: Controller, builder_count: int) -> bool:
        if c.get_action_cooldown() != 0: return False
        
        ti, ax = c.get_global_resources()
        cost_ti, cost_ax = c.get_builder_bot_cost()
        reserve_ti = WEIGHTS.get("reserve_titanium", 30)
        
        if ti < cost_ti + reserve_ti or ax < cost_ax: return False

        scale = c.get_scale_percent()
        early_cap = WEIGHTS.get("builder_early_game_cap", 4)
        mid_cap = WEIGHTS.get("builder_mid_game_cap", 6)
        
        target_cap = early_cap if c.get_current_round() < 300 else mid_cap
        
        if scale > 180 and builder_count >= target_cap: return False
        return builder_count < target_cap + 2

    def choose_spawn_tile(self, c: Controller):
        core = c.get_position()
        candidates = []
        for dx, dy in CORE_OFFSETS:
            p = Position(core.x + dx, core.y + dy)
            if c.can_spawn(p):
                score = 0.0
                adj_ore = 0
                for d in DIRECTIONS:
                    q = p.add(d)
                    if c.is_in_vision(q):
                        env = c.get_tile_env(q)
                        if env in (Environment.ORE_TITANIUM, Environment.ORE_AXIONITE):
                            adj_ore += 1
                score += WEIGHTS.get("spawn_ore_weight", 30.0) * adj_ore

                d_ti = nearest_dist(p, self.known_ti)
                score += WEIGHTS.get("spawn_proximity_weight", 20.0) / (1.0 + d_ti)                                                                             
                
                cong = sum(1 for d in DIRECTIONS if c.is_in_vision(p.add(d)) and c.get_tile_builder_bot_id(p.add(d)) is not None and c.get_team(c.get_tile_builder_bot_id(p.add(d))) == c.get_team())
                score += WEIGHTS.get("spawn_congestion_penalty", -6.0) * cong

                candidates.append((score, p))

        if not candidates: return None
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates

    def run_builder(self, c: Controller):
        import random
        my_pos = c.get_position()
        
        if self.task == "route" and self.core_pos:
            if max(abs(my_pos.x - self.core_pos.x), abs(my_pos.y - self.core_pos.y)) <= 2:
                self.task = "explore"

        if self.task == "explore":
            for d in DIRECTIONS:
                check_pos = my_pos.add(d)
                if c.can_build_harvester(check_pos):
                    c.build_harvester(check_pos)
                    self.task = "route" 
                    return

        if self.task == "route" and self.core_pos:
            best_dir = my_pos.direction_to(self.core_pos)
            if best_dir != Direction.CENTRE:
                if c.can_build_conveyor(my_pos, best_dir):
                    c.build_conveyor(my_pos, best_dir)
                self._move_smart(c, my_pos, best_dir)
                return

        if self.task == "explore":
            target_ore = None
            best_score = 99999.0
            
            all_ore = list(self.known_ti.union(self.known_ax))
            repulsion_weight = WEIGHTS.get("ore_repulsion_weight", 5.0)
            
            for ox, oy in all_ore:
                dist = max(abs(my_pos.x - ox), abs(my_pos.y - oy))
                
                congestion = 0
                for uid in c.get_nearby_units(36):
                    if c.get_entity_type(uid) == EntityType.BUILDER_BOT:
                        bpos = c.get_unit_position(uid)
                        d_other = max(abs(bpos.x - ox), abs(bpos.y - oy))
                        if d_other < 8: congestion += 1
                            
                score = dist + (repulsion_weight * congestion)
                
                if score < best_score:
                    best_score = score
                    target_ore = (ox, oy)
                    
            if target_ore:
                best_dir = my_pos.direction_to(Position(target_ore[0], target_ore[1]))
                self._move_smart(c, my_pos, best_dir)
            else:
                self._move_smart(c, my_pos, random.choice(DIRECTIONS))

    def _move_smart(self, c: Controller, my_pos: Position, ideal_dir: Direction):
        if ideal_dir == Direction.CENTRE: return
            
        target_pos = my_pos.add(ideal_dir)
        scored_dirs = []
        for d in DIRECTIONS:
            p = my_pos.add(d)
            dist = max(abs(p.x - target_pos.x), abs(p.y - target_pos.y))
            scored_dirs.append((dist, d, p))
            
        scored_dirs.sort(key=lambda x: x[0])
        
        for dist, d, p in scored_dirs:
            if c.can_move(d):
                c.move(d)
                return
            if c.can_build_road(p):
                c.build_road(p)
                if c.can_move(d): c.move(d)
                return
