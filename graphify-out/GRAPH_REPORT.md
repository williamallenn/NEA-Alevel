# Graph Report - coding  (2026-09-15)

## Corpus Check
- Corpus is ~9,862 words - fits in a single context window. You may not need a graph.

## Summary
- 201 nodes · 303 edges · 19 communities (11 shown, 8 thin omitted)
- Extraction: 91% EXTRACTED · 8% INFERRED · 1% AMBIGUOUS · INFERRED: 23 edges (avg confidence: 0.82)
- Token cost: 658,503 input · 0 output

## Community Hubs (Navigation)
- Game Loop & Menus
- Core Modules & Environment Sprites
- Enemy System
- Camera, Input & Zombie Sprite
- Database & Score Persistence
- Upgrade Effects
- Player Character
- Buttons & Sprite Loading
- Decorations & Weapon Icon
- Floor Tileset Assets
- Admin Menu & Text Buttons
- Pathfinding Queue
- Bullet & Projectile Damage
- Upgrade Card UI
- Project Docs & Level Maps
- Settings Screen
- Exit Button Asset
- Grass Tileset Asset
- Yuki Pet Sprite

## God Nodes (most connected - your core abstractions)
1. `Game` - 35 edges
2. `Player` - 17 edges
3. `Enemy` - 17 edges
4. `Database` - 16 edges
5. `create_upgrade_pool()` - 13 edges
6. `TextButton` - 11 edges
7. `Bullet` - 9 edges
8. `UpgradeCard` - 8 edges
9. `Queue` - 7 edges
10. `SpriteSheet` - 7 edges

## Surprising Connections (you probably didn't know these)
- `Player Sprite Sheet` --shares_data_with--> `Player`  [INFERRED]
  images/player.png → src/sprites.py
- `Zombie Icon (Pixel Art Sprite)` --conceptually_related_to--> `Zombie`  [INFERRED]
  images/zombie.png → src/sprites.py
- `Zombie Sprite Sheet` --shares_data_with--> `Zombie`  [EXTRACTED]
  images/zombie-sheet.png → src/sprites.py
- `Map 1 Level Layout` --conceptually_related_to--> `2D Zombie Horde Shooter`  [INFERRED]
  src/Maps/Map1.txt → README.md
- `Map 2 Level Layout` --conceptually_related_to--> `2D Zombie Horde Shooter`  [INFERRED]
  src/Maps/Map2.txt → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **NEA Zombie Shooter Level Maps** — readme_nea_project, src_maps_map1_layout, src_maps_map2_layout [INFERRED 0.85]

## Communities (19 total, 8 thin omitted)

### Community 1 - "Core Modules & Environment Sprites"
Cohesion: 0.11
Nodes (18): Cat/Fox Orange Enemy Sprite, Enemy/Character Sprite Row (goblin, flame, mummy, cat, markers), Flame/Fire Enemy Sprite, Goblin-like Green Enemy Sprite, Bandaged/Mummy Enemy Sprite, Player Spawn Marker Tile (blue tile labeled 'P'), Unlabeled Red Marker Tile, Play Button UI Asset (+10 more)

### Community 2 - "Enemy System"
Cohesion: 0.12
Nodes (9): Boss, Brute, Enemy, Base enemy. Subclasses set the class attributes below and may override…, Default appearance: a flat-coloured placeholder rect. Overridden by subclasses…, Fast, low-health enemy type that unlocks from round 3., Slow, tanky enemy type that unlocks from round 3., Boss, spawns on every 5th round (+1 more)

### Community 3 - "Camera, Input & Zombie Sprite"
Cohesion: 0.12
Nodes (8): Zombie Sprite Sheet, Zombie Icon (Pixel Art Sprite), CameraGroup, InputBox, Sprite group that draws everything offset around a target (the player), so the…, Standard enemy with a real animated sprite sheet, spawns from round 1., A clickable text field that becomes active on click and accepts typed input…, Zombie

### Community 4 - "Database & Score Persistence"
Cohesion: 0.15
Nodes (4): Database, SQLite-backed storage for user accounts and leaderboard scores., main(), print_table()

