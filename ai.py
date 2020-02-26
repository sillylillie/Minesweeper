"""
Basic usage:
`python3`
`from ai import *`
`from game import *`
`solver = Solver(options={'PRINT_MODE': 'NOTHING'})`
`mygame = start_game(silent=True, options={'DISPLAY_ON_MOVE': False, 'PRINT_GUIDES': True}, level='EXPERT', specs={})`
`solver.solve(mygame).consoleDisplayVisible()`
"""

import copy
import time
from game import *

"""
Public members:

RESULT_CODE
__init__(options=None)
getData()
solve(game)
"""
class Solver:
	__PRINT_CODE = {
		'DOTS': 0,
		'BOARD': 1,
		'NOTHING': 2,
	}

	RESULT_CODE = {
		'N/A': 0,
		'WIN': 1,
		'LOSS': 2,
		'GIVE_UP': 3,
	}

	__STATE_CODE = {
		'INITIALIZED': 0,
		'NORMAL': 1,
		'WARNING': 2,
		'CRITICAL': 3,
		'GUESS': 4,
		'DONE': 5,
	}

	__CODES = Game.CELL_CODE
	__PRINT_MODE = __PRINT_CODE['DOTS']
	__DELAY = 0
	__AI_STATE = __STATE_CODE['INITIALIZED']
	__GUESS = False

	# TODO 
	# ADD TO DATA COLLECTION IN SAMPLE
	# 'GAME_SEED': 0,
	# 'START_SEED': 0,
	# 'START_POSITION': [0, 0], # Location of the first click

	__DATA_START = {
		'GAME': {
			'RESULT': RESULT_CODE['N/A'], 
			'CELL_COUNT': {
				'HEIGHT': 0,
				'WIDTH': 0,
				'TOTAL': 0, # height x width
				'BOMBS': 0, # total bombs (not bombs left)
				'BOMBS_AT_EDGES': 0, 
				'NUMERICAL': [], # 0s, 1s, 2s, ..., and 8s
			},
			'OPENING': [], # For each element, store the size of the opening (a cluster of empty cells)
		},
		'LOOP': [], # example below; the first entry will be the state of the game before the first loop
# 		'LOOP': [
# 			{
# 				'BOMBS_LEFT': 0,
# 				'TIME_ELAPSED': 0,
# 				'NUMBER_OPENED': 0,
# 				'NUMBER_FLAGGED': 0,
# 				'STILL_COVERED': 0,
# 			}, 
# 		],

	}

	__DATA = copy.deepcopy(__DATA_START)

	def __init__(self, options=None):
		if options is not None:
			if 'PRINT_MODE' in options:
				self.__PRINT_MODE = self.__PRINT_CODE[options['PRINT_MODE']]
			if 'DELAY' in options:
				self.__DELAY = options['DELAY']
			if 'GUESS' in options:
				self.__GUESS = options['GUESS']

	def getData(self):
		return self.__DATA

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
			return self.__filterCells(board, neighbors, code)

	def __filterCells(self, board, cells, code):
		if code not in self.__CODES:
			return self.__filterCellsOther(board, cells)

		return [n for n in cells if board[n[0]][n[1]] == self.__CODES[code]]

	def __filterCellsOther(self, board, cells):
		notOpened = []
		notOpened.extend(self.__filterCells(board, cells, 'COVERED'))
		notOpened.extend(self.__filterCells(board, cells, 'FLAGGED'))
		notOpened.extend(self.__filterCells(board, cells, 'OPENED'))
		return [n for n in cells if n not in notOpened]

	def __checkFulfillment(self, board, bombs, influencedCells, modifiedCells):
		toOpen = []
		toFlag = []

		# Check for negative base case
		if bombs < 0:
			return False

		for i in influencedCells:
			neighbors = self.__getNeighbors(board, i[0], i[1])
			nbsFlagged = self.__filterCells(board, neighbors, 'FLAGGED')
			nbsCovered = self.__filterCells(board, neighbors, 'COVERED')
			nbsOpened = self.__filterCells(board, neighbors, 'OPENED')

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


	def __tryToFulfill(self, board, bombs, influencedCells, modifiedCells):
		check = self.__checkFulfillment(board, bombs, influencedCells, modifiedCells)

		# toOpen = []
		# toFlag = []

		# # Check for negative base case
		# if bombs < 0:
		# 	return False

		# for i in influencedCells:
		# 	neighbors = self.__getNeighbors(board, i[0], i[1])
		# 	nbsFlagged = self.__filterCells(board, neighbors, 'FLAGGED')
		# 	nbsCovered = self.__filterCells(board, neighbors, 'COVERED')
		# 	nbsOpened = self.__filterCells(board, neighbors, 'OPENED')

		# 	value = board[i[0]][i[1]]
		# 	value = int(value) if type(value) == type(0) else 0

		# 	if len(nbsFlagged) > value:
		# 		return False
		# 	elif len(nbsFlagged) == value:
		# 		toOpen.extend(nbsCovered)
		# 	else:
		# 		if len(nbsFlagged) + len(nbsCovered) > value:
		# 			pass
		# 		elif len(nbsFlagged) + len(nbsCovered) < value:
		# 			return False
		# 		else:
		# 			toFlag.extend(nbsCovered)

		# Failed the check for fulfillment
		if not check:
			return False

		# If check is not false, it will contain one list of toOpen and one list of toFlag
		toOpen = list(set(check[0]))
		toFlag = list(set(check[1]))

		# TODO --- IMPROVE ALGORITHM
		# if bombs is zero, open everything covered on the whole board

		# Check for positive base case
		if len(toOpen) == 0 and len(toFlag) == 0:
			toReturn = []
			toReturn.append([c for c in modifiedCells if board[c[0]][c[1]] == self.__CODES['OPENED']])
			toReturn.append([c for c in modifiedCells if board[c[0]][c[1]] == self.__CODES['FLAGGED']])

			# TODO --- IMPROVE ALGORITHM
			# Implement option to continue the recursion by asking canIFlag/OpenThis on neighboring covered cells
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
			bombs = bombs - 1
		modifiedCells.extend(toFlag)
		influencedCells.extend(nbsOfToFlag)

		modifiedCells = list(set(modifiedCells))
		influencedCells = list(set(influencedCells))

		return self.__tryToFulfill(board, bombs, influencedCells, modifiedCells)

	def __canIFlagThis(self, board, bombs, coordinates):
		testBoard = copy.deepcopy(board)
		testBoard[coordinates[0]][coordinates[1]] = self.__CODES['FLAGGED']
		modifiedCells = [coordinates]

		influencedCells = self.__getNeighbors(board, coordinates[0], coordinates[1], code='REALLY_OPENED')

		return self.__tryToFulfill(testBoard, bombs - 1, influencedCells, modifiedCells)

	def __canIOpenThis(self, board, bombs, coordinates):
		testBoard = copy.deepcopy(board)
		testBoard[coordinates[0]][coordinates[1]] = self.__CODES['OPENED']
		modifiedCells = [coordinates]

		influencedCells = self.__getNeighbors(board, coordinates[0], coordinates[1], code='REALLY_OPENED')

		return self.__tryToFulfill(testBoard, bombs, influencedCells, modifiedCells)

	def __count(self, board, code):
		cells = []
		for x in range(len(board)):
			for y in range(len(board[x])):
				cells.append((x,y))
		return len(self.__filterCells(board, cells, code))

	def __updateDataLoop(self, index, turn, flagged=None, opened=None):
		self.__DATA['LOOP'].append({})
		self.__DATA['LOOP'][index]['BOMBS_LEFT'] = turn['BOMBS']
		self.__DATA['LOOP'][index]['TIME_ELAPSED'] = '{0:.2f}'.format(turn['TIME'])
		self.__DATA['LOOP'][index]['NUMBER_FLAGGED'] = 0 if flagged is None else flagged
		self.__DATA['LOOP'][index]['NUMBER_OPENED'] = 0 if opened is None else opened
		all_cells = []
		for x in range(len(turn['BOARD'])):
			all_cells.extend([(x, y) for y in range(len(turn['BOARD'][x]))])
		self.__DATA['LOOP'][index]['STILL_COVERED'] = len(self.__filterCells(turn['BOARD'], all_cells, code='COVERED'))

	def solve(self, game):
		# Information to keep track within the loops
		self.__AI_STATE = self.__STATE_CODE['NORMAL']
		self.__DATA = copy.deepcopy(self.__DATA_START)
		loop_count = 0
		previousTurn = game.getGameVisible()
		thisTurn = game.getGameVisible()

		# Set up data collection
		self.__DATA['GAME']['RESULT'] = self.RESULT_CODE['N/A']
		self.__DATA['GAME']['CELL_COUNT']['HEIGHT'] = game.getBoardHeight()
		self.__DATA['GAME']['CELL_COUNT']['WIDTH'] = game.getBoardWidth()
		self.__DATA['GAME']['CELL_COUNT']['TOTAL'] = game.getBoardHeight() * game.getBoardWidth()
		self.__DATA['GAME']['CELL_COUNT']['BOMBS'] = game.getTotalBombs()
		self.__updateDataLoop(loop_count, thisTurn)

		if self.__PRINT_MODE != self.__PRINT_CODE['NOTHING']:
			print('\nVisible: ')
			game.consoleDisplayVisible()
			print('')
			print('')
			print('STARTING RECURSIVE ALGORITHM')

		while(self.__AI_STATE != self.__STATE_CODE['DONE']):
			loop_count = loop_count + 1
			time.sleep(self.__DELAY)

			currentBoard = thisTurn['BOARD']

			toOpen = []
			toFlag = []

			if self.__AI_STATE == self.__STATE_CODE['NORMAL']:
				# Candidates for modification are any covered cells neighboring opened cells
				candidates = []
				for x in range(len(currentBoard)):
					for y in range(len(currentBoard[x])):
						if currentBoard[x][y] == self.__CODES['COVERED'] and len(self.__getNeighbors(currentBoard, x, y, code='REALLY_OPENED')) > 0 :
							candidates.append((x, y))

				for c in candidates:
					# For efficiency, check that the candidate has not been solved yet
					if c not in toOpen and c not in toFlag:
						# If this move would conflict with game logic, canFlag is False
						# If it is possible to do this move, canFlag contains two lists:
						# canFlag[0] is a list of cells that would be opened according to game logic
						# canFlag[1] is a list of cells that would be flagged according to game logic
						canFlag = self.__canIFlagThis(currentBoard, thisTurn['BOMBS'], c)
						canOpen = self.__canIOpenThis(currentBoard, thisTurn['BOMBS'], c)

						if canFlag and canOpen:
							# Should open/flag any neighbors that BOTH tests suggested opening/flagging
							toOpen.extend([o for o in canFlag[0] if o in canOpen[0]])
							toFlag.extend([o for o in canFlag[1] if o in canOpen[1]])

						if not canFlag:
							# Must open the candidate and open/flag neighbors suggested in the correct test
							toOpen.extend(canOpen[0])
							toFlag.extend(canOpen[1])

						if not canOpen:
							# Must flag the candidate and open/flag neighbors suggested in the correct test
							toOpen.extend(canFlag[0])
							toFlag.extend(canFlag[1])

			if self.__AI_STATE == self.__STATE_CODE['GUESS'] and self.__GUESS == True:
				all_cells = []
				for x in range(len(thisTurn['BOARD'])):
					all_cells.extend([(x, y) for y in range(len(thisTurn['BOARD'][x]))])
				covered_cells = self.__filterCells(thisTurn['BOARD'], all_cells, 'COVERED')

				toOpen.append(covered_cells[random.randrange(len(covered_cells))])


			toOpen = list(set(toOpen))
			toFlag = list(set(toFlag))

			countOpened = 0
			countFlagged = 0

			for c in toOpen:
				result = game.open(c[0], c[1])
				if result == True:
					self.__AI_STATE = self.__STATE_CODE['DONE']
					self.__DATA['GAME']['RESULT'] = self.RESULT_CODE['WIN']
				elif result == False:
					self.__AI_STATE = self.__STATE_CODE['DONE']
					self.__DATA['GAME']['RESULT'] = self.RESULT_CODE['LOSS']
				countOpened = countOpened + 1

				if self.__AI_STATE == self.__STATE_CODE['DONE']:
					break
			if self.__AI_STATE != self.__STATE_CODE['DONE']:
				for c in toFlag:
					game.flag(c[0], c[1])
					countFlagged = countFlagged + 1

			previousTurn = copy.deepcopy(thisTurn)
			thisTurn = game.getGameVisible()
			"""
			'INITIALIZED': 0,
			'NORMAL': 1,
			'WARNING': 2,
			'CRITICAL': 3,
			'GUESS': 4,
			'DONE': 5,
			"""
			if previousTurn['BOARD'] == thisTurn['BOARD']:
				if self.__AI_STATE == self.__STATE_CODE['NORMAL']:
					self.__AI_STATE = self.__STATE_CODE['WARNING']
				elif self.__AI_STATE == self.__STATE_CODE['WARNING']:
					self.__AI_STATE = self.__STATE_CODE['CRITICAL']
				elif self.__AI_STATE == self.__STATE_CODE['CRITICAL']:
					self.__AI_STATE = self.__STATE_CODE['GUESS']
				elif self.__AI_STATE == self.__STATE_CODE['GUESS']:
					self.__AI_STATE = self.__STATE_CODE['DONE']
					self.__DATA['GAME']['RESULT'] = self.RESULT_CODE['GIVE_UP']
			elif self.__AI_STATE != self.__STATE_CODE['NORMAL'] and self.__AI_STATE != self.__STATE_CODE['DONE']:
				self.__AI_STATE = self.__STATE_CODE['NORMAL']

			# We want an update for every loop, including the last in case of giving up
			self.__updateDataLoop(loop_count, thisTurn, flagged=countFlagged, opened=countOpened)

			# Print to console on every loop
			if self.__PRINT_MODE == self.__PRINT_CODE['DOTS']:
				print('.')
			elif self.__PRINT_MODE == self.__PRINT_CODE['BOARD']:
				game.consoleDisplayVisible()

		# Finish up solve function and return
		if self.__PRINT_MODE != self.__PRINT_CODE['NOTHING']:
			print('')
			if self.__PRINT_MODE == self.__PRINT_CODE['DOTS']:
				game.consoleDisplayVisible()
			print('DONE')

		# Finish up data collection
		solution = game.getGameSolution()

		# Count of each kind of cell content except bomb (0, 1, 2, etc.)
		for i in range(9):
			self.__DATA['GAME']['CELL_COUNT']['NUMERICAL'].append(self.__count(solution['BOARD'], str(i)))

		# Count of bombs on the edge of the board (predicted more likely to end in giving up due to guessing)
		edgesBoard = copy.deepcopy(solution['BOARD'])
		for i in range(1, len(edgesBoard) - 1):
			edgesBoard[i] = [edgesBoard[i][0], edgesBoard[i][len(edgesBoard[0]) - 1]]
		self.__DATA['GAME']['CELL_COUNT']['BOMBS_AT_EDGES'] = self.__count(edgesBoard, 'BOMB')

		return game

if __name__=='__main__':
	print('Nothing to do here')