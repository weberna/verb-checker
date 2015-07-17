##########################################################
#     	lingstructs.py
#		Various classes to hold linguistic data parsed
#		from the xml output produced by the Stanford CoreNLP
#		pipeline
############################################################
#Note that this code assumes that xml is in correct format 
#and that feature extracting assumes that all words have 
#been lowercased 
import fst

class Token:
	'Holds the data for a single token'
	def __init__(self, word, lemma, pos, tid):
		self.word = word.lower()  #lower() added 
		self.lemma = lemma
		self.pos = pos
		self.tid = tid #token id (ie position in sentence)

	def singular_noun(self):
		"""Return whether Token is singular or plural noun"""
		if self.pos == 'NNS' or self.pos == 'NNPS' or self.word in ['we', 'they']:
			return False
		else:
			return True

	def noun_person(self):
		"""If token is noun return whether token is 3rdSingular, Plural, or 1stSingular,
			return a string from the set {3rdSingular, Plural, 1stSingular}
			else return false if not a noun
		"""
		if self.word == 'i' or self.word == 'I':
			return '1stSingular'
		elif self.pos == 'NN' or self.pos == 'NNP' or self.word.lower() in ['he', 'she', 'it']:
			return '3rdSingular'
		elif self.pos == 'NNS' or self.pos == 'NNPS' or self.word.lower() in ['we', 'you', 'they']:
			return 'Plural'
		else:
			return False

	def isverb(self):
		"""Return true if token is a verb or modal verb"""
		if self.pos[0] == 'V' or self.pos == 'MD':
			return True
		else:
			return False

	#verb labels
	def get_label_new(self, subj=None, subonly=False):
		"""Return the label of the verb token"""
		p = self.pos
		label = ""
		if self.lemma == 'be':
			if subonly:  #return only subtype
				label = "be"
			else:
				label = "{}[be]".format(p)
		elif self.lemma == 'have':
			if subonly:  #return only subtype
				label = "have"
			else:
				label = "{}[have]".format(p)
		elif self.lemma == 'do':
			if subonly:  #return only subtype
				label = "do"
			else:
				label = "{}[do]".format(p)
		else:
			if subonly:  #return only subtype
				label = "main"
			else:
				label = "{}[main]".format(p)
		return label

	def isaux(self):
		"""return True if verb is auxiliary verb"""
		auxlist = ['be', 'have', 'do']
		if not self.isverb():
			return False
		elif self.lemma in auxlist or self.pos == 'MD':
			return True
		else:
			return False

	def isadverb(self):
		if self.pos[0] == 'R':
			return True
		else:
			return False

	def get_label(self, subj=None):
		p=self.pos
		label=""
		if self.lemma == 'be':
			if (self.word == 'are') or (self.word == 'were'):
				label = "{}[auxplural]".format(p)
			else:
				label = self.pos
		else:
			label = self.pos
		return label

#note that most token/token property searching methods just return a NullToken object if 
#no sutiable token/token property could be found
class NullToken(Token):
	'NullToken class represents non exsistent Tokens, use for error handeling'
	def __init__(self):
		self.word = 'None'
		self.lemma = 'None'
		self.pos = 'None'
		self.tid = -1

class VChain:
	'Represents a chain of verb Token objects'
	def __init__(self, chain, start, end):
		"""@params:
				List of Tokens chain
				int start, end - tid of where the verb chain starts (inclusive),
								 and where it ends (exclusive)
		"""
		self.chain = chain	
		self.start = start
		self.end = end
		self.length = len(self.chain)
	
	def length(self):
		return self.length
	
	def range(self):
		"""Return (start tid, end tid) tuple"""
		return (self.start, self.end)
	
	def fst_sequence(self):
		"""Return a representation of the verb chain that can be used in the fst"""
		seq = []
		for i in self.chain:
			if i.isaux():
				seq.append(i.word)
			elif i.isadverb():
				seq.append('RB')
			else:
				seq.append(i.pos)
		return seq
				
