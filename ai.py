import copy, time
from game import *
# start_game(silent=False, startSeed=None, startPosition=None, options=None, level='BEGINNER', specs={})
# new_game(silent=False, options=None, level='BEGINNER', specs={})
# Game


# Public members:
# 
# __init__(options=None)
# solve(game)

class AI:
	__PRINT_CODE = {
		'DOTS': 0,
		'BOARD': 1,
		'NOTHING': 2,
	}

	__CODES = Game.CELL_CODE
	__PRINT_MODE = __PRINT_CODE['DOTS']

	def __init__(self, options=None):
		if options is not None:
			if 'PRINT_MODE' in options:
				self.__PRINT_MODE = self.__PRINT_CODE[options['PRINT_MODE']]

	def __getAllNeighbors(self, board, x, y):
		coordinates = []
		# These ranges specify a square around the given cell, 
		# so nine coordinates will be added to the list
		for i in range(-1,2):
			for j in range(-1,2):
				coordinates.append((x + i, y + j))

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

	def __getNeighbors(self, board, x, y, code=None):
		neighbors = self.__getAllNeighbors(board, x, y)

		if code is None:
			return neighbors
		else:
			return self.__filterNeighbors(board, neighbors, code)

	def __filterNeighbors(self, board, neighbors, code):
		if code not in self.__CODES:
			return self.__filterNeighborsOther(board, neighbors)

		return [n for n in neighbors if board[n[0]][n[1]] == self.__CODES[code]]

	def __filterNeighborsOther(self, board, neighbors):
		notOpened = []
		notOpened.extend(self.__filterNeighbors(board, neighbors, 'COVERED'))
		notOpened.extend(self.__filterNeighbors(board, neighbors, 'FLAGGED'))
		notOpened.extend(self.__filterNeighbors(board, neighbors, 'OPENED'))
		return [n for n in neighbors if n not in notOpened]

	def __tryToFulfill(self, board, influencedCells, modifiedCells):
		toOpen = []
		toFlag = []

		# Check for negative base case
		# 
		# TODO implement checking based on the number of bombs left
		# Dependency: requires info about the number of bombs left to be passed and 
		# maintained within this function
		for i in influencedCells:
			neighbors = self.__getNeighbors(board, i[0], i[1])
			nbsFlagged = self.__filterNeighbors(board, neighbors, 'FLAGGED')
			nbsCovered = self.__filterNeighbors(board, neighbors, 'COVERED')
			nbsOpened = self.__filterNeighbors(board, neighbors, 'OPENED')

			value = board[i[0]][i[1]]
			value = int(value) if type(value) == type(0) else 0

			if len(nbsFlagged) > value:
				return False
			elif len(nbsFlagged) == value:
				toOpen.extend(nbsCovered)
			else:
				if len(nbsFlagged) + len(nbsCovered) > value:
					pass
				elif len(nbsFlagged) + len(nbsCovered) < value:
					return False
				else:
					toFlag.extend(nbsCovered)

		toOpen = list(set(toOpen))
		toFlag = list(set(toFlag))

		if len(toOpen) == 0 and len(toFlag) == 0:
			# TODO implement option to continue the recursion by asking canIFlag/OpenThis on neighboring covered cells
			# 
			# # - - - <- this should be opened
			# # 3 2 -
			# 3 4 3 -
			# # # # 2
			# 
			# because there are TWO potential flags required, the algorithm won't detect this
			# it only tries to adjust one thing at a time and then base all other things off of 
			# that one modification
			# this situation would call for two potential modifications at the same time
			# 
			# Q: should the further canIFlag/canIOpen only apply to unmodified covered neighbors cells of the influenced cells?
			# Q: should this call be only allowed to go one call deep or can it repeat itself?
			# Q: if recursive/repeating, what is the base case? when there are no covered neighbors of the influeced cells left?? 

			# Reminder that the code 'OPENED' refers only to cells that were opened using the test board
			# Anything that was opened on the real board will have a code ' ', 1, 2, etc.
			toReturn = []
			toReturn.append([c for c in modifiedCells if board[c[0]][c[1]] == self.__CODES['OPENED']])
			toReturn.append([c for c in modifiedCells if board[c[0]][c[1]] == self.__CODES['FLAGGED']])

			return toReturn

		if len([e for e in toOpen if e in toFlag]) > 0:
			# The intersection containing coordinates of cells would indicate something went
			# wrong and one cell is being asked to open as well as flag
			return False

		# BEYOND THE POINT OF NO RETURN
		# (prepare to recurse)
		# We need a new list of modified cells, and an updated test board
		# We also need to add new influenced cells based on the neighbors of the recently added modified cells

		nbsOfToOpen = []
		for c in toOpen:
			board[c[0]][c[1]] = self.__CODES['OPENED']
			nbsOfToOpen.extend(self.__getNeighbors(board, c[0], c[1], code='REALLY_OPENED'))
		modifiedCells.extend(toOpen)
		influencedCells.extend(nbsOfToOpen)

		nbsOfToFlag = []
		for c in toFlag:
			board[c[0]][c[1]] = self.__CODES['FLAGGED']
			nbsOfToFlag.extend(self.__getNeighbors(board, c[0], c[1], code='REALLY_OPENED'))
		modifiedCells.extend(toFlag)
		influencedCells.extend(nbsOfToFlag)

		modifiedCells = list(set(modifiedCells))
		influencedCells = list(set(influencedCells))

		return self.__tryToFulfill(board, influencedCells, modifiedCells)

	def __canIFlagThis(self, board, coordinates):
		testBoard = copy.deepcopy(board)
		testBoard[coordinates[0]][coordinates[1]] = self.__CODES['FLAGGED']
		modifiedCells = [coordinates]

		# TODO considering the possibility of calling this again from the recursive call, 
		# should we be using the code 'REALLY_OPENED' here?
		influencedCells = self.__getNeighbors(board, coordinates[0], coordinates[1], code='REALLY_OPENED')

		return self.__tryToFulfill(testBoard, influencedCells, modifiedCells)

	def __canIOpenThis(self, board, coordinates):
		testBoard = copy.deepcopy(board)
		testBoard[coordinates[0]][coordinates[1]] = self.__CODES['OPENED']
		modifiedCells = [coordinates]

		influencedCells = self.__getNeighbors(board, coordinates[0], coordinates[1], code='REALLY_OPENED')

		return self.__tryToFulfill(testBoard, influencedCells, modifiedCells)

	def solve(self, game):

		if self.__PRINT_MODE != self.__PRINT_CODE['NOTHING']:
			print('\nVisible: ')
			game.consoleDisplayVisible()
			print('')
			print('')
			print('STARTING RECURSIVE ALGORITHM')

		done = False
		previousBoard = game.exportGameVisible()
		currentBoard = game.exportGameVisible()

		while(not done):
			time.sleep(0)

			candidates = []
			for x in range(len(currentBoard)):
				for y in range(len(currentBoard[x])):
					if currentBoard[x][y] == self.__CODES['COVERED'] and len(self.__getNeighbors(currentBoard, x, y, code='REALLY_OPENED')) > 0 :
						candidates.append((x, y))

			toOpen = []
			toFlag = []

			for c in candidates:
				canFlag = self.__canIFlagThis(currentBoard, c)
				canOpen = self.__canIOpenThis(currentBoard, c)

				if canFlag and canOpen:
					# must open/flag any neighbors that BOTH tests suggested opening/flagging
					toOpen.extend([o for o in canFlag[0] if o in canOpen[0]])
					toFlag.extend([o for o in canFlag[1] if o in canOpen[1]])

				if not canFlag:
					# must open the candidate and open/flag neighbors suggested in the correct test
					toOpen.extend(canOpen[0])
					toFlag.extend(canOpen[1])

				if not canOpen:
					# must flag the candidate and open/flag neighbors suggested in the correct test
					toOpen.extend(canFlag[0])
					toFlag.extend(canFlag[1])

			toOpen = list(set(toOpen))
			toFlag = list(set(toFlag))

			for c in toOpen:
				if game.open(c[0], c[1]):
					done = True
					break;
			if not done:
				for c in toFlag:
					if game.flag(c[0], c[1]):
						done = True
						break;

			previousBoard = copy.deepcopy(currentBoard)
			currentBoard = game.exportGameVisible()
			if previousBoard == currentBoard:
				done = True

			if self.__PRINT_MODE == self.__PRINT_CODE['DOTS']:
				print('.')
			elif self.__PRINT_MODE == self.__PRINT_CODE['BOARD']:
				game.consoleDisplayVisible()

		if self.__PRINT_MODE != self.__PRINT_CODE['NOTHING']:
			print('')
			if self.__PRINT_MODE == self.__PRINT_CODE['DOTS']:
				game.consoleDisplayVisible()
			print('DONE')

		return game

if __name__=='__main__':
	# TODO write a testing suite to run this over a long period to get data
	# I want this testing suite to iterate over all possible starting locations of each board
	# It should generate a percentage of how likely you are to get a playable board with no guessing
	# Ideal boards can be completed 100% of the time with no guessing
	# There might be a range from 1% to 99%
	# I expect many in the 0% to 1% range: board which have one guessing spot that can 
	# be fixed only when the user starts exactly there
	# 
	# Dependency: makes little sense before the data gathering listed below is implemented

	solver = AI(options={'PRINT_MODE': 'NOTHING'})
	# Favorite one so far: startSeed=76964, seed=69365
	mygame = start_game(silent=True, options={'DISPLAY_ON_MOVE': False, 'PRINT_GUIDES': True}, level='EXPERT', specs={})

	# TODO get solver to keep track of data, such as: 
	# Number opened and flagged per loop
	# Number of bombs left after every loop
	# Number of covered cells left after every loop
	# Number of loops
	# Time required for each loop
	# Result (win, loss, draw)

	# Note: modifies my own copy of mygame
	solver.solve(mygame)

	mygame.consoleDisplayVisible()
	