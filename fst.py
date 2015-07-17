#A simple finite state transducer class

class Fst:
	'Finite state transducer - assume state 1 is start state and 0 is "error" state'
	def __init__(self, input_alpha, state_outputs, transitions):
		"""@params:
				list input_alpha - list of symbols that can be used as input (note order does matter, 
								   the ith symbol in list is ith column in transition table
				list state_outputs - the ith element in this list gives what is outputted when ith state is
									 transitioned to (use None for no output)
				list of lists transitions - ith element of the list gives a list of transitions for the ith state, 
											the jth element in this list gives the index of the state to transition 
											to when the jth input symbol is read in, the last element is the 'empty' transistion
											(can automatically transition with no input required, put 0 to indicate no 'empty' transition)
		"""
		self.inputs = input_alpha
		self.outputs = state_outputs
		self.trans = transitions
		self.curr_state = 1

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
				print("{} is not a valid input symbol".format(i))
				return out 
			else:
				input_index = self.inputs.index(i)
				out = out + self.transition(input_index)

			if self.curr_state == 0: #reached error state
				return out
		return out

#if __name__ == "__main__":
def aspect_transducer():
	"""Return a transducer that takes in inputs of auxiliary verbs and form of main verb and outputs tense/aspect"""
	#          0     1       2       3     4     5       6     7     8        9     10    11    12     13      14      15
	inputs = ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ', 'RB', 'had', 'have', 'has', 'is', 'am', 'are', 'was', 'were', 'been']

	outputs = ['ERROR', None, 'SIMPLE', 'PAST', '1ST', '3RD', '1ST', '3RD', 'PLURAL', 'PRESENT', 
			   'SINGULAR', 'PLURAL', 'PAST', 'PERFECT', None, 'PERFECT PROGRESSIVE', 'PROGRESSIVE'] 
	
	trans = [[] for x in range(len(outputs))] #init transition table to all zeros

	trans[0] = [0]*(len(inputs) + 1)
	trans[1] = [2, 2, 2, 2, 2, 2, 1, 3, 4, 5, 7, 6, 8, 10, 11, 0, 0]
	trans[2] = [0]*(len(inputs) + 1)
	trans[2][6] = 2
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
	trans[9][6] = 9

	trans[10] = [0]*(len(inputs) + 1)
	trans[10][16] = 12 

	trans[11] = [0]*(len(inputs) + 1)
	trans[11][16] = 12 

	trans[12] = [0]*(len(inputs) + 1)
	trans[12][2] = 16
	trans[12][6] = 12

	trans[13] = [0]*(len(inputs) + 1)
	trans[13][6] = 13

	trans[14] = [0]*(len(inputs) + 1)
	trans[14][2] = 15	
	trans[14][6] = 14

	trans[15] = [0]*(len(inputs) + 1)
	trans[15][6] = 15

	trans[16] = [0]*(len(inputs) + 1)
	trans[16][6] = 16

	transducer = Fst(inputs, outputs, trans)				
	return transducer


		
			
											
				                            