class Dependency:
	'Holds a dependency relation for tokens in a sentence'
	def __init__(self, dtype, gov, dependent):
		"""@params: 
				string dtype - type of relation
				2-Tuple gov - a tuple (governer string, idx) for governer 
				2-Tuple dependent - tuple (dependent string, idx) for dependent
		"""
		#For a list of dependency types used see http://universaldependencies.github.io/docs/en/dep/all.html
		self.dtype = dtype
		self.gov = gov 
		self.dependent = dependent

	def gov_id(self):
		return self.gov[1]

	def gov_word(self):
		return self.gov[0]

	def dependent_id(self):
		return self.dependent[1]

	def dependent_word(self):
		return self.dependent[0]

class Features:	
	'Creates and stores features for a verb Token object'
	def __init__(self, verb, s, ps=None):
		"""@params: 
			Token verb - the instance for which features are stored
			Sentence s - the sentence in which verb appears in 
			Sentence ps - previous sentence before s
		"""
		self.sentence = s
		self.instance = verb
		self.fvect = self.create_fvect2(ps) #holds all features

	def create_fvect(self, ps=None):	
		"""
			Helping method which creates the final feature vector 
			for the instance, the feature are currently:
			lemma of instance
			lemma of word right/left of instance
			subject of sentence
			pos/person/det of subject
			does sentence have passive construct?
			left/right noun person/lemma/pos
			is instance first/last in chain?
			lemma/pos/relation of governor of instance
			lemma/pos/relation of governee of instance
		"""
		fvect = []
		#extract data needed for features
		left_nonverb = closest_nonverb(self.instance, self.sentence, left=True)
		right_nonverb = closest_nonverb(self.instance, self.sentence, left=False)
		subj = self.sentence.get_subject_token()[0]
		left = self.sentence.get_token(self.instance.tid - 1)
		right = self.sentence.get_token(self.instance.tid + 1)
		leftnoun = closest_noun(self.instance, self.sentence, True)
		rightnoun = closest_noun(self.instance, self.sentence, False)
		gov_tuple = self.sentence.get_gov(self.instance.tid)
		gov_token = self.sentence.get_token(gov_tuple[1])
		governee_list = self.sentence.get_governees(self.instance.tid)
		governee_tuple = governee_list[0]
		governee_token = self.sentence.get_token(governee_tuple[1])
		prev_head = prev_vphrase(self.instance, self.sentence)
		if ps:
			prev_sen_head = prev_vphrase(ps.get_token(len(ps.sen) - 1), ps)
		else:
			prev_sen_head = NullToken()


		fvect.append(self.instance.lemma)
		fvect.append(right.lemma)
		fvect.append(left.lemma)
		fvect.append(subj.word)
		fvect.append(subj.pos)
		fvect.append(subj.noun_person())
		fvect.append(subj.singular_noun())
		fvect.append(self.sentence.get_det(subj.tid))
		fvect.append(self.sentence.ispassive())
		fvect.append(leftnoun.noun_person())
		fvect.append(rightnoun.noun_person())
		fvect.append(leftnoun.lemma)
		fvect.append(leftnoun.pos)
		fvect.append(rightnoun.lemma)
		fvect.append(rightnoun.pos)
		fvect.append(first_in_chain(self.instance, self.sentence)) #is verb first verb in chain
		fvect.append(last_in_chain(self.instance, self.sentence)) #is verb last verb in chain
		fvect.append(gov_token.lemma)
		fvect.append(gov_token.pos)
		fvect.append(gov_tuple[0])
		fvect.append(governee_token.lemma)
		fvect.append(governee_token.pos)
		fvect.append(governee_tuple[0])
		fvect.append(prev_head.pos)	
		fvect.append(prev_sen_head.pos)
		fvect.append(time_adverb(self.instance, self.sentence, False).word)
		fvect.append(time_adverb(self.instance, self.sentence, True).word)
		fvect.append(self.instance.get_label(subj)) #put label of sentence at end
		return fvect

	def create_fvect2(self, ps=None):	
		"""
			Helping method which creates the final feature vector 
			for the instance, the feature are currently:
			lemma of instance
			lemma of word right/left of instance
			subject of sentence
			pos/person/det of subject
			does sentence have passive construct?
			left/right noun person/lemma/pos
			is instance first/last in chain?
			lemma/pos/relation of governor of instance
			lemma/pos/relation of governee of instance
		"""
		fvect = []
		#extract data needed for features
		left_nonverb = closest_nonverb(self.instance, self.sentence, left=True)
		right_nonverb = closest_nonverb(self.instance, self.sentence, left=False)
		subj = self.sentence.get_subject_token()[0]
		left = self.sentence.get_token(self.instance.tid - 1)
		right = self.sentence.get_token(self.instance.tid + 1)
		leftnoun = closest_noun(self.instance, self.sentence, True)
		rightnoun = closest_noun(self.instance, self.sentence, False)
		gov_tuple = self.sentence.get_gov(self.instance.tid)
		gov_token = self.sentence.get_token(gov_tuple[1])
		governee_list = self.sentence.get_governees(self.instance.tid)
		governee_tuple = governee_list[0]
		governee_token = self.sentence.get_token(governee_tuple[1])
		prev_head = prev_vphrase(self.instance, self.sentence)
		if ps:
			prev_sen_head = prev_vphrase(ps.get_token(len(ps.sen) - 1), ps)
		else:
			prev_sen_head = NullToken()


		fvect.append(self.instance.lemma + "self")
		fvect.append(right.lemma + "right")
		fvect.append(left.lemma + "left")
		fvect.append(subj.pos + "subj")
		fvect.append(str(subj.noun_person()) + "subj")
		fvect.append(str(subj.singular_noun()) + "subj")
		fvect.append(self.sentence.get_det(subj.tid) + "det")
		fvect.append(str(self.sentence.ispassive()) + "passive")
		fvect.append(str(leftnoun.noun_person()) + "leftn")
		fvect.append(str(rightnoun.noun_person()) + "rightn")
		fvect.append(leftnoun.pos + "leftn")
		fvect.append(rightnoun.pos + "rightn")
		fvect.append(str(first_in_chain(self.instance, self.sentence)) + "firstin") #is verb first verb in chain
		fvect.append(str(last_in_chain(self.instance, self.sentence)) + "lastin") #is verb last verb in chain
		fvect.append(gov_token.word + "gov")
		fvect.append(gov_token.pos + "gov")
		fvect.append(gov_tuple[0] + "govrel")
		fvect.append(governee_token.word + "governee")
		fvect.append(governee_token.pos + "governee")
		fvect.append(governee_tuple[0] + "governeerel")
		fvect.append(prev_head.pos + "prevhead")	
		fvect.append(prev_sen_head.pos + "prevsen")
		fvect.append(str(last_in_sentence(self.instance, self.sentence)) + "lastin")
		fvect.append(time_adverb(self.instance, self.sentence, False).word + "tadverbright")
		fvect.append(time_adverb(self.instance, self.sentence, True).word + "tadverbleft")
		fvect.append(self.instance.get_label(subj)) #put label of sentence at end
		return fvect



