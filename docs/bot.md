Units
Builder Bot
The only mobile unit — responsible for constructing all buildings.
Builder bot
Builder bots are the only mobile unit. They construct buildings, repair friendly entities on a tile, and can make a weak attack against the building under them.
​
Properties

Property	Value
HP	30
Base cost	50 Ti
Scaling contribution	20%
Vision radius²	20
Action radius²	2
Builder bot range — blue is vision, red is action radius
​
Movement

Builder bots can move to an adjacent tile (including diagonals) if their move cooldown is 0. Moving increases the cooldown by 1.
Builder bots can only walk on:
Conveyors (any variant, any direction, either team)
Roads (either team)
The allied core
These are called walkable tiles. The direction of the conveyor does not matter, and neither does the presence of resources on the tile.
# Move towards a target
direction = c.get_position().direction_to(target)
if c.can_move(direction):
    c.move(direction)
​
Actions

When action cooldown is 0, a builder bot can perform one of:
​
Build

Build any building or turret on a tile within action radius that doesn’t already have a building.
Only walkable buildings (conveyors and roads) can be built on a tile that contains a builder bot.
​
Heal

Spend 1 Ti to heal 4 HP to all friendly entities on a tile within action radius. If a friendly builder bot and a friendly building share that tile, both are healed. The action fails if nothing on the tile would gain HP.
if c.can_heal(target_pos):
    c.heal(target_pos)
​
Attack

Spend 2 Ti to deal 2 damage to the building on the tile the builder bot is standing on. This reuses the standard can_fire() / fire() combat API.
my_pos = c.get_position()
if c.can_fire(my_pos):
    c.fire(my_pos)
​
Destroy

Destroy any allied building within action radius. This can be done any number of times per round and does not cost action cooldown.
if c.can_destroy(building_pos):
    c.destroy(building_pos)
​
Self-destruct

A builder bot can self-destruct at any time. It does not deal damage.
c.self_destruct()
​
Markers

Builder bots (like all units) can place one marker per round within action radius, separate from the action cooldown.