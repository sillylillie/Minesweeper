from functionality import MinesweeperFunctions
import numpy as np
import itertools
import time
import random

class LinearAlgebraAlgorithm(MinesweeperFunctions):

	def __init__(self):
		super().__init__('status_off')

	def __recursivelyFindGroup(self, board, cell, requirement_cells, fulfillment_cells):
		covered_neighbors = self._getNeighbors(board, cell, code='COVERED')
		# base case: no group
		if len(covered_neighbors) == 0:
			return [requirement_cells, fulfillment_cells]

		# remove covered neighbors that have already been added to the group
		covered_neighbors = [n for n in covered_neighbors if n not in fulfillment_cells]

		# base case: group has been accounted for in this direction
		if len(covered_neighbors) == 0:
			return [requirement_cells, fulfillment_cells]

		opened_neighbors = []
		for n in covered_neighbors:
			opened_neighbors.extend(self._getNeighbors(board, n, code='REALLY_OPENED'))
		opened_neighbors = [n for n in opened_neighbors if n not in requirement_cells]

		fulfillment_cells.extend(covered_neighbors)
		requirement_cells.extend(opened_neighbors)

		for n in opened_neighbors:
			requirement_cells, fulfillment_cells = self.__recursivelyFindGroup(board, n, requirement_cells, fulfillment_cells)

		return (list(set(requirement_cells)), list(set(fulfillment_cells)))

	def __findGroup(self, board, cell):
		return self.__recursivelyFindGroup(board, cell, [], [])

	def __getGroups(self, board):
		# get all requirement cells and fulfillment cells
		requirement_cells = [(x, y)
			for x in range(len(board)) 
			for y in range(len(board[x]))
			if board[x][y] != self._CODES['COVERED'] 
			and board[x][y] != self._CODES['FLAGGED'] 
			and len(self._getNeighbors(board, (x, y), code='COVERED')) > 0]
		fulfillment_cells = [(x, y)
			for x in range(len(board)) 
			for y in range(len(board[x]))
			if board[x][y] == self._CODES['COVERED'] 
			and len(self._getNeighbors(board, (x, y), code='REALLY_OPENED')) > 0]

		groups = []
		while len(requirement_cells) + len(fulfillment_cells) > 0:
			new_group = self.__findGroup(board, requirement_cells[random.randrange(len(requirement_cells))])

			requirement_cells = [rc for rc in requirement_cells if rc not in new_group[0]]
			fulfillment_cells = [fc for fc in fulfillment_cells if fc not in new_group[1]]

			groups.append(new_group)

		return groups

	def __getSolutions(self, board, bombs, group):
		requirement_cells = group[0]
		fulfillment_cells = group[1]

		print('requirement_cells (len={}): {}'.format(len(requirement_cells), requirement_cells))
		print('fulfillment_cells (len={}): {}'.format(len(fulfillment_cells), fulfillment_cells))

		requirements = np.mat([[1 if fc in self._getNeighbors(board, rc) else 0 
				for fc in fulfillment_cells]
			for rc in requirement_cells])
		print('Requirements: \n{}'.format(requirements))

		goal = np.mat([board[c[0]][c[1]] - len(self._getNeighbors(board, c, code='FLAGGED')) 
			for c in requirement_cells])
		print('Goal: \n{}'.format(goal))

		# For beginner board with 9 cells to fill, should be 2^9 = 512 possible solutions
		# https://stackoverflow.com/questions/14931769/how-to-get-all-combination-of-n-binary-value
		guesses = list(itertools.product([0, 1], repeat=len(fulfillment_cells)))
		print('Possible Solutions: {}'.format(len(guesses)))

		solutions = [s for s in guesses
			if sum(s) <= bombs
			and np.equal(requirements.dot(np.array(s))[0], goal).all()]

		print('Correct Solutions: {}\n(First 8...):\n{}'.format(len(solutions), solutions[:8]))

		return solutions

	def __getSolutionInfo(self, board, bombs, group, solutions):
		print('Nothing yet')

	def solution(self, solver, turn):

		groups = self.__getGroups(turn['BOARD'])
		print('Groups: {}'.format(len(groups)))
		for g in groups:
			start_time = time.time()

			print('')
			print('Next Group...')

			solutions = self.__getSolutions(turn['BOARD'], turn['BOMBS'], g)
			self.__getSolutionInfo(turn['BOARD'], turn['BOMBS'], g, solutions)

			end_time = time.time()
			print('Time taken: {}'.format(end_time - start_time))

		return [],[]