#------------------------------------------------------------
#		Various general helping functions
#-----------------------------------------------------------
def get_aspect(vseq):
	"""Find the aspect of a verb chain vseq (represented as a list of Token objects)"""
	if len([x for x in vseq.chain if (x.isverb() and x.pos != 'MD')]) == 1: #only 1 non model verb
		aspect = 'SIMPLE'
	else:
		seq = vseq.fst_sequence()
		transducer = fst.aspect_transducer()
		aspect = " ".join(transducer.transduce(seq))
	return aspect

def last_in_sentence(tok, sentence):
	index = tok.tid
	index = index + 1	
	last = True
	while not (index >= len(sentence.sen)):
		temptok = sentence.get_token(index)
		if temptok.isverb():
			last = False
		index = index + 1
	return last

def time_adverb(tok, sentence, left=False):
		"""look for time adverb to the left/right of tok in sentence"""
		adverb_list = ['now', 'then', 'today', 'tomorrow', 'tonight', 'yesterday', 'usually', 'recently', 'sometimes', 'always']
		index = tok.tid 
		if left:
			index = index - 1
			while not (index <= 0):
				temptok = sentence.get_token(index)
				if temptok.word.lower() in adverb_list:
					return temptok
				else:
					index = index - 1
		else: #search right
			index = index + 1
			while not (index >= len(sentence.sen)):
				temptok = sentence.get_token(index)
				if temptok.word.lower() in adverb_list:
					return temptok
				else:
					index = index + 1

		return NullToken() #return null if no time adverb in sentence

	
