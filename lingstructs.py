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
from nltk.corpus import verbnet

class Token:
	'Holds the data for a single token'
	def __init__(self, word, lemma, pos, tid, delim=False):
		self.word = word.lower()  #lower() added 
		self.lemma = lemma
		self.pos = pos
		self.tid = tid #token id (ie position in sentence)
		self.in_delim = delim #whether or not this token is in a delimited (error) phrase 

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
#			return 'FirstSingular'
			return '1stSingular'
		elif self.pos == 'NN' or self.pos == 'NNP' or self.word.lower() in ['he', 'she', 'it']:
#			return 'ThirdSingular'
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
	
	def abbv_to_word(self):
		"""Convert abbreviated words (ie 'nt, 've 'd) to there word form"""
		if self.word == "'m":
			return 'am'
		elif self.word == "'ve":
			return 'have'
		elif self.word == "'s":
			return 'is'
		elif self.word == "'re":
			return 'are'
		elif self.word == "'d":
			return 'would'
		else:
			return self.word

	def copy(self):
		return Token(self.word, self.lemma, self.pos, self.tid, self.in_delim)

	#verb labels
	def get_label_new(self):
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

	def get_label(self):
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
	def __init__(self, chain, start=None, end=None, position=-1,):
		"""@params:
				List of Tokens chain
				int start, end - tid of where the verb chain starts (inclusive),
								 and where it ends (exclusive)
		"""
		if start == None:
			start = chain[0].tid
		if end == None:
			end = chain[len(chain)-1].tid
		self.chain = chain	
		self.start = start
		self.end = end
		self.position = position #what number verb chain it is in the sentence
		self.length = len(self.chain)
	
	def length(self):
		return self.length
	
	def range(self):
		"""Return (start tid, end tid) tuple"""
		return (self.start, self.end)
	
	def tostring(self):
		return " ".join([x.word for x in self.chain])
	
	def first(self):
		return self.chain[0]
	
	def last(self):
		return self.chain[self.length - 1]

	def head(self):
		"""Return head of verb chain (return the last verb pretty much)"""
		found = False
		for i in self.chain:
			if i.isverb():
				found = True
				head = i
		if not found:
			head = self.last()
		return head

	def fst_sequence(self):
		"""Return a representation of the verb chain that can be used in the fst"""
		seq = []
		other_aux = ['be', 'being', 'having', 'doing']	
		for i in self.chain:
			if i.isaux() and i.pos != 'MD' and (i not in other_aux):
				seq.append(i.abbv_to_word())
			elif (not i.isadverb() or (i in other_aux) or i.tid == self.head().tid) and i.pos != 'MD':
				seq.append(i.pos)
		return seq

class CorrectionPair:
	'Represents a error annotated verb phrase and its corresponding correction (for P(O|C,S))'
	def __init__(self, error, corr):
		"""@params: (VChain) error, corr"""
		self.error = error
		self.correction = corr
	
	def tostring(self):
		return "{} -> {}".format(self.error.tostring(), self.correction.tostring())	
				
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

class CorrectionFeatures:	
	'Creates and stores features for a verb phrase error and correction (for the P(O | C, S) part of model)'
	def __init__(self, pair, s):
		"""@params: 
			CorrectionPair pair 	
			Sentence s - the sentence in which verb appears in 
		"""
		self.sentence = s
		self.instance = pair
		self.fvect = self.create_fvect() #holds all features

	def create_fvect(self):	
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
		corr = self.instance.correction
		error = self.instance.error
		#extract data needed for features
		subj = self.sentence.get_subject_token()[0]
		left = self.sentence.get_token(error.first().tid - 1)
		right = self.sentence.get_token(error.last().tid + 1)
		leftnoun = closest_noun(error.first(), self.sentence, True)
		rightnoun = closest_noun(error.last(), self.sentence, False)
		gov_tuple = self.sentence.get_gov(error.head().tid)
		gov_token = self.sentence.get_token(gov_tuple[1])
		governee_list = self.sentence.get_governees(error.head().tid)
		governee_tuple = governee_list[0]
		governee_token = self.sentence.get_token(governee_tuple[1])
		prevphrase = prev_vphrase(error, self.sentence)
		if prevphrase:
			prevhead = prevphrase.head()
			c = verbnet.classids(prevhead.lemma)
			if not c:	
				prevclass = 'NoPrevClass'
			else:
				prevclass = c[0] 
			prevaspect = get_aspect(prevphrase)
		else:
			prevhead = NullToken()
			prevclass = 'NoPrevClass'
			prevaspect = 'NoPrevAspect'
		vnet_class = verbnet.classids(error.head().lemma)


