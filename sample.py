# TODO write a testing suite to run this over a long period to get data
# I want this testing suite to iterate over all possible starting locations of each board
# It should generate a percentage of how likely you are to get a playable board with no guessing
# Ideal boards can be completed 100% of the time with no guessing
# There might be a range from 1% to 99%
# I expect many in the 0% to 1% range: board which have one guessing spot that can 
# be fixed only when the user starts exactly there

# Dependency: makes little sense before the data gathering listed below is implemented
# Q: does it matter that the displaced bombs on the first click will be randomly placed elsewhere?

from game import *
from ai import *
import time
import copy
import random

def new_game(silent=False, options=None, level='BEGINNER', specs={}):
	if not silent:
		print('Creating game object...')
		print('Using options {}'.format(options))
	g = Game(options=options)

	if not silent:
		print('')

	if not silent:
		print('Generating game...')
		print('Using level {} and specs {}.'.format(level, specs))
	g.populateBoard(level=level, specs=specs)

	if not silent:
		print('')

	return g

def start_game(silent=False, startSeed=None, startPosition=None, options=None, level='BEGINNER', specs={}):
	if silent:
		options.update({'SILENT': True})
	g = new_game(silent=silent, options=options, level=level, specs=specs)

	mySeed = random.randrange(100000) if startSeed is None else startSeed
	random.seed(mySeed)
	h = g.getBoardHeight()
	w = g.getBoardWidth()
	x = random.randrange(h) if startPosition is None else startPosition[0]
	y = random.randrange(w) if startPosition is None else startPosition[1]

	if not silent:
		print('Starting game with seed = {}'.format(mySeed))
		print('Starting game with open({}, {})...'.format(x,y))
		print('')

	g.open(x,y)
	return (g, mySeed)

def solveMany(howMany):
	solver = Solver(options={'PRINT_MODE': 'NOTHING'})
	total = howMany
	results = []

	for i in range(howMany):
		# Recommended sleep time:
		# Beginner/Intermediate - 1 second
		# Expert - 2.5 seconds
		time.sleep(2.5)
		print('{}... '.format(i), end='')
		mygame, start_seed = start_game(silent=True, options={}, level='EXPERT', specs={})
		solver.solve(mygame)
		print('Game seed: {}, '.format(mygame.getGameSolution()['SEED']), end='')
		print('Start seed: {}'.format(start_seed))

		results.append({})
		data = solver.getData()
		results[i]['RESULT'] = data['GAME']['RESULT'] == Solver.RESULT_CODE['WIN']

	wins = len([w for w in results if w['RESULT'] == Solver.RESULT_CODE['WIN']])
	print('Wins: {}/{} ({}%)'.format(wins, total, 100 * wins / total))

def solveOne():
	solver = Solver(options={'DELAY': 0.5, 'PRINT_MODE': 'BOARD'})
	# Favorite one so far: startSeed=76964, seed=69365, level='EXPERT'
	mygame = start_game(startSeed=76964, silent=False, options={'SEED': 69365, 'DISPLAY_ON_MOVE': False, 'PRINT_GUIDES': True, 'PRINT_SEED': True}, level='EXPERT', specs={})

	# Note: pass by reference; will modify my own copy
	solver.solve(mygame)

	mygame.consoleDisplayVisible()

	# print(solver.getData())

if __name__=='__main__':
	solveMany(100)
	# solveOne()
