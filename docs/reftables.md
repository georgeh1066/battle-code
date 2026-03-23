Reference
Reference Tables
Quick-reference stat tables for all entities.
​
Entity stats

Entity	HP	Cost	Scale	Notes
Core	500	—	—	3×3; spawns builders
Builder bot	30	50 Ti	20%	Mobile; build, heal, attack, destroy
Conveyor	20	3 Ti	1%	3 inputs, 1 output
Splitter	20	6 Ti	1%	1 input, 3 rotating outputs
Bridge	20	20 Ti	5%	Output to tile within dist 3
Armoured conv.	50	10 Ti, 5 Ax	1%	Conveyor with more HP
Harvester	30	80 Ti	10%	Outputs every 4 rounds
Foundry	50	120 Ti	100%	Ti + raw Ax → refined Ax
Road	10	1 Ti	0.5%	Walkable
Barrier	30	3 Ti	1%	Blocks space
Marker	1	Free	—	No action cooldown
Gunner	40	10 Ti	10%	Closest tile in facing dir; markers do not shield
Sentinel	30	15 Ti	20%	Line ±1; refined Ax stuns +2 cd
Breach	60	30 Ti, 10 Ax	10%	180° cone; friendly fire
Launcher	30	20 Ti	10%	Throws adjacent builders
​
Unit combat stats

Unit	Vision r²	Action r²	Attack r²	Damage	Reload	Ammo/shot
Core	36	8	—	—	—	—
Builder bot	20	2	0 (own tile)	2	—	2 Ti
Gunner	13	2	13	10 (+10 with Ax)	1	2
Sentinel	32	2	32	10	2	5
Breach	13	2	5	40 + 20 splash	1	5
Launcher	26	2 (pickup)	26 (throw)	—	1	—
​
Game constants

Constant	Value
Max rounds	2000
Unit cap per team	50 living units (including the core)
Stack size	10
Starting titanium	1000
Starting axionite	0
Builder bot heal	4 HP for 1 Ti to all friendly entities on the tile
Builder bot attack	2 damage for 2 Ti (own tile only)
Builder bot self-destruct damage	0
Harvester output interval	Every 4 rounds
Sentinel stun (refined axionite ammo)	+2 action and move cooldown
CPU time per unit per round	2ms (+5% buffer)
Memory limit per bot	1 GB
​
Cost scaling

Every entity you build increases the cost multiplier. Scale starts at 1.0x (100%). Increases are additive — two gunners at +10% each give 1.2x, not 1.21x.
Entity	Scale increase
Road	+0.5%
Conveyor, splitter, armoured conveyor, barrier	+1%
Bridge	+5%
Harvester, gunner, breach, launcher	+10%
Builder bot, sentinel	+20%
Axionite foundry	+100%
cost
=
⌊
scale
×
base cost
⌋
cost=⌊scale×base cost⌋