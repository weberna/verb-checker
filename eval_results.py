###################################################
#         eval_results.py
#    Module that evaluates the corrections made
#    on FCE data and checks it aginst fce data set
#    and returns recall, precision and f-score.
###################################################
from lingstructs import *
import process_data as pd
import lxml.etree as xml
import sys

def read_fce_xml(datafile, corrected=True, delimited=False):
	"""Read the the fce xml file from datafile and return the text data
		as a string. If corrected is True, return the data with verb errors corrected
		else return original, possibly incorrect data
		TODO: Take out delimited options, now has its own method
	"""
	sents = []
	xfile = open(datafile, 'r')
	data = xml.parse(xfile)
	root = data.getroot()
	strdata = ""
	if corrected:
		for p in root.iter('p'):
			strdata = strdata + get_vcorrected(p, delimited) + " "
	else:
		for p in root.iter('p'):
			strdata = strdata + get_original(p) + " "
	return strdata

def create_delimited(datafile):
	"""Create String data for training from fce xml documents"""
	sents = []
	xfile = open(datafile, 'r')
	data = xml.parse(xfile)
	root = data.getroot()
	strdata = ""
	for p in root.iter('p'):
		strdata = strdata + delimit_data(p) + " "
	return strdata

def delimit_data(elm):
	"""Get String data for training (delimit errors with @@ and corrections with $$)"""
	if elm.tag == 'NS':
		err = elm.get('type')
		if err == 'AGV' or (len(err) > 1 and err[1] == 'V' and err[0] != 'M' and err[0] != 'U' and err[0] != 'R'): #for all targeted verb corrs
			for i in elm:
				if i.tag == 'i' or i.tag == 'c': 
					i.set('delimit', 'yes')
	if elm.text: 
		if elm.get('delimit') == 'yes' and elm.tag == 'i':  
			data = ' @@ ' + elm.text + ' @@ '	#delimit verb errors
		elif elm.get('delimit') == 'yes' and elm.tag == 'c':  
			data = ' $$ ' + elm.text + ' $$ '	#delimit verb corrections
		elif elm.tag != 'c':  #add regular data
			data = elm.text
		else:   #some weird exception
			data = ""
	else: #no text in element
		data = ""
	for child in elm:
		data = data + delimit_data(child)
	if elm.tail:
		data = data + elm.tail
	return data

def get_original(elm):
	"""Extract the original text data from the element elm
		@params:
			xml.Element elm - the element to get text data from 
		@ret:
			text data represented as a string
	"""
	if elm.text and elm.tag != 'c': #get the original text only
		data = elm.text
	else:
		data = ""
	for child in elm:
		data = data + get_original(child)
	if elm.tail:
		data = data + elm.tail
	return data


def get_vcorrected(elm, delimit=False):
	"""Extract the text data with only verb errors corrected
		@params:
			xml.Element elm - element holding the text data
			delimit - whether or not to delimit verb errors/correction
		@ret:
			text data represented as a string
	"""
	if elm.text and elm.get('use') != 'no' and (elm.tag != 'c' or elm.get('use') == 'yes'): #attribute mark whether or not we should use correction or original
		if delimit and elm.get('use') == 'yes':
			data = ' @@ ' + elm.text + ' @@ '	#delimit verb errors
		else:
			data = elm.text 
	else:
		data = ""
	if elm.tag == 'NS':
		err = elm.get('type')
		if err == 'AGV' or (len(err) > 1 and err[1] == 'V' and err[0] != 'M' and err[0] != 'U' and err[0] != 'R'): #for all verb corrs
			for i in elm:
				if i.tag == 'c':  #mark this element to use 
					i.set('use', 'yes')
				elif i.tag == 'i':  #mark this element to not use
					i.set('use', 'no')
	for child in elm:
		data = data + get_vcorrected(child, delimit)
	if elm.tail:
		data = data + elm.tail
	return data

def match(v1, v2):
	"""Return true = the verbs (represented as Strings) v1/v2 are equal"""	
	eq = False	
	if v1 == v2:
		eq = True
	elif (v1 == "is" and v2 == "'s") or (v2 == "is" and v1 == "'s"):
		eq = True
	elif (v1 == "are" and v2 == "'re") or (v2 == "are" and v1 == "'re"):
		eq = True
	elif (v1 == "have" and v2 == "'ve") or (v2 == "have" and v1 == "'ve"):
		eq = True
	elif (v1 == "am" and v2 == "'m") or (v2 == "am" and v1 == "'m"):
		eq = True
	return eq

def get_hit_stats(method_verbs, gold_verbs, orig_verbs):
	"""Return the 'hit' statistics ie return a 4-tuple of
		(True positives, false positives, invalid positives, false negatives)
	"""
#	if len(method_verbs) != len(gold_verbs) or len(method_verbs) != len(orig_verbs):
#		print("Outputs lengths not of the same size")
#		print("{} {} {}".format(len(method_verbs), len(gold_verbs), len(orig_verbs)))
#		return None
	true_pos = 0
	false_pos = 0
	inv_pos = 0
	false_neg = 0
	for i in range(len(gold_verbs)):
		if not match(gold_verbs[i], orig_verbs[i]): #there is an error
			if match(method_verbs[i], gold_verbs[i]): #detect error correctly
				true_pos = true_pos + 1
				print("TruePos: {} {} {}".format(method_verbs[i], gold_verbs[i], orig_verbs[i]))
			elif match(method_verbs[i], orig_verbs[i]):  #did not detect error
				print("FalseNeg: {} {} {}".format(method_verbs[i], gold_verbs[i], orig_verbs[i]))
				false_neg = false_neg + 1
			else:						#fixed error incorrectly
				inv_pos = inv_pos + 1
				print("InvPos: {} {} {}".format(method_verbs[i], gold_verbs[i], orig_verbs[i]))
		elif not match(method_verbs[i], gold_verbs[i]):   #there is no error but we detected one
			false_pos = false_pos + 1
			print("FalsePos: {} {} {}".format(method_verbs[i], gold_verbs[i], orig_verbs[i]))

	return (true_pos, false_pos, inv_pos, false_neg)
			
