"""
Basic usage:
`python3`
`from ai import *`
`from game import *`
`solver = Solver(options={'PRINT_MODE': 'NOTHING'})`
`mygame = start_game(silent=True, options={'DISPLAY_ON_MOVE': False, 'PRINT_GUIDES': True}, level='EXPERT', specs={})`
`solver.solve(mygame).consoleDisplayVisible()`
"""

from functionality import MinesweeperFunctions
import copy
import time
from game import *
import linalg

"""
Public members:

RESULT_CODE
__init__(options=None)
getData()
solve(game)
"""
class Solver(MinesweeperFunctions):
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

	__PRINT_MODE = __PRINT_CODE['DOTS']
	__DELAY = 0
	__AI_STATE = __STATE_CODE['INITIALIZED']
	__GUESS = False

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
		'LOOP': [], 
	}
	"""
	example below; the first entry will be the state of the game before the first loop
	'LOOP': [
		{
			'BOMBS_LEFT': 0,
			'TIME_ELAPSED': 0,
			'NUMBER_OPENED': 0,
			'NUMBER_FLAGGED': 0,
			'STILL_COVERED': 0,
		}, 
	],
	"""

	__DATA = copy.deepcopy(__DATA_START)

	def __init__(self, options=None):
		super().__init__('status_off')

		if options is not None:
			if 'PRINT_MODE' in options:
				self.__PRINT_MODE = self.__PRINT_CODE[options['PRINT_MODE']]
			if 'DELAY' in options:
				self.__DELAY = options['DELAY']
			if 'GUESS' in options:
				self.__GUESS = options['GUESS']

	def getData(self):
		return self.__DATA

	def __setupDataCollection(self, game):
		self.__DATA = copy.deepcopy(self.__DATA_START)
		self.__DATA['GAME']['RESULT'] = self.RESULT_CODE['N/A']
		self.__DATA['GAME']['CELL_COUNT']['HEIGHT'] = game.getBoardHeight()
		self.__DATA['GAME']['CELL_COUNT']['WIDTH'] = game.getBoardWidth()
		self.__DATA['GAME']['CELL_COUNT']['TOTAL'] = game.getBoardHeight() * game.getBoardWidth()
		self.__DATA['GAME']['CELL_COUNT']['BOMBS'] = game.getTotalBombs()

	def __updateDataLoop(self, index, turn, flagged=None, opened=None):
		self.__DATA['LOOP'].append({})
		self.__DATA['LOOP'][index]['BOMBS_LEFT'] = turn['BOMBS']
		self.__DATA['LOOP'][index]['TIME_ELAPSED'] = '{0:.2f}'.format(turn['TIME'])
		self.__DATA['LOOP'][index]['NUMBER_FLAGGED'] = 0 if flagged is None else flagged
		self.__DATA['LOOP'][index]['NUMBER_OPENED'] = 0 if opened is None else opened
		all_cells = [(x, y)
			for x in range(len(turn['BOARD'])) 
			for y in range(len(turn['BOARD'][x]))]
		self.__DATA['LOOP'][index]['STILL_COVERED'] = len(self._filterCells(turn['BOARD'], all_cells, code='COVERED'))

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

	def __canIFlagThis(self, board, bombs, coordinates):
		testBoard = copy.deepcopy(board)
		testBoard[coordinates[0]][coordinates[1]] = self._CODES['FLAGGED']
		modifiedCells = [coordinates]

		influencedCells = self._getNeighbors(board, coordinates, code='REALLY_OPENED')

		return self.__recursiveSolution(testBoard, bombs - 1, influencedCells, modifiedCells)

	def __canIOpenThis(self, board, bombs, coordinates):
		testBoard = copy.deepcopy(board)
		testBoard[coordinates[0]][coordinates[1]] = self._CODES['OPENED']
		modifiedCells = [coordinates]

		influencedCells = self._getNeighbors(board, coordinates, code='REALLY_OPENED')

		return self.__recursiveSolution(testBoard, bombs, influencedCells, modifiedCells)

	def __stateCheckPhase(self, previousTurn, thisTurn):
		if previousTurn['BOARD'] == thisTurn['BOARD']:
			# if self.__AI_STATE == self.__STATE_CODE['NORMAL']:
				# self.__AI_STATE = self.__STATE_CODE['WARNING']
			# elif self.__AI_STATE == self.__STATE_CODE['WARNING']:
				# self.__AI_STATE = self.__STATE_CODE['CRITICAL']
			# elif self.__AI_STATE == self.__STATE_CODE['CRITICAL']:
				# self.__AI_STATE = self.__STATE_CODE['GUESS']

			if self.__AI_STATE == self.__STATE_CODE['NORMAL']:
				self.__AI_STATE = self.__STATE_CODE['WARNING']
			elif self.__AI_STATE == self.__STATE_CODE['WARNING']:
				self.__AI_STATE = self.__STATE_CODE['GUESS']
			elif self.__AI_STATE == self.__STATE_CODE['GUESS']:
				self.__AI_STATE = self.__STATE_CODE['DONE']
				self.__DATA['GAME']['RESULT'] = self.RESULT_CODE['GIVE_UP']
		elif self.__AI_STATE != self.__STATE_CODE['NORMAL'] and self.__AI_STATE != self.__STATE_CODE['DONE']:
			self.__AI_STATE = self.__STATE_CODE['NORMAL']

	def __searchPhase(self, thisTurn):
		# Depending on the game mode, add certain cells to these arrays
		toOpen = []
		toFlag = []

		if self.__AI_STATE == self.__STATE_CODE['NORMAL']:
			# Candidates for modification are any covered cells neighboring opened cells
			candidates = [(x, y)
				for x in range(len(thisTurn['BOARD'])) 
				for y in range(len(thisTurn['BOARD'][x]))
				if thisTurn['BOARD'][x][y] == self._CODES['COVERED'] 
				and len(self._getNeighbors(thisTurn['BOARD'], (x, y), code='REALLY_OPENED')) > 0]

			for c in candidates:
				# For efficiency, check that the candidate has not been solved yet
				if c not in toOpen and c not in toFlag:
					# If this move would conflict with game logic, canFlag is False
					# If it is possible to do this move, canFlag contains two lists:
					# canFlag[0] is a list of cells that would be opened according to game logic
					# canFlag[1] is a list of cells that would be flagged according to game logic
					canFlag = self.__canIFlagThis(thisTurn['BOARD'], thisTurn['BOMBS'], c)
					canOpen = self.__canIOpenThis(thisTurn['BOARD'], thisTurn['BOMBS'], c)

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

		elif self.__AI_STATE == self.__STATE_CODE['WARNING']:
			toOpen, toFlag = linalg.solution(self, thisTurn)


		elif self.__AI_STATE == self.__STATE_CODE['GUESS'] and self.__GUESS == True:
			all_cells = [(x, y)
				for x in range(len(thisTurn['BOARD'])) 
				for y in range(len(thisTurn['BOARD'][x]))]
			covered_cells = self._filterCells(thisTurn['BOARD'], all_cells, 'COVERED')

			toOpen.append(covered_cells[random.randrange(len(covered_cells))])

		return (toOpen, toFlag)

	"""
	Expects an already-started game (unless guessing is turned on)
	"""
	def solve(self, game):
		# Information to keep track within the loops
		self.__AI_STATE = self.__STATE_CODE['NORMAL']
		previousTurn = game.getGameVisible()
		thisTurn = game.getGameVisible()

		# Set up data collection and add first loop information
		loop_count = 0
		self.__setupDataCollection(game)
		self.__updateDataLoop(loop_count, thisTurn)

		if self.__PRINT_MODE != self.__PRINT_CODE['NOTHING']:
			print('\nVisible: ')
			game.consoleDisplayVisible()
			print('')
			print('')
			print('STARTING SOLUTION LOOP')

		while(self.__AI_STATE != self.__STATE_CODE['DONE']):
			### SETUP LOOP
			# Prepare loop with all necessary functions
			time.sleep(self.__DELAY)
			loop_count = loop_count + 1

			### SEARCH PHASE
			toOpen, toFlag = self.__searchPhase(thisTurn)

			### WORK PHASE
			# Open and flag the cells that were determined in the search phase
			toOpen = list(set(toOpen))
			toFlag = list(set(toFlag))

			countOpened = 0
			countFlagged = 0

			for c in toFlag:
				game.flag(c[0], c[1])
				countFlagged = countFlagged + 1

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

			### STATE CHECK PHASE
			# Start the decision process to see if we need to elevate the level of solving
			previousTurn = copy.deepcopy(thisTurn)
			thisTurn = game.getGameVisible()
			self.__stateCheckPhase(previousTurn, thisTurn)

			### END OF LOOP PHASE
			# Add data to data collection and print information to console
			self.__updateDataLoop(loop_count, thisTurn, flagged=countFlagged, opened=countOpened)

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
		self.__DATA['GAME']['CELL_COUNT']['NUMERICAL'] = [self._countAllCells(solution['BOARD'], str(i)) for i in range(9)]

		# Count of bombs on the edge of the board (predicted more likely to end in giving up due to guessing)
		edges = copy.deepcopy(solution['BOARD'])
		edges = [edges[i] if (i == 0 or i == len(edges) - 1) else [edges[i][0], edges[i][len(edges[i]) - 1]]
			for i in range(len(edges))]
		# for i in range(1, len(edgesBoard) - 1):
			# edgesBoard[i] = [edgesBoard[i][0], edgesBoard[i][len(edgesBoard[0]) - 1]]
		self.__DATA['GAME']['CELL_COUNT']['BOMBS_AT_EDGES'] = self._countAllCells(edges, 'BOMB')

		return game
