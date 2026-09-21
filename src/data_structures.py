##### GROUP A - Queue operations (user-defined data structure) #####
class Queue:
	"""Simple FIFO queue used for the breadth-first search in get_reachable_tiles."""
	def __init__(self):
		self.items = []

	# adds an item to the back of the queue
	def enqueue(self, item):
		self.items.append(item)

	# removes and returns the item at the front of the queue
	def dequeue(self):
		return self.items.pop(0)

	# true when there is nothing left to process
	def is_empty(self):
		return len(self.items) == 0


##### GROUP A - Priority queue implemented as a binary heap (tree structure) #####
class PriorityQueue:
	"""Priority queue for the A* search in find_path - dequeue returns the lowest-priority item.
	Stored as a binary heap in a list: the item at index i has children at 2i+1 and 2i+2,
	and every parent's priority is <= both of its children, so the lowest sits at the root."""
	def __init__(self):
		self.items = [] 

	# adds the item at the end, then sifts it up past any parent with a higher priority
	def enqueue(self, item, priority):
		self.items.append((priority, item))
		i = len(self.items) - 1
		while i > 0:
			parent = (i - 1) // 2
			if self.items[i][0] >= self.items[parent][0]:
				break
			self.items[i], self.items[parent] = self.items[parent], self.items[i]
			i = parent

	# takes the lowest-priority item off the root, moves the last item into its place,
	# then sifts that one down past whichever child is smaller until the heap is in order
	def dequeue(self):
		last = self.items.pop()
		if not self.items:
			return last[1]
		priority, item = self.items[0]
		self.items[0] = last
		i = 0
		while True:
			left, right, smallest = 2 * i + 1, 2 * i + 2, i
			if left < len(self.items) and self.items[left][0] < self.items[smallest][0]:
				smallest = left
			if right < len(self.items) and self.items[right][0] < self.items[smallest][0]:
				smallest = right
			if smallest == i:
				break
			self.items[i], self.items[smallest] = self.items[smallest], self.items[i]
			i = smallest
		return item

	# true when the heap is empty
	def is_empty(self):
		return len(self.items) == 0