def prev_vphrase(tok, sentence):
	"""return the token that starts the previous verb phrase in the sentence"""
	currtok = closest_nonverb(tok, sentence, True)
	while currtok.tid > 0:
		if first_in_chain(currtok, sentence):
			return currtok	
		else:
			currtok = sentence.get_token(currtok.tid - 1)
	return NullToken() #return null token if nothing found

def closest_nonverb(tok, sentence, left=False):
	"""Helping function to return the nonverb/nonadverb token that is closest to 
		tok in the Sentence object sentence.
	    If left = True, then look left, else look right
	"""
	index = tok.tid
	closest_tok = NullToken() 
	if left:
		index = index - 1
		while not (index < 0):
			temptok = sentence.get_token(index)
			if temptok.pos[0] != 'V' and temptok.pos[0] != 'R' and (str.isalpha(temptok.word) or temptok.word == '.') and temptok.pos != 'MD':
				closest_tok = temptok
				break
			index = index - 1
	else:
		index = index + 1
		while not (index > len(sentence.sen)):
			temptok = sentence.get_token(index)
			if temptok.pos[0] != 'V' and temptok.pos[0] != 'R' and (str.isalpha(temptok.word) or temptok.word == '.') and temptok.pos != 'MD':
				closest_tok = temptok
				break
			index = index + 1
	return closest_tok

def closest_noun(tok, sentence, left=False):
	"""Helping function to return the noun token that is closest to 
		tok in the Sentence object sentence.
	    If left = True, then look left, else look right
	"""
	index = tok.tid
	closest_tok = NullToken() 
	if left:
		index = index - 1
		while not (index < 0):
			temptok = sentence.get_token(index)
			if temptok.pos[0] == 'N':
				closest_tok = temptok
				break
			index = index - 1
	else:
		index = index + 1
		while not (index > len(sentence.sen)):
			temptok = sentence.get_token(index)
			if temptok.pos[0] == 'N':
				closest_tok = temptok
				break
			index = index + 1
	return closest_tok

def last_in_chain(tok, sentence):
	"""test whether the Token object tok, in the Sentence object sentence
		if the final verb in its respective verb chain
	"""
	if not tok.isverb():
		return False
	last = False
	right = sentence.get_token(tok.tid + 1)
	if not right.isverb():
		#if its an adverb, we need to see if there is a verb after it
		if right.pos[0] == 'R':
			if not sentence.get_token(right.tid + 1).isverb(): 
				last = True
		else:
			last = True
	return last
	
def first_in_chain(tok, sentence):
	"""test whether the Token object tok, in the Sentence object sentence
		if the first verb in its respective verb chain
	"""
	if not tok.isverb():
		return False
	first = False
	left = sentence.get_token(tok.tid - 1)
	if not left.isverb():
		#if its an adverb, we need to see if there is a verb before it
		if left.pos[0] == 'R':
			if not sentence.get_token(left.tid - 1).isverb(): 
				first = True
		else:
			first = True
	return first
		 
class NullFeatures(Features): #do not really need this
	'A class for features of null states'
	def __init__(self, verb, s, subj=None):
		"""sen is a sentence object, verb is the token that comes after the Null State,
			the subject of sentence can optionally be passed in for efficiency reasons"""
		self.sentence = s
		self.instance = Token('NULLSTATE', 'NULLSTATE', 'NULLSTATE', verb.tid)
		self.label = 'NULLSTATE'
		self.fvect = self.create_fvect() #holds all features

