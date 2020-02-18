"""
Basic usage:
`python3`
`import api`
`g = api.start_game()`
"""

import copy
import time
import math
import random

"""
Public members:

CELL_CODE
__init__(options=None)
populateBoard(level='BEGINNER', specs={})
open(x, y)
flag(x, y)
unflag(x, y)
chord(x, y)
consoleDisplaySolution()
consoleDisplayVisible()
getBombsLeft()
getTimeElapsed()
getBoardHeight()
getBoardWidth()
exportGame() # somewhat broken
importGame(board) # somewhat broken
getGameVisible()
getGameSolution()
"""
class Game:
	__LEVEL_CODE = {
		'BEGINNER': {
			'height': 8,
			'width': 8,
			'bombs': 10,
		},
		'INTERMEDIATE': {
			'height': 16,
			'width': 16,
			'bombs': 40,
		},
		'EXPERT': {
			'height': 16,
			'width': 30,
			'bombs': 99,
		},
	}

	__STATUS_CODE = {
		'COVERED': '-',
		'FLAGGED': '#',
		'OPENED': '?',
	}

	__CONTENT_CODE = {
		'BOMB': 'B',
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

	__STATE_CODE = {
		'NOT_PLAYING': 0,
		'READY_TO_PLAY': 1,
		'PLAYING': 2,
		'LOST': 3,
		'CLEANING': 4,
		'WON': 5,
	}

	CELL_CODE = {}
	CELL_CODE.update(__STATUS_CODE)
	CELL_CODE.update(__CONTENT_CODE)

	# options
	__DEBUG = False
	__DISPLAY_ON_MOVE = True
	__PRINT_GUIDES = True
	__SEED = None
	__REUSE_SEED = False
	__PRINT_SEED = True
	__SILENT = False

	# game data
	__BOARD = []
	__GAME_STATE = __STATE_CODE['NOT_PLAYING']
	__CHORD_STARTED = False
	__TOTAL_BOMBS = 0
	__BOMBS_LEFT = 0
	__START_TIME = 0
	__END_TIME = 0

	def __init__(self, options=None):
		if options is not None:
			if 'DEBUG' in options:
				self.__DEBUG = options['DEBUG']
			if 'DISPLAY_ON_MOVE' in options:
				self.__DISPLAY_ON_MOVE = options['DISPLAY_ON_MOVE']
			if 'PRINT_GUIDES' in options:
				self.__PRINT_GUIDES = options['PRINT_GUIDES']
			if 'SEED' in options:
				self.__SEED = options['SEED']
			if 'REUSE_SEED' in options:
				self.__REUSE_SEED = options['REUSE_SEED']
			if 'PRINT_SEED' in options:
				self.__PRINT_SEED = options['PRINT_SEED']
			if 'SILENT' in options:
				self.__SILENT = options['SILENT']
				self.__DISPLAY_ON_MOVE = False
				self.__PRINT_SEED = False

		# For users that want a seed but don't want to supply it
		self.__SEED = random.randrange(100000) if self.__SEED == None and (self.__REUSE_SEED or self.__PRINT_SEED) else self.__SEED
		if self.__SEED != None and not self.__REUSE_SEED:
			if self.__PRINT_SEED:
				print('Initializing with seed = {}'.format(self.__SEED))
			random.seed(self.__SEED)

	# Decorator to check whether x, y are within board height and width ranges
	def __validateArguments(func):
		def inner1(self, x, y):
			if x not in range(len(self.__BOARD)) or y not in range(len(self.__BOARD[0])):
				if len(self.__BOARD) == 0:
					message = 'board is not yet initialized. Cannot call {}({}, {}).'.format(func.__name__,x,y)
					raise ValueError(message)
				message = '({},{}) are invalid arguments for board of size ({}, {}).'.format(x,y,len(self.__BOARD), len(self.__BOARD[0]))
				raise ValueError(message)
			return func(self, x, y)

		return inner1

	# Decorator to check the game state. Accomplishes two tasks:
	# 1. Will only allow actions when state is 'PLAYING'
	# 2. Will update state from 'PLAYING' to 'WON'/'LOST' upon game end
	def __stateCheck(func):
		def inner1(self, *args, **kwargs):
			if self.__GAME_STATE == self.__STATE_CODE['PLAYING'] or self.__GAME_STATE == self.__STATE_CODE['READY_TO_PLAY']:
				func(self, *args, **kwargs)
			elif self.__GAME_STATE == self.__STATE_CODE['CLEANING']:
				func(self, *args, **kwargs)
				return
			elif self.__GAME_STATE == self.__STATE_CODE['LOST'] or self.__GAME_STATE == self.__STATE_CODE['WON']:
				return
			else:
				raise Exception('Board is not yet initialized. Populate board to continue playing.')

			# check if game ended by win or loss
			if self.__lostCheck():
				self.__END_TIME = time.time() - self.__START_TIME
				self.__GAME_STATE = self.__STATE_CODE['LOST']
				if self.__DISPLAY_ON_MOVE:
					self.consoleDisplayVisible()
				if not self.__SILENT:
					print('Game lost!')
				return False
			elif self.__wonCheck():
				self.__END_TIME = time.time() - self.__START_TIME
				self.__GAME_STATE = self.__STATE_CODE['CLEANING']
				self.__cleanBoard()
				self.__GAME_STATE = self.__STATE_CODE['WON']
				if self.__DISPLAY_ON_MOVE:
					self.consoleDisplayVisible()
				if not self.__SILENT:
					print('Game won!')
				return True
			else:
				return

		return inner1

	# Do not try to simplify the following functions into one helper function.
	# I tried. It would need to provide the following results: 
	#           lost?     won?
	# switch:	T T T T   F F F F
	# isBomb:	T T F F   T T F F
	# isOpen:	T F T F   T F T F
	# 			-----------------
	# return:	T F F F   T T T F
	# The logic required is: ((b xnor s) and (o xnor s)) xnor s 
	# It is too ridiculous to implement. Stick with the simple, understandable functions. 
	def __lostCheck(self):
		for x in self.__BOARD:
			for y in x:
				isBomb = y['CONTENT'] == self.__CONTENT_CODE['BOMB']
				isOpen = y['STATUS'] == self.__STATUS_CODE['OPENED']

				if isBomb and isOpen:
					return True
		return False

	def __wonCheck(self):
		for x in self.__BOARD:
			for y in x:
				isNotBomb = y['CONTENT'] != self.__CONTENT_CODE['BOMB']
				isNotOpen = y['STATUS'] != self.__STATUS_CODE['OPENED']

				if isNotBomb and isNotOpen:
					return False
		return True

	def __cleanBoard(self):
		for x in range(len(self.__BOARD)):
			for y in range(len(self.__BOARD[x])):
				try:
					self.flag(x, y)
				except:
					pass
		self.__BOMBS_LEFT = 0

	# Expects level supplied as string and specs supplied as dict
	# Available specs are 'height', 'width', and 'bombs'
	# If all three specs are not supplied, the default from the given level 
	# will be used. The level itself defaults to beginner, which is 8x8, 10 bombs
	def populateBoard(self, level='BEGINNER', specs={}):
		if self.__REUSE_SEED:
			if self.PRINT_SEED:
				print('Populating board with seed = {}'.format(self.__SEED))
			random.seed(self.__SEED)

		self.__BOARD = []

		# Validate arguments
		if level in self.__LEVEL_CODE:
			h = self.__LEVEL_CODE[level]['height']
			w = self.__LEVEL_CODE[level]['width']
			b = self.__LEVEL_CODE[level]['bombs']
		else:
			raise ValueError('Invalid Level Code. Please choose one of \'BEGINNER\', \'INTERMEDIATE\', or \'EXPERT\'.')
		if 'height' in specs:
			h = specs['height']
		if 'width' in specs:
			w = specs['width']
		if 'bombs' in specs:
			b = specs['bombs']

		if h <= 0 or w <= 0 or b >= h * w:
			raise ValueError('Invalid parameters: can not make a board of size {}x{} with {} bombs'.format(h,w,b))

		# Add all cells, set status to covered
		[self.__BOARD.append([{'STATUS': self.__STATUS_CODE['COVERED'], 'CONTENT': self.__CONTENT_CODE['0']} for i in range(w)]) for j in range(h)]

		self.__TOTAL_BOMBS = b
		self.__BOMBS_LEFT = b

		# Set cell content to bomb for b number of bombs, randomly placed
		while b > 0:
			x = random.randrange(h)
			y = random.randrange(w)
			if self.__BOARD[x][y]['CONTENT'] != self.__CONTENT_CODE['BOMB']:
				self.__BOARD[x][y].update({'CONTENT': self.__CONTENT_CODE['BOMB']})
				b = b - 1

		for x in range(h):
			for y in range(w):
				if self.__BOARD[x][y]['CONTENT'] != self.__CONTENT_CODE['BOMB']:
					self.__BOARD[x][y].update({'CONTENT': self.__CONTENT_CODE[str(self.__countBombs(x, y))]})

		self.__START_TIME = 0
		self.__END_TIME = 0
		self.__GAME_STATE = self.__STATE_CODE['READY_TO_PLAY']

	@__validateArguments
	def __countFlags(self, x, y):
		return self.__countNeighbors(x, y, 'STATUS', 'FLAGGED')

	@__validateArguments
	def __countBombs(self, x, y):
		return self.__countNeighbors(x, y, 'CONTENT', 'BOMB')

	def __countNeighbors(self, x, y, code, subcode):
		neighbors = self.__getNeighborCoordinates(x, y)
		count = 0

		for n in neighbors:
			cell = self.__BOARD[n[0]][n[1]]
			if code == 'STATUS' and cell[code] == self.__STATUS_CODE[subcode]:
				count = count + 1
			if code == 'CONTENT' and cell[code] == self.__CONTENT_CODE[subcode]:
				count = count + 1

		return count

	def __getNeighborCoordinates(self, x, y):
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
		if x == len(self.__BOARD) - 1:
			coordinates[6] = None
			coordinates[7] = None
			coordinates[8] = None
		if y == 0:
			coordinates[0] = None
			coordinates[3] = None
			coordinates[6] = None
		if y == len(self.__BOARD[0]) - 1:
			coordinates[2] = None
			coordinates[5] = None
			coordinates[8] = None

		# Set coordinates for the given cell to None
		coordinates[4] = None
		
		return [c for c in coordinates if c is not None]

	def __displayOnMove(self):
		if self.__DISPLAY_ON_MOVE and not self.__CHORD_STARTED:
			if self.__GAME_STATE == self.__STATE_CODE['PLAYING'] or self.__GAME_STATE == self.__STATE_CODE['READY_TO_PLAY']:
				self.consoleDisplayVisible()

	@__stateCheck
	def __change_status(self, cell, code, altcode):
		if cell['STATUS'] == self.__STATUS_CODE[code]:
			cell['STATUS'] = self.__STATUS_CODE[altcode]
			return True
		return False

	@__validateArguments
	def flag(self, x, y):
		self.__change_status(self.__BOARD[x][y], 'COVERED', 'FLAGGED')

		if self.__GAME_STATE == self.__STATE_CODE['PLAYING'] or self.__GAME_STATE == self.__STATE_CODE['READY_TO_PLAY']:
			self.__BOMBS_LEFT = self.__BOMBS_LEFT - 1
		self.__displayOnMove()

	@__validateArguments
	def unflag(self, x, y):
		self.__change_status(self.__BOARD[x][y], 'FLAGGED', 'COVERED')
		self.__BOMBS_LEFT = self.__BOMBS_LEFT + 1
		self.__displayOnMove()

	@__validateArguments
	def open(self, x, y):
		if self.__GAME_STATE == self.__STATE_CODE['READY_TO_PLAY']:
			bombNeighbors = self.__moveBomb(x, y, x, y)
			for n in bombNeighbors:
				self.__moveBomb(n[0], n[1], x, y)
			self.__GAME_STATE = self.__STATE_CODE['PLAYING']
			self.__START_TIME = time.time()

		cell = self.__BOARD[x][y]
		gameEnd = self.__change_status(cell, 'COVERED', 'OPENED')

		# Chord if empty and not currently in the process of chording
		if self.__mergeVisible(cell, 'STATUS') == self.__CONTENT_CODE['0'] and not self.__CHORD_STARTED:
			gameEnd = self.chord(x, y)
		else:
			self.__displayOnMove()

		return gameEnd

	# This function checks whether the given cell is a bomb or not 
	# If it is, it will remove the bomb from (x, y), decrement numerical neighbors, 
	# place it at a random location (i, j), and icnrement numerical new neighbors
	# Whether the given cell is a bomb or not, it returns a list of all neighbors
	# around (x, y) which are bombs themselves
	def __moveBomb(self, x, y, a, b):
		neighbors = self.__getNeighborCoordinates(x, y)
		bombNeighbors = [n for n in neighbors if self.__BOARD[n[0]][n[1]]['CONTENT'] == self.__CONTENT_CODE['BOMB']]

		if self.__BOARD[x][y]['CONTENT'] != self.__CONTENT_CODE['BOMB']:
			return bombNeighbors

		value = len(bombNeighbors)
		self.__BOARD[x][y]['CONTENT'] = self.__CONTENT_CODE[str(value)]

		for n in neighbors:
			if n not in bombNeighbors:
				value = self.__BOARD[n[0]][n[1]]['CONTENT'] - 1
				self.__BOARD[n[0]][n[1]]['CONTENT'] = self.__CONTENT_CODE[str(value)]

		while True:
			# TODO Should the user be asked to pass in another seed for randomly displacing bombs?
			# Currently, because the generation of the board is the same for every successive run with a given seed, 
			# the new location of displaced bombs will also be the same for every successive run with that seed
			i = random.randrange(len(self.__BOARD))
			j = random.randrange(len(self.__BOARD[0]))
			if self.__BOARD[i][j]['CONTENT'] != self.__CONTENT_CODE['BOMB']:
				# Compare to where the actual location is
				if (i, j) not in self.__getNeighborCoordinates(a, b) and (i, j) != (a, b):
					self.__BOARD[i][j]['CONTENT'] = self.__CONTENT_CODE['BOMB']
					break

		newNeighbors = self.__getNeighborCoordinates(i, j)
		newBombNeighbors = [n for n in newNeighbors if self.__BOARD[n[0]][n[1]]['CONTENT'] == self.__CONTENT_CODE['BOMB']]

		for n in newNeighbors:
			if n not in newBombNeighbors:
				value = self.__BOARD[n[0]][n[1]]['CONTENT']
				value = (0 if value == self.__CONTENT_CODE['0'] else value) + 1
				self.__BOARD[n[0]][n[1]]['CONTENT'] = self.__CONTENT_CODE[str(value)]

		return bombNeighbors

	@__validateArguments
	def chord(self, x, y):
		# Can not chord on covered or flagged cells
		if self.__BOARD[x][y]['STATUS'] != self.__STATUS_CODE['OPENED']:
			if not self.__SILENT:
				print('Cannot chord on covered or flagged cells')
			return

		# Start and end the chord
		self.__CHORD_STARTED = True
		gameEnd = self.__chordOpen([(x, y)])
		self.__CHORD_STARTED = False

		self.__displayOnMove()

		return gameEnd

	# Recursive function which takes a list of tuples representing cell coordinates
	# Assumes that all of the cells have been opened
	# Checks that all of the cells have their neighbor bombs flagged, then constructs
	# a list of neighbor cell coordinates. Proceeds to open all neighbor cells that
	# are currently covered, then recursively calls itself on all neighbor cells that
	# are empty. 
	# Note: User would expect upon chording a cell that any empty cells that got opened
	# would chord themselves automatically. 
	# Base case: when list of neighbor cells to open in the next layer is empty, return
	def __chordOpen(self, coordinates):
		# Can not chord on cells that don't have all neighbor bombs flagged
		for c in coordinates:
			content = self.__BOARD[c[0]][c[1]]['CONTENT']
			content = 0 if content == ' ' else content
			if self.__countFlags(c[0], c[1]) != content:
				if not self.__SILENT:
					print('Cannot chord on cells that are touching the wrong number of flags')
				return False

		allNeighbors = []
		for c in coordinates:
			allNeighbors.extend(self.__getNeighborCoordinates(c[0], c[1]))

		# Remove duplicates and filter out any which are flagged or opened
		allNeighbors = list(set(allNeighbors))
		allNeighbors = [n for n in allNeighbors if self.__BOARD[n[0]][n[1]]['STATUS'] == self.__STATUS_CODE['COVERED']]

		for n in allNeighbors:
			self.open(n[0], n[1])

		# Filter out all recently opened neighbors that are not empty
		allNeighbors = [n for n in allNeighbors if self.__BOARD[n[0]][n[1]]['CONTENT'] == self.__CONTENT_CODE['0']]

		if len(allNeighbors) == 0:
			return
		else:
			return self.__chordOpen(allNeighbors)

	# If the code is 'STATUS', then I am trying to display what the user would be seeing
	# The user would not see the code for opened cells, they would instead see the value
	# of the cell taking the place of its status
	# So if the status is opened, I will always return the content
	def __mergeVisible(self, cell, code):
		if cell['STATUS'] == self.__STATUS_CODE['OPENED']:
			return cell['CONTENT']
		else:
			return cell[code]

	def __consoleDisplay(self, code):
		if len(self.__BOARD) == 0:
			message = 'Board is not yet initialized. Cannot call display.'
			raise ValueError(message)

		# Top fancy bit
		print('/===' if self.__PRINT_GUIDES else '/=', end='')
		for y in self.__BOARD[0]:
			print('==', end='')
		print('\\')
		# Number of seconds elapsed
		print('| ', end='')
		message = 'Time: {0:.2f}'.format(self.getTimeElapsed())
		print(message, end='')
		for column in range((2 * len(self.__BOARD[0])) - len(message)):
			print(' ', end='')
		print('  |' if self.__PRINT_GUIDES else '|')
		# Number of bombs left
		print('| ', end='')
		message = 'Bombs left: {}'.format(self.__BOMBS_LEFT)
		print(message, end='')
		for column in range((2 * len(self.__BOARD[0])) - len(message)):
			print(' ', end='')
		print('  |' if self.__PRINT_GUIDES else '|')

		# Separation bit
		print('|===' if self.__PRINT_GUIDES else '|=', end='')
		for y in self.__BOARD[0]:
			print('==', end='')
		print('\\')
		# Blank line / column numbers
		print('|   ' if self.__PRINT_GUIDES else '| ', end='')
		for column in range(len(self.__BOARD[0])):
			print('{} '.format(str(column % 10)) if self.__PRINT_GUIDES else '  ', end='')
		print('|')

		# Row contents
		for row in range(len(self.__BOARD)):
			# Print the row number before the row contents
			print('| {} '.format(str(row % 10)) if self.__PRINT_GUIDES else '| ', end='')

			for y in self.__BOARD[row]:
				print(self.__mergeVisible(y, code), end=' ')
			print('|')

		# Bottom fancy bit
		print('|   ' if self.__PRINT_GUIDES else '| ', end='')
		for y in self.__BOARD[0]:
			print('  ', end='')
		print('|')
		print('\\===' if self.__PRINT_GUIDES else '\\=', end='')
		for y in self.__BOARD[0]:
			print('==', end='')
		print('/')

	def consoleDisplayVisible(self):
		self.__consoleDisplay('STATUS')

	def consoleDisplaySolution(self):
		# If they take a peek at the solution, then the game is over
		if not self.__DEBUG and self.__GAME_STATE == self.__STATE_CODE['PLAYING']:
			self.__GAME_STATE = self.__STATE_CODE['NOT_PLAYING']
		self.__consoleDisplay('CONTENT')

	def getTotalBombs(self):
		return self.__TOTAL_BOMBS

	def getBombsLeft(self):
		return self.__BOMBS_LEFT

	def getTimeElapsed(self):
		return time.time() - self.__START_TIME

	def getBoardHeight(self):
		return len(self.__BOARD)

	def getBoardWidth(self):
		return len(self.__BOARD[0]) if self.getBoardHeight() > 0 else 0

	# TODO export and import somewhat broken
	# There needs to be a way to import the game state
	# As well as the number of bombs left and time
	def exportGame(self):
		return copy.deepcopy(self.__BOARD)

	# def importGame(self, board, game_state, start_time, pause_time):
	def importGame(self, board, game_state, start_time, pause_time):
		self.__BOARD = copy.deepcopy(board)
		# If none of the cells have been opened, 
		# then the state is READY_TO_PLAY
		playing = False
		for row in self.__BOARD:
			for cell in row:
				if cell['CONTENT'] != self.__CONTENT_CODE['COVERED'] and cell['CONTENT'] != self.__CONTENT_CODE['FLAGGED']:
					playing = True
		
		self.__GAME_STATE = self.__STATE_CODE['PLAYING'] if playing else self.__STATE_CODE['READY_TO_PLAY']
		return True

	def getGameVisible(self):
		return self.__getGame('STATUS')

	def getGameSolution(self):
		if not self.__DEBUG and self.__GAME_STATE == self.__STATE_CODE['PLAYING']:
			self.__GAME_STATE = self.__STATE_CODE['NOT_PLAYING']
		return self.__getGame('CONTENT')

	def __getGame(self, code):
		values = {}
		values.update({'BOARD': self.__getBoard(code)})
		values.update({'BOMBS': self.getBombsLeft()})
		values.update({'TIME': self.getTimeElapsed()})
		return values

	def __getBoard(self, code):
		board = []
		h = len(self.__BOARD)
		if h == 0:
			message = 'Board is not yet initialized. Cannot call display.'
			raise Exception(message)
		else:
			w = len(self.__BOARD[0])

		[board.append([self.__mergeVisible(self.__BOARD[i][j], code) for j in range(w)]) for i in range(h)]
		return board

# Used mainly for testing purposes
if __name__=='__main__':
	mygame = Game(options={'PRINT_GUIDES': True, 'DISPLAY_ON_MOVE': True})
	mygame.populateBoard(level='EXPERT', specs={'bombs': 30})
	print('\nSolution: ')
	mygame.consoleDisplaySolution()

	mygame.open(0,0)
