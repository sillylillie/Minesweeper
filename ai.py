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
from linalg import LinearAlgebraAlgorithm
from recursive import RecursiveAlgorithm
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

	# Solvers
	__RECURSIVE_SOLVER = RecursiveAlgorithm()
	__LINEAR_ALGEBRA_SOLVER = LinearAlgebraAlgorithm()

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
					# If it is possible to do this move, canFlag is a list of two lists:
					#   canFlag[0] is a list of cells that would be opened according to game logic
					#   canFlag[1] is a list of cells that would be flagged according to game logic
					canFlag = self.__RECURSIVE_SOLVER.canIFlagThis(thisTurn['BOARD'], thisTurn['BOMBS'], c)
					canOpen = self.__RECURSIVE_SOLVER.canIOpenThis(thisTurn['BOARD'], thisTurn['BOMBS'], c)

					if canFlag and canOpen:
						# Even though there is not clear evidence to open or flag the candidate,
						# we can open/flag any neighbors that BOTH tests suggested opening/flagging
						toOpen.extend([o for o in canFlag[0] if o in canOpen[0]])
						toFlag.extend([o for o in canFlag[1] if o in canOpen[1]])

					elif not canFlag:
						# Clear evidence to open the candidate and modify suggested neighbors
						toOpen.extend(canOpen[0])
						toFlag.extend(canOpen[1])

					elif not canOpen:
						# Clear evidence to flag the candidate and modify suggested neighbors
						toOpen.extend(canFlag[0])
						toFlag.extend(canFlag[1])

		elif self.__AI_STATE == self.__STATE_CODE['WARNING']:
			xx = 0
			print('WARNING!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
			toOpen, toFlag = self.__LINEAR_ALGEBRA_SOLVER.solution(self, thisTurn)


		elif self.__AI_STATE == self.__STATE_CODE['GUESS'] and self.__GUESS == True:
			all_cells = [(x, y)
				for x in range(len(thisTurn['BOARD'])) 
				for y in range(len(thisTurn['BOARD'][x]))]
			covered_cells = self._filterCells(thisTurn['BOARD'], all_cells, 'COVERED')

			toOpen.append(covered_cells[random.randrange(len(covered_cells))])

		return (list(set(toOpen)), list(set(toFlag)))

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
