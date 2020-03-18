class MinesweeperFunctions:
	_STATUS_CODE = {
		'COVERED': '-',
		'FLAGGED': '#',
		'OPENED': '?',
	}

	_CONTENT_CODE = {
		'BOMB': '!',
		'0': ' ',
		'1': 1,
		'2': 2,
		'3': 3,
		'4': 4,
		'5': 5,
		'6': 6,
		'7': 7,
		'8': 8,
	}

	_CODES = {}
	_CODES.update(_STATUS_CODE)
	_CODES.update(_CONTENT_CODE)

	__MODE = None

	def __init__(self, mode):
		if mode != 'status_on' and mode != 'status_off':
			raise Exception('Must use the modes \'status_on\' or \'status_off\'')
		self.__MODE = mode

	def _filterCells(self, board, cells, code, status_on=None):
		if code not in self._CODES:
			return self._filterOtherCells(board, cells)

		if self.__MODE == 'status_off':
			return [n for n in cells if board[n[0]][n[1]] == self._CODES[code]]
		else:
			if status_on is None:
				raise Exception('Must call filter cells with status_on value set if in status_on mode')
			elif status_on:
				return [n for n in cells 
					if board[n[0]][n[1]]['STATUS'] == self._STATUS_CODE[code]]
			else:
				return [n for n in cells 
					if board[n[0]][n[1]]['CONTENT'] == self._CONTENT_CODE[code]]

	def _filterOtherCells(self, board, cells):
		notOpened = []
		notOpened.extend(self._filterCells(board, cells, 'COVERED'))
		notOpened.extend(self._filterCells(board, cells, 'FLAGGED'))
		notOpened.extend(self._filterCells(board, cells, 'OPENED'))
		return [n for n in cells if n not in notOpened]

	def _getAllNeighbors(self, board, cell):
		# These ranges specify a square around the given cell, 
		# so nine coordinates will be added to the list
		x = cell[0]
		y = cell[1]
		coordinates = [(x + i, y + j)
			for i in range(-1,2)
			for j in range(-1,2)]

		# If the cell is at the top, bottom, left, or right sides
		# of the board, then set the coordinates past the side 
		# to None and later remove them from the return value
		if x == 0:
			coordinates[0] = None
			coordinates[1] = None
			coordinates[2] = None
		if x == len(board) - 1:
			coordinates[6] = None
			coordinates[7] = None
			coordinates[8] = None
		if y == 0:
			coordinates[0] = None
			coordinates[3] = None
			coordinates[6] = None
		if y == len(board[0]) - 1:
			coordinates[2] = None
			coordinates[5] = None
			coordinates[8] = None

		# Set coordinates for the given cell to None
		coordinates[4] = None
		
		return [c for c in coordinates if c is not None]

	def _getNeighbors(self, board, cell, code=None):
		neighbors = self._getAllNeighbors(board, cell)

		if code is None:
			return neighbors
		else:
			return self._filterCells(board, neighbors, code)

	def _countAllCells(self, board, code):
		all_cells = [(x, y)
			for x in range(len(board))
			for y in range(len(board[x]))]
		return len(self._filterCells(board, all_cells, code))

	def _countNeighbors(self, board, cell, code, status_on=None):
		neighbors = self._getAllNeighbors(board, cell)
		return len(self._filterCells(board, neighbors, code, status_on=status_on))
