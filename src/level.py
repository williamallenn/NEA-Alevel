import random
import pathfinding
from sprites import Ground, Block, Decoration
from settings import TILE_SIZE, TILE_LEGEND, MAP_STAMPS, DECORATION_SPRITES, WATER_DECORATION_CHANCE, LAND_DECORATION_CHANCE


class Level:
	"""A map loaded from a text file: its tile sprites, which tiles are walkable or blocked, and pathfinding across them."""
	# builds the level's tiles, stamps and decorations, then works out which tiles the player can reach
	def __init__(self, game, map_path):
		self.valid_tiles = []
		self.blocked_tiles = set()
		grid = self.load_level(map_path)
		self.add_tiles(game, grid)
		stamped_tiles = self.add_stamps(game, map_path)
		self.add_decorations(game, grid, stamped_tiles)

		self.height = len(grid)
		self.width = max((len(row) for row in grid), default=0)
		self.spawn = (self.width // 2, self.height // 2)
		self.reachable_tiles = pathfinding.get_reachable_tiles(self.valid_tiles, self.spawn)
		unreachable = set(self.valid_tiles) - self.reachable_tiles
		if unreachable:
			print(f"Warning: {len(unreachable)} unreachable tile(s) in {map_path}: {sorted(unreachable)}")

	# reads a level file into a list of row strings
	def load_level(self, path):
		try:
			with open(path, "r") as f:
				return [line.rstrip("\n") for line in f]
		except FileNotFoundError:
			print(f"Level file not found: ({path})")
			return []

	# checks if the tile at (x, y) is water, treating out-of-bounds as not water
	def is_water_tile(self, grid, x, y):
		if 0 <= y < len(grid) and 0 <= x < len(grid[y]):
			return grid[y][x] == "W"
		return False

	# picks the water edge/corner sprite based on which neighbouring tiles are land
	def get_water_variant(self, grid, x, y):
		up = self.is_water_tile(grid, x, y - 1)
		down = self.is_water_tile(grid, x, y + 1)
		left = self.is_water_tile(grid, x - 1, y)
		right = self.is_water_tile(grid, x + 1, y)

		if not up and not left:
			return "water_top_left"
		if not up and not right:
			return "water_top_right"
		if not down and not left:
			return "water_bottom_left"
		if not down and not right:
			return "water_bottom_right"
		if not up:
			return "water_top"
		if not down:
			return "water_bottom"
		if not left:
			return "water_left"
		if not right:
			return "water_right"

		# all four sides are water, so check diagonals for an inner corner
		if not self.is_water_tile(grid, x + 1, y - 1):
			return "water_inner_top_right"
		if not self.is_water_tile(grid, x - 1, y - 1):
			return "water_inner_top_left"
		if not self.is_water_tile(grid, x + 1, y + 1):
			return "water_inner_bottom_right"
		if not self.is_water_tile(grid, x - 1, y + 1):
			return "water_inner_bottom_left"
		return "water"

	# creates a ground sprite for every tile, plus a block for walls, and records walkable/blocked tiles
	def add_tiles(self, game, grid):
		for i, row in enumerate(grid):
			for j, tile in enumerate(row):
				info = TILE_LEGEND.get(tile)
				if info and info.get("ground") == "water":
					ground_key = self.get_water_variant(grid, j, i)
				elif info and "ground" in info:
					ground_key = info["ground"]
				else:
					ground_key = "ground"
				Ground(game, j, i, ground_key)
				if info and info.get("blocking"):
					Block(game, j, i)
					self.blocked_tiles.add((j, i))
				if tile == ".":
					self.valid_tiles.append((j, i))

	# draws this map's fixed multi-tile features over the ground and returns the tiles they cover
	def add_stamps(self, game, map_path):
		stamped_tiles = set()
		for stamp in MAP_STAMPS.get(map_path, []):
			dx0, dy0 = stamp["pos"]
			sx0, sy0 = stamp["sheet_pos"]
			tiles_wide, tiles_high = stamp["size"]
			for ty in range(tiles_high):
				for tx in range(tiles_wide):
					Ground(game, dx0 + tx, dy0 + ty, (sx0 + tx * TILE_SIZE, sy0 + ty * TILE_SIZE))
					stamped_tiles.add((dx0 + tx, dy0 + ty))
		return stamped_tiles

	# randomly scatters decorations on water and land tiles; blocking ones (rocks) become unwalkable
	def add_decorations(self, game, grid, stamped_tiles):
		water_decorations = [key for key, info in DECORATION_SPRITES.items() if info["terrain"] == "water"]
		land_decorations = [key for key, info in DECORATION_SPRITES.items() if info["terrain"] == "land"]
		for i, row in enumerate(grid):
			for j, tile in enumerate(row):
				if (j, i) in stamped_tiles:
					continue
				is_interior_water = (
					tile == "W"
					and self.is_water_tile(grid, j, i - 1)
					and self.is_water_tile(grid, j, i + 1)
					and self.is_water_tile(grid, j - 1, i)
					and self.is_water_tile(grid, j + 1, i)
				)
				if is_interior_water and random.random() < WATER_DECORATION_CHANCE:
					Decoration(game, j, i, random.choice(water_decorations))
				elif tile == "." and random.random() < LAND_DECORATION_CHANCE:
					deco_key = random.choice(land_decorations)
					Decoration(game, j, i, deco_key)
					if DECORATION_SPRITES[deco_key].get("blocking"):
						self.blocked_tiles.add((j, i))
						self.valid_tiles.remove((j, i))

	# A* route between two tiles on this level
	def find_path(self, start, goal):
		return pathfinding.find_path(start, goal, self.blocked_tiles, self.width, self.height)
