Overview
Resources
Titanium, axionite, and the cost scaling formula.
​
Titanium

Titanium
The primary resource used to construct most buildings. Each team starts with 1000 titanium.
Titanium is harvested from titanium ore deposits and delivered to the core via conveyors.
​
Axionite

Axionite comes in two forms:
Raw axionite
Raw axionite
Mined from axionite ore deposits. When fed to a turret or core, it is destroyed. You must refine it first for advanced uses.
Refined axionite
Refined axionite
Produced by axionite foundries from raw axionite + titanium. Used for powerful units and advanced infrastructure.
Whenever “axionite” is mentioned in the spec without qualification, it refers to refined axionite.
​
Resource distribution

Resources are stored and moved in stacks of 10. At the end of each round, buildings that output resources send them to adjacent buildings that accept them.
Resources can be outputted to buildings belonging to the opposing team.
See conveyors, harvester & foundry, and turrets for details on input/output directions.
​
Cost scaling

Every building and unit you construct increases the cost of future builds. The cost of every building and unit is:
cost
=
⌊
scale
×
base cost
⌋
cost=⌊scale×base cost⌋
Where scale starts at 1.0 and increases additively with each entity built — two gunners at +10% each give 1.2x, not 1.21x. You can query the current scale with c.get_scale_percent() which returns it as a percentage (100.0 at base).
Entity	Scale increase
Road	+0.5%
Conveyor, splitter, armoured conveyor, barrier	+1%
Bridge	+5%
Harvester, gunner, breach, launcher	+10%
Builder bot, sentinel	+20%
Axionite foundry	+100%
When an entity is destroyed, its scaling contribution is removed — costs go back down.
Every entity you build makes the next one more expensive. Be efficient with what you build!
Previous
Core
Your central building — if it's destroyed, you lose.
Next