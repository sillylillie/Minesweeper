from functionality import MinesweeperFunctions
import numpy as np
import itertools
import time

class LinearAlgebraAlgorithm(MinesweeperFunctions):

	def __init__(self):
		super().__init__('status_off')

	def solution(self, solver, turn):
		requirement_cells = [(x, y)
			for x in range(len(turn['BOARD'])) 
			for y in range(len(turn['BOARD'][x]))
			if turn['BOARD'][x][y] != self._CODES['COVERED'] 
			and turn['BOARD'][x][y] != self._CODES['FLAGGED'] 
			and len(self._getNeighbors(turn['BOARD'], (x, y), code='COVERED')) > 0]
		fulfillment_cells = [(x, y)
			for x in range(len(turn['BOARD'])) 
			for y in range(len(turn['BOARD'][x]))
			if turn['BOARD'][x][y] == self._CODES['COVERED'] 
			and len(self._getNeighbors(turn['BOARD'], (x, y), code='REALLY_OPENED')) > 0]

		print('requirement_cells (len={}): {}'.format(len(requirement_cells), requirement_cells))
		print('fulfillment_cells (len={}): {}'.format(len(fulfillment_cells), fulfillment_cells))

		requirements = np.mat([[1 if fc in self._getNeighbors(turn['BOARD'], rc) else 0 
				for fc in fulfillment_cells]
			for rc in requirement_cells])
		print('Requirements: \n{}'.format(requirements))

		start_time = time.time()

		goal = np.mat([turn['BOARD'][c[0]][c[1]] - len(self._getNeighbors(turn['BOARD'], c, code='FLAGGED')) 
			for c in requirement_cells])
		print('Goal: \n{}'.format(goal))

		# For beginner board with 9 cells to fill, should be 2^9 = 512 possible solutions
		# https://stackoverflow.com/questions/14931769/how-to-get-all-combination-of-n-binary-value
		guesses = list(itertools.product([0, 1], repeat=len(fulfillment_cells)))
		print('(first 8) Possible Solutions (len={}): \n{}'.format(len(guesses), guesses[:8]))

		solutions = [s for s in guesses 
			if np.equal(requirements.dot(np.array(s))[0], goal).all()]
		solutions = [s for s in solutions 
			if sum(s) <= turn['BOMBS']]
		print('(first 8) Correct Solutions (len={}): \n{}'.format(len(solutions), solutions[:8]))

		end_time = time.time()

		print('Time taken: {}'.format(end_time - start_time))

		return [],[]