#		fvect.append(get_aspect(corr) + "corrAspect")
#		fvect.append(corr.head().word + "self")
		

		fvect.append(get_aspect(error) + "corrAspect")
		fvect.append(error.head().word + "self")

		fvect.append(prevhead.lemma + "prevword")
		fvect.append(prevhead.pos + "prevpos")
		fvect.append(prevclass)
		fvect.append(prevaspect + "prevaspect")

		fvect.append(right.word + "right")
		fvect.append(right.pos + "right")
		fvect.append(left.word + "left")
		fvect.append(left.pos + "left")
		fvect.append(subj.pos + "subj")
		fvect.append(subj.lemma + "subjlem")
		fvect.append(str(subj.noun_person()) + "subj")
		fvect.append(str(subj.singular_noun()) + "subj")
		fvect.append(self.sentence.get_det(subj.tid) + "det")
		fvect.append(str(self.sentence.ispassive()) + "passive")
		fvect.append(str(leftnoun.noun_person()) + "leftn")
		fvect.append(str(rightnoun.noun_person()) + "rightn")
		fvect.append(leftnoun.pos + "leftn")
		fvect.append(rightnoun.pos + "rightn")
		fvect.append(gov_token.word + "gov")
		fvect.append(gov_token.pos + "gov")
		fvect.append(gov_tuple[0] + "govrel")
		fvect.append(governee_token.word + "governee")
		fvect.append(governee_token.pos + "governee")
		fvect.append(governee_tuple[0] + "governeerel")
		fvect.append(time_adverb(error.last(), self.sentence, False).word + "tadverbright")
		fvect.append(time_adverb(error.first(), self.sentence, True).word + "tadverbleft")

#		if get_aspect(error) and get_aspect(corr) and get_aspect(corr) != 'ERROR':
#			fvect.append(get_aspect(error)) #label
		if get_aspect(corr) and get_aspect(error) and get_aspect(error) != 'ERROR':
			fvect.append(get_aspect(corr)) #label
		else:
			fvect.append('ERROR')

		return fvect

