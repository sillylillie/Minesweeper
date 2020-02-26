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

def printStats(data):
	results = []
	for d in range(len(data)):
		results.append({})
		results[d]['RESULT'] = data[d]['solver']['GAME']['RESULT'] == Solver.RESULT_CODE['WIN']
		results[d]['STILL_COVERED'] = data[d]['solver']['LOOP'][-1]['STILL_COVERED']
		results[d]['PERCENT_EXPLORED'] = 1 - (results[d]['STILL_COVERED'] / data[d]['solver']['GAME']['CELL_COUNT']['TOTAL'])
		results[d]['TIME'] = float(data[d]['solver']['LOOP'][-1]['TIME_ELAPSED'])


	wins = len([w for w in results if w['RESULT'] == Solver.RESULT_CODE['WIN']])
	total = len(data)
	print('Wins: {0}/{1} ({2:.2f}%)'.format(wins, total, 100 * wins / total))
	print('Average exploration: {0:.2f}%'.format(100 * sum(r['PERCENT_EXPLORED'] for r in results) / total))
	print('Average time: {0:.2f}'.format(sum([r['TIME'] for r in results]) / total))
	if wins < total:
		print('--- For lost boards only: ')
		print('Average exploration: {0:.2f}%'.format(100 * sum(r['PERCENT_EXPLORED'] for r in results if r['RESULT'] != Solver.RESULT_CODE['WIN']) / (total - wins)))
		print('Average time: {0:.2f}'.format(sum([r['TIME'] for r in results if r['RESULT'] != Solver.RESULT_CODE['WIN']]) / (total - wins)))
	if wins > 0:
		print('--- For won boards only: ')
		print('Average exploration: {0:.2f}%'.format(100 * sum(r['PERCENT_EXPLORED'] for r in results if r['RESULT'] == Solver.RESULT_CODE['WIN']) / wins))
		print('Average time: {0:.2f}'.format(sum([r['TIME'] for r in results if r['RESULT'] == Solver.RESULT_CODE['WIN']]) / wins))

# Recommended sleep time:
# Expert - 0.1 seconds
def solveMany(howMany, sleep=0.1):
	solver = Solver(options={'GUESS': True, 'PRINT_MODE': 'NOTHING'})
	total = howMany
	data = []

	for i in range(howMany):
		time.sleep(sleep)

		mygame, start_seed = start_game(silent=True, options={}, level='EXPERT', specs={})
		try:
			solver.solve(mygame)
		except:
			mygame.consoleDisplayVisible()

		data.append({'solver': solver.getData(), 'game': mygame.getGameSolution()})

		print('{}... Game seed: {}, Start seed: {}'.format(i, mygame.getGameSolution()['SEED'], start_seed))

	printStats(data)

def solveOne():
	solver = Solver(options={'GUESS': True, 'DELAY': 0, 'PRINT_MODE': 'DOTS'})
	# Favorite one so far: startSeed=76964, seed=69365, level='EXPERT'
	# Interesting problem: startSeed=85173, seed=9357, level='EXPERT'
	
	mygame = start_game(silent=False, options={'DISPLAY_ON_MOVE': False, 'PRINT_GUIDES': True, 'PRINT_SEED': True}, level='EXPERT', specs={})[0]
	# mygame = start_game(startSeed=63615, silent=False, options={'SEED': 1281, 'DISPLAY_ON_MOVE': False, 'PRINT_GUIDES': True, 'PRINT_SEED': True}, level='EXPERT', specs={})[0]

	# Note: pass by reference; will modify my own copy
	try:
		solver.solve(mygame)
	except:
		mygame.consoleDisplayVisible()

	# mygame.consoleDisplayVisible()

	# print(solver.getData())

if __name__=='__main__':
	# solveMany(500, sleep=0)
	solveOne()