### Community 5 - "Upgrade Effects"
Cohesion: 0.25
Nodes (12): apply_adrenaline_rush(), apply_explosive_rounds(), apply_glass_cannon(), apply_iron_skin(), apply_overclock(), apply_piercing_rounds(), apply_second_wind(), apply_twin_shot() (+4 more)

### Community 6 - "Player Character"
Cohesion: 0.19
Nodes (3): Player Sprite Sheet, Player, The player character: movement, shooting, taking damage and colliding with the…

### Community 7 - "Buttons & Sprite Loading"
Cohesion: 0.17
Nodes (4): Button, A clickable image-based button with a slightly enlarged hover state., Wraps a loaded spritesheet image so individual frames can be cut out of it., SpriteSheet

### Community 8 - "Decorations & Weapon Icon"
Cohesion: 0.25
Nodes (4): Decoration, Visual weapon icon that orbits the player, always facing the mouse cursor., A purely visual ground decoration, cut out from the sheet with a soft edge so…, WeaponSprite

### Community 9 - "Floor Tileset Assets"
Cohesion: 0.29
Nodes (7): Floor.png (Tileset & Sprite Sheet), Desert/Sand Floor Tileset (orange variant), Grass/Dirt Floor Tileset with pool tiles, Snow/Ice Floor Tileset (white variant), Stairs/Ladder Tile Set (dark green), Water/Pool Decorative Tiles (blue, two color themes), Wood Plank Floor Tileset

### Community 10 - "Admin Menu & Text Buttons"
Cohesion: 0.33
Nodes (3): build_row_buttons(), A clickable rectangular button drawn from text rather than an image., TextButton

### Community 14 - "Project Docs & Level Maps"
Cohesion: 0.67
Nodes (4): NEA Project, 2D Zombie Horde Shooter, Map 1 Level Layout, Map 2 Level Layout

## Ambiguous Edges - Review These
- `settings.py` → `Desert/Sand Floor Tileset (orange variant)`  [AMBIGUOUS]
  images/Floor.png · relation: conceptually_related_to
- `settings.py` → `Stairs/Ladder Tile Set (dark green)`  [AMBIGUOUS]
  images/Floor.png · relation: conceptually_related_to
- `settings.py` → `Weapon Icons Sprite (Pistol, Blade, Rifle)`  [AMBIGUOUS]
  images/weapon.png · relation: conceptually_related_to
- `sprites.py` → `Play Button UI Asset`  [AMBIGUOUS]
  images/Play_Button.png · relation: conceptually_related_to

## Knowledge Gaps
- **17 isolated node(s):** `NEA Project`, `Exit Button (UI Asset)`, `Grass/Dirt Floor Tileset with pool tiles`, `Snow/Ice Floor Tileset (white variant)`, `Wood Plank Floor Tileset` (+12 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 76 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `settings.py` and `Desert/Sand Floor Tileset (orange variant)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `settings.py` and `Stairs/Ladder Tile Set (dark green)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `settings.py` and `Weapon Icons Sprite (Pistol, Blade, Rifle)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `sprites.py` and `Play Button UI Asset`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Game` connect `Game Loop & Menus` to `Core Modules & Environment Sprites`, `Camera, Input & Zombie Sprite`, `Database & Score Persistence`, `Buttons & Sprite Loading`, `Admin Menu & Text Buttons`, `Pathfinding Queue`?**
  _High betweenness centrality (0.233) - this node is a cross-community bridge._
- **Why does `Player` connect `Player Character` to `Game Loop & Menus`, `Core Modules & Environment Sprites`, `Enemy System`, `Camera, Input & Zombie Sprite`?**
  _High betweenness centrality (0.139) - this node is a cross-community bridge._
- **Why does `Database` connect `Database & Score Persistence` to `Game Loop & Menus`, `Core Modules & Environment Sprites`, `Buttons & Sprite Loading`?**
  _High betweenness centrality (0.117) - this node is a cross-community bridge._