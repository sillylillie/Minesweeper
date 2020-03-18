import copy
from functionality import MinesweeperFunctions

class RecursiveAlgorithm(MinesweeperFunctions):
	def __init__(self):
		super().__init__('status_off')

	def __checkFulfillment(self, board, bombs, influencedCells, modifiedCells):
		toOpen = []
		toFlag = []

		# TODO --- IMPROVE ALGORITHM
		# if bombs is zero, open everything covered on the whole board

		# Check for negative base case
		if bombs < 0:
			return False

		for i in influencedCells:
			neighbors = self._getNeighbors(board, i)
			nbsFlagged = self._filterCells(board, neighbors, 'FLAGGED')
			nbsCovered = self._filterCells(board, neighbors, 'COVERED')
			nbsOpened = self._filterCells(board, neighbors, 'OPENED')

			value = board[i[0]][i[1]]
			value = int(value) if type(value) == type(0) else 0

			# Too many flags around a cell
			if len(nbsFlagged) > value:
				return False
			# Completely fulfilled; open remaining neighbors
			elif len(nbsFlagged) == value:
				toOpen.extend(nbsCovered)
			else:
				# Not yet fulfilled; keep going
				if len(nbsFlagged) + len(nbsCovered) > value:
					pass
				# Too many opened around a cell
				elif len(nbsFlagged) + len(nbsCovered) < value:
					return False
				# Will be fulfilled; flag remaining neighbors
				else:
					toFlag.extend(nbsCovered)

		return [toOpen, toFlag]


	def __recursiveSolution(self, board, bombs, influencedCells, modifiedCells):
		# Is this board still possible to fulfill?
		check = self.__checkFulfillment(board, bombs, influencedCells, modifiedCells)

		# Failed the check for fulfillment (negative base case)
		if not check:
			return False

		# If check is not false, it will contain one list of toOpen and one list of toFlag
		toOpen = list(set(check[0]))
		toFlag = list(set(check[1]))

		# Check for positive base case
		if len(toOpen) == 0 and len(toFlag) == 0:
			toReturn = []
			toReturn.append([c for c in modifiedCells if board[c[0]][c[1]] == self._CODES['OPENED']])
			toReturn.append([c for c in modifiedCells if board[c[0]][c[1]] == self._CODES['FLAGGED']])

			"""
			# - - - <- this should be opened
			# 3 2 -
			3 4 3 -
			# # # 2

			However, this would cause a crazy amount of recursion in the general case
			Instead, we will simply allow the general case algorithm to run its course 
			until it gets stuck, then switch to probability-based solution
			"""

			return toReturn

		# Failed a check for sanity: the same cell should not be marked toOpen and toFlag
		if len([e for e in toOpen if e in toFlag]) > 0:
			return False

		"""
		BEYOND THE POINT OF NO RETURN (prepare to recurse)
		
		We need a new list of modified cells, and an updated test board
		We also need to add new influenced cells based on the neighbors of the recently added modified cells
		"""

		nbsOfToOpen = []
		for c in toOpen:
			board[c[0]][c[1]] = self._CODES['OPENED']
			nbsOfToOpen.extend(self._getNeighbors(board, c, code='REALLY_OPENED'))
		modifiedCells.extend(toOpen)
		influencedCells.extend(nbsOfToOpen)

		nbsOfToFlag = []
		for c in toFlag:
			board[c[0]][c[1]] = self._CODES['FLAGGED']
			nbsOfToFlag.extend(self._getNeighbors(board, c, code='REALLY_OPENED'))
			bombs = bombs - 1
		modifiedCells.extend(toFlag)
		influencedCells.extend(nbsOfToFlag)

		modifiedCells = list(set(modifiedCells))
		influencedCells = list(set(influencedCells))

		return self.__recursiveSolution(board, bombs, influencedCells, modifiedCells)

	def canIFlagThis(self, board, bombs, cell):
		testBoard = copy.deepcopy(board)
		testBoard[cell[0]][cell[1]] = self._CODES['FLAGGED']
		modifiedCells = [cell]

		influencedCells = self._getNeighbors(board, cell, code='REALLY_OPENED')

		return self.__recursiveSolution(testBoard, bombs - 1, influencedCells, modifiedCells)

	def canIOpenThis(self, board, bombs, cell):
		testBoard = copy.deepcopy(board)
		testBoard[cell[0]][cell[1]] = self._CODES['OPENED']
		modifiedCells = [cell]

		influencedCells = self._getNeighbors(board, cell, code='REALLY_OPENED')

		return self.__recursiveSolution(testBoard, bombs, influencedCells, modifiedCells)

