#A simple finite state transducer class

class Fst:
	'Finite state transducer (output upon reaching state) - assume state 1 is start state and 0 is "dead" state'
	#A transistion to state -1 indicates 'Do Nothing'
	def __init__(self, input_alpha, state_outputs, transitions, end_states=None):
		"""@params:
				list input_alpha - list of symbols that can be used as input (note order does matter, 
								   the ith symbol in list is ith column in transition table)
				list state_outputs - the ith element in this list gives what is outputted when ith state is
									 transitioned to (use None for no output), outputs correspond to states
				list of lists transitions - ith row of the 2d array gives a list of transitions for the ith state, 
										the jth element in this list gives the index of the state to transition 
										to when the jth input symbol is read in, the last element is the 'empty' transistion
										(can automatically transition with no input required, put 0 to indicate no 'empty' transition for that state)
										Transitioning to state -1 indicates a state is transitioning to itself and that nothing should
										be outputted on this transition.
				list end_states - a list a state indices that are valid ending states, default to all states
		"""
		self.inputs = input_alpha
		self.outputs = state_outputs
		self.trans = transitions
		self.curr_state = 1
		if end_states:
			self.end_states = end_states
		else:
			self.end_states = [x for x in range(1, len(self.outputs))]

	def has_empty_trans(self, state):
		"""return true is given state has a empty transistion"""
		if self.trans[state][len(self.inputs)] != 0:
			return True
		else:
			return False

	def transition(self, input_index):
		"""input index correspondes to indices of inputs array"""
		out = []
		new_state = self.trans[self.curr_state][input_index]
		if new_state == -1: #a 'Do Nothing' transition
			return [""]
		
		self.curr_state = new_state
		if self.outputs[new_state]: #if transition to new state produces output, add to list
			out.append(self.outputs[new_state])
			if self.has_empty_trans(self.curr_state): 
				out = out + self.transition(len(self.inputs)) #do empty transition
		return out

	def transduce(self, symbols):
		"""Run the input symbols through fst and return outputs from states
			@params:
				list symbols - list of input symbols
			@ret:
				list of output symbols
		"""
		out = []
		for i in symbols:
			if i not in self.inputs:
#				print("{} {} {} is not a valid input symbol".format(i, out, symbols))
				#return out 
				return ['ERROR']
			else:
				input_index = self.inputs.index(i)
				out = out + self.transition(input_index)

			if self.curr_state == 0: #reached error state
				return out

		if self.curr_state in self.end_states:
			return out
		else:
			return ['ERROR']

def vchain_transducer():
	"""Return a transducer that takes in inputs of auxiliary verbs and form of main verb and outputs tense/aspect and person/number of the verb chain"""
	#          0     1       2       3     4     5       6     7     8        9     10    11    12     13      14      15      
	inputs = ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ', 'RB', 'had', 'have', 'has', 'is', 'am', 'are', 'was', 'were', 'been']

	outputs = ['ERROR', None, 'SIMPLE', 'PA', '1ST', '3RD', '1ST', '3RD', 'PL', 'PR', 
			   'SING', 'PL', 'PA', 'PER', None, 'PERPROG', 'PROG'] 
	
	trans = [[] for x in range(len(outputs))] #init transition table to all zeros

	trans[0] = [0]*(len(inputs) + 1)
	trans[1] = [2, 2, 2, 2, 2, 2, 1, 3, 4, 5, 7, 6, 8, 10, 11, 0, 0]
	trans[2] = [0]*(len(inputs) + 1)
	trans[2][6] = -1 
	trans[3] = [0, 0, 0, 13, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 14, 0]

	trans[4] = [0]*(len(inputs) + 1)
	trans[4][15] = 14
	trans[4][3] = 13

	trans[5] = [0]*(len(inputs) + 1)
	trans[5][15] = 14
	trans[5][3] = 13

	trans[6] = [0]*(len(inputs) + 1)
	trans[6][16] = 9 

	trans[7] = [0]*(len(inputs) + 1)
	trans[7][16] = 9 

	trans[8] = [0]*(len(inputs) + 1)
	trans[8][16] = 9 

	trans[9] = [0]*(len(inputs) + 1)
	trans[9][2] = 16
	trans[9][6] = -1 

	trans[10] = [0]*(len(inputs) + 1)
	trans[10][16] = 12 

	trans[11] = [0]*(len(inputs) + 1)
	trans[11][16] = 12 

	trans[12] = [0]*(len(inputs) + 1)
	trans[12][2] = 16
	trans[12][6] = -1 

	trans[13] = [0]*(len(inputs) + 1)
	trans[13][6] = -1

	trans[14] = [0]*(len(inputs) + 1)
	trans[14][2] = 15	
	trans[14][6] = -1

	trans[15] = [0]*(len(inputs) + 1)
	trans[15][6] = -1

	trans[16] = [0]*(len(inputs) + 1)
	trans[16][6] = -1

	transducer = Fst(inputs, outputs, trans)				
	return transducer

