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
			data = ' ## ' + elm.text + ' ## '	#delimit verb corrections
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

def get_hit_stats(method_lab, gold_lab, orig_lab):
	true_pos = 0
	false_pos = 0
	inv_pos = 0
	false_neg = 0
	for i in range(len(method_lab)):
		if gold_lab[i] != orig_lab[i]: #there is an error
			if method_lab[i] == gold_lab[i]: #detect error correctly
				true_pos = true_pos + 1
				print("TruePos: {} {} {}".format(method_lab[i], gold_lab[i], orig_lab[i]))
			elif method_lab[i] == orig_lab[i]:  #did not detect error
				print("FalseNeg: {} {} {}".format(method_lab[i], gold_lab[i], orig_lab[i]))
				false_neg = false_neg + 1
			else:						#fixed error incorrectly
				inv_pos = inv_pos + 1
				print("InvPos: {} {} {}".format(method_lab[i], gold_lab[i], orig_lab[i]))
		elif method_lab[i] != gold_lab[i]:   #there is no error but we detected one
			false_pos = false_pos + 1
			print("FalsePos: {} {} {}".format(method_lab[i], gold_lab[i], orig_lab[i]))

	return (true_pos, false_pos, inv_pos, false_neg)

def evaluate(method_out, gold_out, orig_out):
	"""Evaluate the results of the method against gold standard
		@params:
			filename method_out - output labels from method
			filename gold_out - output labels from corrected data
			filename orig_out - output labels from original data
		@ret:
			a triplet (precision, recall, f-score)
	"""
	mf = open(method_out, 'r')
	gf = open(gold_out, 'r')
	of = open(orig_out, 'r')
	method_labs = [x.strip('\n') for x in mf.readlines()]
	gold_labs = [x.strip('\n') for x in gf.readlines()]
	orig_labs = [x.strip('\n') for x in of.readlines()]

	stats = get_hit_stats(method_labs, gold_labs, orig_labs)
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
#		data_file.write(read_fce_xml(infile, corrected=True))
		#Want corrected=True for training, corrected=False for testing
		data_file.write(read_fce_xml(infile, corrected=False))
		delim_file.write(create_delimited(infile))
	else:
		method = sys.argv[1]	
		gold = sys.argv[2]
		orig = sys.argv[3]
		results = evaluate(method, gold, orig)
		print("Precision: {}".format(results[0]))
		print("Recall: {}".format(results[1]))


		

		
