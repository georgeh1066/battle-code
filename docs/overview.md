Overview
Game Overview
Objective, map, units, buildings, and win conditions for Cambridge Battlecode.
​
Background

The year is 2076. A crystalline ore called axionite — a room-temperature superconductor — has been discovered on Titan, Saturn’s largest moon. At least six corporations have deployed autonomous extraction fleets to Titan’s surface.
Titan is lethal to humans: −179°C, a nitrogen-methane atmosphere, and a 76-minute communication delay to Earth. All operations are carried out by robots.
You write the software that controls your fleet: mining ore, refining axionite, and outcompeting the enemy.
​
Objective

Collect resources and destroy the enemy’s core.
To do this, you must find ore deposits, build harvesters, deliver resources back to the core using conveyors, and expand your territory.
​
Win conditions

If both cores are still alive after 2000 rounds, the winner is decided by tiebreakers in order:
1
Axionite delivered

Total refined axionite delivered to the core
2
Titanium delivered

Total titanium delivered to the core
3
Harvesters alive

Number of harvesters currently alive
4
Axionite stored

Total axionite currently stored
5
Titanium stored

Total titanium currently stored
6
Coinflip

Random tiebreaker
​
Map

The map is a rectangular grid between 20×20 and 50×50 inclusive. The top-left (northwest) corner is position (0, 0).
The map is guaranteed to be symmetric by either reflection or rotation.
Each grid cell is one of:
Cell type	Tile	Description
Empty		Can build anything
Wall		Impassable, cannot build
Titanium ore		Harvesters mine titanium
Axionite ore		Harvesters mine raw axionite
Walls prevent building anything on the tile they occupy. Ores are tiles on which harvesters may be built to mine resources.
​
Units

Units are game entities which run an independent instance of the code that you submit. The core, builder bots, and turrets are units. Harvesters are not units — they operate automatically.
Each round, units take their turns in the order they were spawned. After all units have taken their turn, resources are distributed. See the reference tables for a quick comparison of all entity stats.
​
Vision and action radius

Units have a vision radius and an action radius.
The vision radius is the area in which the unit can sense its environment.
The action radius is the area in which the unit can perform actions, such as building, placing markers, or destroying buildings.
All units have an action radius of √2 (r² = 2), except the core, which has an action radius of √8 (r² = 8) measured from its centre.
Turrets also have an attack range which is different from their action radius — see each turret’s page for details.
Unit	Vision r²	Action r²
Core	36	8 (from centre)
Builder bot	20	2
Gunner	13	2
Sentinel	32	2
Breach	10	2
Launcher	26	2
​
Cooldowns

All units have action and move cooldowns which are non-negative integers that decrease by 1 at the end of each round. Actions and movement can only be performed when the respective cooldown is 0.
The move cooldown is only used by the builder bot — it is the only mobile unit.
​
Markers

All units may place one marker per round on a tile within action radius. This is separate from the action cooldown. You can overwrite an existing friendly marker, but not an enemy marker.
​
Self-destruct

All units may self-destruct at any time. Builder bots deal 20 damage to the tile they are standing on upon self-destruct.
​
Buildings

Buildings are game entities which are immovable. All entities are buildings except builder bots.
In particular, the core and turrets are considered both a unit and a building.
​
Entity IDs

All entities (buildings and units) in the game have a unique integer ID. All Controller methods that deal with entities accept and return these IDs. Properties of an entity can be queried with getter functions — for example, c.get_hp(id).
# Get all nearby entities and check their type
for entity_id in c.get_nearby_entities():
    if c.get_entity_type(entity_id) == EntityType.HARVESTER:
        pos = c.get_position(entity_id)
The ID-based API was chosen for performance — constructing Python objects for every entity query would be too slow within the 2ms time limit.
​
Computation limit

Each unit gets 2ms of CPU time per round. If your code exceeds this, execution is interrupted and run() is called fresh on the next round — your bot does not resume where it left off.
To absorb variance, each unit has an extra time buffer equal to 5% of the time limit. If a round takes longer than 2ms, the overage is deducted from the buffer. If a round takes less than 2ms, the savings are refunded to the buffer (capped at 5%).
Once a unit exhausts both its 2ms budget and its buffer in a single round, it is interrupted immediately.
Each bot process has a 1 GB memory limit. Exceeding this will terminate the process.
The local runner (cambc run) does not enforce time limits. Use cambc test-run to test on the same AWS Graviton3 hardware that runs ladder matches.
​
Debugging

stdout (print()) is captured by the engine and saved to the replay. You can view each unit’s output in the visualiser.
stderr prints to the console in real time — use this for debugging during local runs.
c.draw_indicator_line(pos_a, pos_b, r, g, b) and c.draw_indicator_dot(pos, r, g, b) draw debug overlays on the map, saved to the replay.