class Sentence:
	'Holds the data for a instance of a sentence parsed from the xml output of Core NLP'
	def __init__(self, s=None, d=None ):
		if not s:
			s = []
		if not d:
			d = []
		self.sen = s #sentence is a list of tokens
		self.deps = d #the dependency relations of sentence, a list of Dependency objects
	
	def get_token(self, tid): 
		"""return token given by token id, return None if out of bounds"""
		if tid > len(self.sen) or tid < 0:
			return NullToken()
		if tid == 0:
			return Token("ROOT", "ROOT", "ROOT", 0)
		else:
			tid = tid-1
			return self.sen[tid]

	def add_word(self, token):
		"""Append a token to the sentence"""
		self.sen.append(token)

	def add_dep(self, dep):
		self.deps.append(dep)
	
	def dep_tostring(self):
		"""Print the dependency relations in the sentence"""
		for i in self.deps:
			print("{}({}, {})".format(i.dtype, i.gov, i.dependent))

	def tostring(self):
		"""Return a single string representation of the words in the sentence"""
		return " ".join([x.word for x in self.sen])
	
	def token_tostring(self):
		"""Return a string with all infomation for each token, not just the word"""
		return " ".join("[{}, {}, {}, {}]".format(x.word, x.lemma, x.pos, x.tid) for x in self.sen)
	
	def get_subject_list(self): #do not use this method
		"""Return a list of indices of the subject tokens of the sentence"""
		subs = []
		for i in self.deps:
			if i.dtype == 'nsubj' or i.dtype == 'nsubjpass' or i.dtype == 'expl': 
				subs.append(i.dependent_id())
		return list(subs)

	def ispassive(self):
		"""return true if there is a passive contruct in sentence"""
		p = False	
		for d in self.deps:
			if d.dtype == 'nsubjpass' or d.dtype == 'csubjpass':
				passive = True
				break
		return p

	def get_subject_token(self):
		"""Return a list of the subject tokens of the sentence"""
		subs = []
		for i in self.deps:
			if i.dtype == 'nsubj' or i.dtype == 'nsubjpass' or i.dtype == 'expl': 
				subs.append(self.get_token(i.dependent_id()))
		if not subs:
			subs.append(NullToken())
		return list(subs)

	def get_root(self):
		"""Return the root of the sentence as a Token object"""
		root = 'None'
		for i in self.deps:
			if i.dtype == 'root':
				root = self.get_token(i.dependent_id())
				break	
		return root

	def get_governees(self, token_index):
		"""Return the a list of governees and relations of the token 
			with tid equal to token index
			@ret: list of 2-Tuples with form (relation type, governee id)
		"""
		governees = []
		for i in self.deps:
			if i.gov_id() == token_index:
				governees.append((i.dtype, i.dependent_id()))
		if not governees: #no governees for token
			return [('None', -1)]	
		else:
			return governees

	def get_gov(self, token_index): #note that all tokens have a single governor (which may be ROOT)
		"""Return the governor of the token with tid equal to token_index
			as well as its relation type.
			@ret: 2-Tuple - (relation type, governor index) 
		"""
		for i in self.deps:
			if i.dependent_id() == token_index:
				return (i.dtype, i.gov_id())
		print("Token not found in sentence")
		return False

	def get_det(self, token_index):
		"""Return the determiner (surface form) for the token with given index,
			else return False"""
		for i in self.deps:
			if i.dtype == 'det' and i.gov_id() == token_index:
				return i.dependent_word()
		return 'None'

	def get_vchains(self):
		"""Return list of VChain objects for all verb chains in the sentence"""
		chains = []
		started = False #whether we have started building chain
		for tok in self.sen:
			if not started:
				poss = []
			if tok.isverb() or tok.isadverb():
				started = True
				poss.append(tok)
			else:
				started = False
				if poss and not (len(poss) == 1 and poss[0].isadverb()): #check for possible chain that is not just a single adverb 
					chain = VChain(list(poss), poss[0].tid, poss[len(poss)-1].tid)
					chains.append(chain)
		return chains
					

	