class Features:	
	'Creates and stores features for a normal Verb Chain object (for P(C|S))'
	def __init__(self, phrase, s):
		"""@params: 
			VChain phrase - the instance for which features are stored
			Sentence s - the sentence in which verb appears in 
		"""
		self.sentence = s
		self.instance = phrase 
		self.fvect = self.create_fvect() #holds all features

	def create_fvect(self):	
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
		subj = self.sentence.get_subject_token()[0]
		left = self.sentence.get_token(self.instance.first().tid - 1)
		left2 = self.sentence.get_token(self.instance.first().tid - 2)
		right = self.sentence.get_token(self.instance.last().tid + 1)
		right2 = self.sentence.get_token(self.instance.last().tid + 2)
		leftnoun = closest_noun(self.instance.first(), self.sentence, True)
		rightnoun = closest_noun(self.instance.last(), self.sentence, False)
		gov_tuple = self.sentence.get_gov(self.instance.head().tid)
		gov_token = self.sentence.get_token(gov_tuple[1])
		governee_list = self.sentence.get_governees(self.instance.head().tid)
		governee_tuple = governee_list[0]
		governee_token = self.sentence.get_token(governee_tuple[1])

		prevphrase = prev_vphrase(self.instance, self.sentence)
		if prevphrase:
			prevhead = prevphrase.head()
			c = verbnet.classids(prevhead.lemma)
			if not c:	
				prevclass = 'NoPrevClass'
			else:
				prevclass = c[0] 
			prevaspect = get_aspect(prevphrase)
		else:
			prevhead = NullToken()
			prevclass = 'NoPrevClass'
			prevaspect = 'NoPrevAspect'
		vnet_class = verbnet.classids(self.instance.head().lemma)





		fvect.append(self.instance.head().word + "self")
		fvect.append(chr(self.instance.length + 65) + "len")
		fvect.append(right.word + "right")
		fvect.append(left.word + "left")
		fvect.append(right.pos + "right")
		fvect.append(left.pos + "left")
		fvect.append(right2.word + "right")
		fvect.append(left2.word + "left")
		fvect.append(right2.pos + "right")
		fvect.append(left2.pos + "left")

		fvect.append(prevhead.lemma + "prevword")
		fvect.append(prevhead.pos + "prevpos")
		fvect.append(prevclass)
		fvect.append(prevaspect + "prevaspect")





		fvect.append(subj.pos + "subj")
		fvect.append(subj.lemma + "subjlem")
		fvect.append(str(subj.noun_person()) + "subj")
		fvect.append(str(subj.singular_noun()) + "subj")
		fvect.append(self.sentence.get_det(subj.tid) + "det")
		fvect.append(str(self.sentence.ispassive()) + "passive")
		fvect.append(str(leftnoun.noun_person()) + "leftn")
		fvect.append(str(rightnoun.noun_person()) + "rightn")
		fvect.append(leftnoun.pos + "leftn")
		fvect.append(rightnoun.pos + "rightn")
		fvect.append(gov_token.word + "gov")
		fvect.append(gov_token.pos + "gov")
		fvect.append(gov_tuple[0] + "govrel")
		fvect.append(governee_token.word + "governee")
		fvect.append(governee_token.pos + "governee")
		fvect.append(governee_tuple[0] + "governeerel")
		fvect.append(time_adverb(self.instance.last(), self.sentence, False).word + "tadverbright")
		fvect.append(time_adverb(self.instance.first(), self.sentence, True).word + "tadverbleft")

		if get_aspect(self.instance):
			fvect.append(get_aspect(self.instance)) #label
		else:
			fvect.append('ERROR')
		return fvect


	def create_fvect2(self):	
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
		subj = self.sentence.get_subject_token()[0]
		left = self.sentence.get_token(self.instance.first().tid - 1)
		left2 = self.sentence.get_token(self.instance.first().tid - 2)
		left3 = self.sentence.get_token(self.instance.last().tid - 3)
		left4 = self.sentence.get_token(self.instance.last().tid - 4)
		right = self.sentence.get_token(self.instance.last().tid + 1)
		right2 = self.sentence.get_token(self.instance.last().tid + 2)
		right3 = self.sentence.get_token(self.instance.last().tid + 3)
		right4 = self.sentence.get_token(self.instance.last().tid + 4)
		leftnoun = closest_noun(self.instance.first(), self.sentence, True)
		rightnoun = closest_noun(self.instance.last(), self.sentence, False)
		gov_tuple = self.sentence.get_gov(self.instance.head().tid)
		gov_token = self.sentence.get_token(gov_tuple[1])
		governee_list = self.sentence.get_governees(self.instance.head().tid)
		governee_tuple = governee_list[0]
		governee_token = self.sentence.get_token(governee_tuple[1])
	
		vnet_classes = verbnet.classids(self.instance.head().lemma)
		if not vnet_classes:
			vnet_class = 'NoClass'
		else:
			vnet_class = vnet_classes[0]
			vnet_class = "".join([x for x in vnet_class if str.isalpha(x)])

		prevphrase = prev_vphrase(self.instance, self.sentence)
		if prevphrase:
			prevhead = prevphrase.head()
			c = verbnet.classids(prevhead.lemma)
			if not c:	
				prevclass = 'NoPrevClass'
			else:
				prevclass = c[0] 
			prevaspect = get_aspect(prevphrase)
		else:
			prevhead = NullToken()
			prevclass = 'NoPrevClass'
			prevaspect = 'NoPrevAspect'

		fvect.append(self.instance.head().word + "self")
		fvect.append(vnet_class + "class")
