class Queue:
	"""Simple FIFO queue used for the breadth-first search in get_reachable_tiles."""
	def __init__(self):
		self.items = []

	def enqueue(self, item):
		self.items.append(item)

	def dequeue(self):
		return self.items.pop(0)

	def is_empty(self):
		return len(self.items) == 0


class PriorityQueue:
	"""Priority queue for the A* search in find_path - dequeue returns the lowest-priority item."""
	def __init__(self):
		self.items = []  # list of (priority, item) pairs

	def enqueue(self, item, priority):
		self.items.append((priority, item))

	# linear scan for the lowest-priority entry - O(n), fine at this map size
	def dequeue(self):
		best_index = 0
		for i in range(1, len(self.items)):
			if self.items[i][0] < self.items[best_index][0]:
				best_index = i
		priority, item = self.items.pop(best_index)
		return item

	def is_empty(self):
		return len(self.items) == 0
