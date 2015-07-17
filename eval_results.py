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

def read_fce_xml(datafile, corrected=True):
	"""Read the the fce xml file from datafile and return the text data
		as a string. If corrected is True, return the data with verb errors corrected
		else return original, possibly incorrect data
	"""
	sents = []
	xfile = open(datafile, 'r')
	data = xml.parse(xfile)
	root = data.getroot()
	strdata = ""
	if corrected:
		for p in root.iter('p'):
			strdata = strdata + get_vcorrected(p) + " "
	else:
		for p in root.iter('p'):
			strdata = strdata + get_original(p) + " "
	return strdata

def get_original(elm):
	"""Extract the original text data from the element elm
		@params:
			xml.Element elm - the element to get text data from 
		@ret:
			text data represented as a string
	"""
	if elm.text and elm.tag != 'c': #get the original text only
		data = elm.text 
#		err_type = elm.get('type')
#		if err_type and (err_type == 'AGV' or (len(err_type) > 1 and err_type[1] == 'V' and err_type[0] != 'M' and err_type[0] != 'U' and err_type[0] != 'R')): #for all verb corrs
#			if any(s == ' ' for s in elm.text):
#				data = ""
	else:
		data = ""
	for child in elm:
		data = data + get_original(child)
	if elm.tail:
		data = data + elm.tail
	return data

def get_vcorrected(elm, prev=None):
	"""Extract the text data with only verb errors corrected
		@params:
			xml.Element elm - element holding the text data
		@ret:
			text data represented as a string
	"""
	if elm.text and elm.get('use') != 'no' and (elm.tag != 'c' or elm.get('use') == 'yes'): #attribute mark whether or not we should use correction or original
		data = elm.text 
	else:
		data = ""
	if elm.tag == 'NS':
		err_type = elm.get('type')
		if err_type == 'AGV' or (len(err_type) > 1 and err_type[1] == 'V' and err_type[0] != 'M' and err_type[0] != 'U' and err_type[0] != 'R'): #for all verb corrs
			for i in elm:
				if i.tag == 'c':
					i.set('use', 'yes')
				#	if any(s == ' ' for s in i.text):
				#		i.set('use', 'no')
				#		p = i.getprevious()
				#		if p is not None and p.tag == 'i':
				#			p.set('use', 'yes')
#						i.text = i.text[3:]
				elif i.tag == 'i':
					i.set('use', 'no')
	for child in elm:
		data = data + get_vcorrected(child)
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
	if sys.argv[1] == 'prep':
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
	else:
		methodxml = sys.argv[1]	
		goldxml = sys.argv[2]
		origxml = sys.argv[3]
		results = evaluate(methodxml, goldxml, origxml)
		print("Precision: {}".format(results[0]))
		print("Recall: {}".format(results[1]))


		

		