def fix_tags(method, gold, orig):
	"""Fix pos tags so that everything that is tagged as a verb in one 
		output, is tagged as a verb in the other output (helps correctly compare outputs
		@params:
			list of Sentence objects method, gold, orig
		Note that this modifies the method, gold, and orig data structures
	"""
	if len(method) != len(gold) or len(method) != len(orig):
		print("Number of Sentences are not equal")
		print("{} {} {}".format(len(method), len(gold), len(orig)))
	for i in range(len(method)):
		msen = method[i]
		gsen = gold[i]
		osen = orig[i]
		#dont include the word 'to' since it is the only word that can get removed or added in 
		words = zip([x for x in msen.sen if x.pos != 'TO'], [x for x in gsen.sen if x.pos != 'TO'], [x for x in osen.sen if x.pos != 'TO'])
		for j in words:
			if any(x.isverb() for x in j):  #if any of the words are a verb
				for k in j:
					k.pos = 'VB'  #mark all 3 words as verbs (at this point, the exact pos tag is irrelevent, so just mark as arbitrary VB)


def evaluate(method_out, gold_out, orig_out):
	"""Evaluate the results of the method against gold standard
		@params:
			xmlfilename method_out - the output from the method we are testing   *output from Stanford parser*
			xmlfilename gold_out - the output using the annoatations from fce corpus (gold standard) 
		@ret:
			a triplet (precision, recall, f-score)
	"""
	test_sents = pd.read_xml(method_out, getdeps=False)
	gold_sents = pd.read_xml(gold_out, getdeps=False)
	orig_sents = pd.read_xml(orig_out, getdeps=False)
	fix_tags(test_sents, gold_sents, orig_sents)
#	for i in range(10):
#		for j in test_sents[i].sen:
		#	print(j.pos)
	#		print("{}, {}".format(j.pos, j.word))	
	#return (0, 0)
	test_verbs = []
	gold_verbs = []
	orig_verbs = []

	for s in test_sents:
		for tok in s.sen:
			if tok.isverb(): # and tok.pos != 'MD': 
				test_verbs.append(tok.word)
	for s in gold_sents:
		for tok in s.sen:
			if tok.isverb(): # and tok.pos != 'MD': 
				gold_verbs.append(tok.word)
	for s in orig_sents:
		for tok in s.sen:
			if tok.isverb(): # and tok.pos != 'MD': 
				orig_verbs.append(tok.word)
#	sents = zip(test_sents, gold_sents, orig_sents)
#	for i in sents:
#		t = i[0].sen
#		g = i[1].sen
#		o = i[2].sen
#		s = zip(t, g, o)
#		for tok in s:
#			if all(a.isverb() for a in tok) and tok[0].lemma  == tok[1].lemma and tok[0].lemma == tok[2].lemma: 
#				test_verbs.append(tok[0].word)	
#				gold_verbs.append(tok[1].word)	
#				orig_verbs.append(tok[2].word)	

	print(len(test_verbs))
	print(len(gold_verbs))
	print(len(orig_verbs))
#	return (0, 0)

	stats = get_hit_stats(test_verbs, gold_verbs, orig_verbs)	#(tp, fp, ip, fn)
	print("Final Stats: {} {} {} {}".format(stats[0],stats[1],stats[2],stats[3]))

	if stats:
		prec = (stats[0] + stats[2]) / (stats[0] + stats[2] + stats[1])
		recall = stats[0] / (stats[0] + stats[2] + stats[3])
		return (prec, recall)
	else:
		return (None, None)

if __name__ == "__main__":
	if sys.argv[1] == 'prep': #extract either fce corrected plain text or fce original text
		infile = sys.argv[2]
		if len(sys.argv) == 5:
			gold = sys.argv[3]
			orig = sys.argv[4]
		else:
			gold = 'goldout'
			orig = 'origout'
		gold_file = open(gold, 'w')	
		orig_file = open(orig, 'w')
		gold_file.write(read_fce_xml(infile, corrected=True))
		orig_file.write(read_fce_xml(infile, corrected=False))
	#Take in a fce xml file and write out two text files, one with original text, and one with delimited text
	elif sys.argv[1] == 'delimit': 
		infile = sys.argv[2]
		if len(sys.argv) == 5:
			dataout = sys.argv[3]
			dataout_delim = sys.argv[4]
		else:
			dataout = 'dataout'
			dataout_delim = 'dataout_delimited'
		data_file = open(dataout, 'w')
		delim_file = open(dataout_delim, 'w')	
		data_file.write(read_fce_xml(infile, corrected=False))
		delim_file.write(create_delimited(infile))
	else:
		methodxml = sys.argv[1]	
		goldxml = sys.argv[2]
		origxml = sys.argv[3]
		results = evaluate(methodxml, goldxml, origxml)
		print("Precision: {}".format(results[0]))
		print("Recall: {}".format(results[1]))


		

		