#		fvect.append(chr(self.instance.length + 65) + "len")
		fvect.append(right.word + "right")
		fvect.append(left.word + "left")
		fvect.append(right.pos + "right")
		fvect.append(left.pos + "left")

		fvect.append(right2.word + "right")
		fvect.append(left2.word + "left")
		fvect.append(right2.pos + "right")
		fvect.append(left2.pos + "left")

		fvect.append(right3.word + "right")
		fvect.append(left3.word + "left")
		fvect.append(right3.pos + "right")
		fvect.append(left3.pos + "left")

		fvect.append(right4.word + "right")
		fvect.append(left4.word + "left")
		fvect.append(right4.pos + "right")
		fvect.append(left4.pos + "left")

		fvect.append(prevhead.lemma + "prevword")
		fvect.append(prevhead.pos + "prevpos")
#		fvect.append(prevclass)
		fvect.append(prevaspect + "prevaspect")

		fvect.append(subj.pos + "subj")
		fvect.append(subj.word + "subjword")
		fvect.append(str(subj.noun_person()) + "subj")
#		fvect.append(str(subj.singular_noun()) + "subj")
		fvect.append(self.sentence.get_det(subj.tid) + "det")
		fvect.append(str(self.sentence.ispassive()) + "passive")
#		fvect.append(str(leftnoun.noun_person()) + "leftn")
#		fvect.append(str(rightnoun.noun_person()) + "rightn")
#		fvect.append(leftnoun.pos + "leftn")
#		fvect.append(rightnoun.pos + "rightn")
		fvect.append(gov_token.word + "gov")
		fvect.append(gov_token.pos + "gov")
		fvect.append(gov_tuple[0] + "govrel")
		fvect.append(governee_token.word + "governee")
		fvect.append(governee_token.pos + "governee")
		fvect.append(governee_tuple[0] + "governeerel")
#		fvect.append(time_adverb(self.instance.last(), self.sentence, False).word + "tadverbright")
#		fvect.append(time_adverb(self.instance.first(), self.sentence, True).word + "tadverbleft")

		if get_aspect(self.instance):
			fvect.append(get_aspect(self.instance)) #label
		else:
			fvect.append('ERROR')
		return fvect

#------------------------------------------------------------
#		Various general helping functions
#-----------------------------------------------------------
def get_aspect(vseq):
	"""Find the aspect of a verb chain vseq (represented as VChain object)"""
	filtered = [x for x in vseq.chain if (x.isverb() and x.pos != 'MD')]
	if vseq.first().pos == 'TO' and vseq.length > 1:
		aspect = 'INF'
	elif len(filtered) == 1: #only 1 non model verb
		if filtered[0].pos == 'VBD' or filtered[0].pos == 'VBN':	
			aspect = 'PA_SIMPLE'
		else:
			aspect = 'PR_SIMPLE'
	else:
		seq = vseq.fst_sequence()
		transducer = fst.forgiving_aspect_transducer()
		aspect_list = transducer.transduce(seq)
		if 'ERROR' in aspect_list:
			aspect = 'ERROR'
		else:
			temp = ['PL', 'SING', '1ST', '3RD'] #these two lines added for testing
			aspect_list = [x for x in aspect_list if x not in temp]
			
			aspect = "_".join(aspect_list)
	return aspect

def generate_aspect(seq):
	transducer = fst.aspect_generator()
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
		adverb_list = ['now', 'then', 'today', 'tomorrow', 'tonight', 'yesterday', 'usually', 
						'later', 'yet', 'still', 'already' 'recently', 'sometimes', 'always', 'ago']
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
	
