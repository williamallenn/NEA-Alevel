from data_structures import Queue, PriorityQueue


##### GROUP A - Graph traversal (breadth-first search over the tile graph) #####
# breadth-first search from the spawn tile to find every tile the player can reach
def get_reachable_tiles(valid_tiles, start):
	valid_set = set(valid_tiles)
	visited = {start}
	queue = Queue()
	queue.enqueue(start)
	while not queue.is_empty():
		x, y = queue.dequeue()
		for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
			neighbour = (x + dx, y + dy)
			if neighbour in valid_set and neighbour not in visited:
				visited.add(neighbour)
				queue.enqueue(neighbour)
	return visited


# A* search from start to goal. Each tile's priority is f = g (steps so far) + h (Manhattan
# distance to goal), so the priority queue always expands the most promising tile first.
# came_from records each tile's parent, which is walked back from the goal to build the path.
# Returns the tiles to walk (excluding start), or None if unreachable
##### GROUP A - Complex user-defined algorithm (A* pathfinding) #####
def find_path(start, goal, blocked_tiles, width, height):
	if start == goal:
		return []
	open_queue = PriorityQueue()
	open_queue.enqueue(start, 0)
	came_from = {}
	g_score = {start: 0}
	visited = set()
	while not open_queue.is_empty():
		current = open_queue.dequeue()
		if current == goal:
			path = []
			while current != start:
				path.append(current)
				current = came_from[current]
			path.reverse()
			return path
		if current in visited:
			continue
		visited.add(current)
		cx, cy = current
		for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
			neighbour = (cx + dx, cy + dy)
			nx, ny = neighbour
			if not (0 <= nx < width and 0 <= ny < height):
				continue
			if neighbour in blocked_tiles:
				continue
			tentative_g = g_score[current] + 1
			if tentative_g < g_score.get(neighbour, float("inf")):
				g_score[neighbour] = tentative_g
				came_from[neighbour] = current
				f_score = tentative_g + abs(nx - goal[0]) + abs(ny - goal[1])
				open_queue.enqueue(neighbour, f_score)
	return None