def forgiving_vchain_transducer():
	"""Just like regular vchain transducer but a little more forgiving (ie try to guess the tense/aspect if input is not entirly correct)"""
	#          0     1       2       3     4     5       6     7     8        9     10    11    12     13      14      15     16    17     18
	inputs = ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ', 'RB', 'had', 'have', 'has', 'is', 'am', 'are', 'was', 'were', 'been', 'do', 'did', 'does']

	outputs = ['ERROR', None, 'SIMPLE', 'PA', '1ST', '3RD', '1ST', '3RD', 'PL', 'PR', 
			   'SING', 'PL', 'PA', 'PER', None, 'PERPROG', 'PROG', 'PR', 'PA', 'PROG', 'DID'] 
	
	ends = [2, 13, 15, 16, 20]
	trans = [[] for x in range(len(outputs))] #init transition table to all zeros

	trans[0] = [0]*(len(inputs) + 1)
	trans[1] = [2, 2, 2, 2, 2, 2, 1, 3, 4, 5, 7, 6, 8, 10, 11, 0, 17, 18, 19, 0]
	trans[2] = [0]*(len(inputs) + 1)
	trans[2][6] = -1 
	trans[3] = [13, 13, 13, 13, 13, 13, 3, 0, 0, 0, 0, 0, 0, 0, 0, 14, 0, 0, 0, 0]

	trans[4] = [0]*(len(inputs) + 1)
	trans[4][15] = 14
	trans[4][:6] = [13 for x in range(6)]

	trans[5] = [0]*(len(inputs) + 1)
	trans[5][15] = 14
	trans[5][:6] = [13 for x in range(6)]

	trans[6] = [0]*(len(inputs) + 1)
	trans[6][len(inputs)] = 9 

	trans[7] = [0]*(len(inputs) + 1)
	trans[7][len(inputs)] = 9 

	trans[8] = [0]*(len(inputs) + 1)
	trans[8][len(inputs)] = 9 

	trans[9] = [0]*(len(inputs) + 1)
	trans[9][:6] = [16 for x in range(6)]
	trans[9][6] = -1 

	trans[10] = [0]*(len(inputs) + 1)
	trans[10][len(inputs)] = 12 

	trans[11] = [0]*(len(inputs) + 1)
	trans[11][len(inputs)] = 12 

	trans[12] = [0]*(len(inputs) + 1)
	trans[12][:6] = [16 for x in range(6)]
	trans[12][6] = -1 

	trans[13] = [0]*(len(inputs) + 1)
	trans[13][6] = -1

	trans[14] = [0]*(len(inputs) + 1)
	trans[14][:6] = [15 for x in range(6)]
	trans[14][6] = -1

	trans[15] = [0]*(len(inputs) + 1)
	trans[15][6] = -1

	trans[16] = [0]*(len(inputs) + 1)
	trans[16][6] = -1

	trans[17] = [0]*(len(inputs) + 1)
	trans[17][:6] = [20 for x in range(6)]
	trans[17][6] = -1

	trans[18] = [0]*(len(inputs) + 1)
	trans[18][:6] = [20 for x in range(6)]
	trans[18][6] = -1

	trans[19] = [0]*(len(inputs) + 1)
	trans[19][:6] = [20 for x in range(6)]
	trans[19][6] = -1

	trans[20] = [0]*(len(inputs) + 1)
	trans[20][6] = -1

	transducer = Fst(inputs, outputs, trans, ends)				
	return transducer

def vchain_generator():
	"""Return transducer which takes in as input a phrase and desired properties and returns a modified version of the
		phrase in the tense/aspect/person/number desired"""
    #Dont use this, not entirly correct
	#          0        1       2           3       4       5            6           7                         8      9    
	inputs = ['1ST', '3RD', 'SINGULAR', 'PLURAL', 'PAST', 'PRESENT', 'PERFECT', 'PERFECT PROGRESSIVE', 'PROGRESSIVE', '']
	#           0        1    2      3       4         5       6       7   8        9   10    11     12     13     14    15      16    17
	outputs = ['ERROR', None, None, 'have', 'VBN', 'been VBG', 'am', 'VBG', None, 'has', 'is', None, 'was', None, 'are', 'were', None, 'had']	
		
	trans = [[] for x in range(len(outputs))] #init transition table to all zeros

	trans[0] = [0]*(len(inputs) + 1)
	trans[1] = [2, 8, 11, 13, 0, 0, 0, 0, 0, 16, 0]
	trans[2] = [0]*(len(inputs) + 1)
	trans[2][5] = 6 
	trans[2][9] = 3 

	trans[3] = [0]*(len(inputs) + 1)
	trans[3][6] = 4
	trans[3][7] = 5

	trans[4] = [0]*(len(inputs) + 1)

	trans[5] = [0]*(len(inputs) + 1)

	trans[6] = [0]*(len(inputs) + 1)
	trans[6][8] = 7 

	trans[7] = [0]*(len(inputs) + 1)

	trans[8] = [0]*(len(inputs) + 1)
	trans[8][5] = 10 
	trans[8][9] = 9 

	trans[9] = [0]*(len(inputs) + 1)
	trans[9][6] = 4
	trans[9][7] = 5

	trans[10] = [0]*(len(inputs) + 1)
	trans[10][8] = 7 

	trans[11] = [0]*(len(inputs) + 1)
	trans[11][4] = 12 

	trans[12] = [0]*(len(inputs) + 1)
	trans[12][8] = 7

	trans[13] = [0]*(len(inputs) + 1)
	trans[13][4] = 15
	trans[13][5] = 14 

	trans[14] = [0]*(len(inputs) + 1)
	trans[14][8] = 7	

	trans[15] = [0]*(len(inputs) + 1)
	trans[15][8] = 7 

	trans[16] = [0]*(len(inputs) + 1)
	trans[16][4] = 17 

	trans[17] = [0]*(len(inputs) + 1)
	trans[17][6] = 4
	trans[17][7] = 5

	transducer = Fst(inputs, outputs, trans)				
	return transducer