def prev_vphrase(vphrase, sentence):
	"""return the previous verb phrase"""
	chains = sentence.get_vchains()
	if vphrase.position == 0:
		if sentence.prev and sentence.prev.get_vchains():
			prevchains = sentence.prev.get_vchains()
			return prevchains[len(prevchains) - 1] 
		else:
			return None
	elif vphrase.position > 0:
		return chains[vphrase.position - 1]
	else:
		return None
		
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
	def __init__(self, s=None, d=None, pairs=None, prev=None):
		if not s:
			s = []
		if not d:
			d = []
		if not pairs:
			pairs = []
		self.sen = s #sentence is a list of tokens
		self.deps = d #the dependency relations of sentence, a list of Dependency objects
		self.corr_pairs = pairs
		self.prev = prev #previous sentence
	
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
	
	def add_pair(self, pair):
		"""Add a correction pair to the sentence's corr_pairs list
			@params: CorrectionPair pair
		"""
		self.corr_pairs.append(pair)
	
	def add_pairs(self, pairs):
		"""Like add_pair but adds a list of CorrectionPairs to corr_pairs"""
		self.corr_pairs = self.corr_pairs + pairs
	
	def print_pairs(self):
		"""Print correction pairs of sentence"""
		for i in self.corr_pairs:
			print(i.tostring())
	
	def isdelimited(self):
		if self.corr_pairs:
			return True
		else:
			return False

	def get_vchains(self):
		"""Return list of VChain objects for all verb chains in the sentence"""
		chains = []
		started = False #whether we have started building chain
		num_chains = 0
		for tok in self.sen:
			if not started:
				poss = []  #possible chain
			if tok.isverb() or tok.isadverb() or ((not started) and tok.word == 'to' and self.get_token(tok.tid + 1).isverb()): #only accept 'to' if at start of chain 
				started = True
				poss.append(tok)
			else:
				started = False
				#check for possible chain that is not just a single adverb, a 'to' or single modal
				if poss and not (len(poss) == 1 and (poss[0].isadverb() or poss[0].pos == 'TO' or poss[0].pos == 'MD')): 
					chain = VChain(list(poss), poss[0].tid, poss[len(poss)-1].tid, num_chains)
					chains.append(chain)
					num_chains = num_chains + 1
				if tok.pos == 'TO' and self.get_token(tok.tid + 1).isverb(): #if current token is 'to' add it to the start of new chain
					poss = [tok]
					started = True
		return chains
				
	def get_feats(self, corr=True):
		"""Return a list of Correction Features for all verb chains in sentence, if a verb chain is 
			already correct, then its correction is the same as the error, only return features for instances 
			where the correction is equal to the verb chain
			@params:
				corr - Whether to return features as CorrectionFeatures as opposed to regular Features
		"""
		ret = []
		corr_stack = list(self.corr_pairs)
		corr_stack.reverse()
		for c in self.get_vchains():
			if all(x.in_delim for x in c.chain) and corr_stack: #if verb phrase is an error use the correct label
				if corr_stack[len(corr_stack)-1].error.tostring() == c.tostring(): #only add data where the verb chain and error annotation match
					corrfeats = CorrectionFeatures(corr_stack.pop(), self)
					if corr:
						feats = corrfeats
					else:
						feats = Features(c, self)
						if corrfeats.fvect[len(corrfeats.fvect) - 1] == 'ERROR': #if the correction is error, mark this in regular feat vect
							feats.fvect[len(feats.fvect) - 1] = 'ERROR'
					ret.append(feats)
				else:
					corr_stack.pop()  #just dont use this correction instance if the verb chain/error annotation doesnt match
			else:
				corrfeats = CorrectionFeatures(CorrectionPair(c, c), self)
				if corr:
					feats = corrfeats
				else:
					feats = Features(c, self)
					if corrfeats.fvect[len(corrfeats.fvect) -1] == 'ERROR': #if the correction is error, mark it in regular feat vect
						feats.fvect[len(feats.fvect) - 1] = 'ERROR'
				ret.append(feats)
		return ret
				
			
