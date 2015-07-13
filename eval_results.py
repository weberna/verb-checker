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

def read_fce_xml(datafile):
	sents = []
	xfile = open(datafile, 'r')
	data = xml.parse(xfile)
	root = data.getroot()
	for p in root.iter('p'):
	#	print(get_original(p))
		print(get_vcorrected(p))

def get_original(elm):
	"""Extract the original text data from the element elm
		@params:
			xml.Element elm - the element to get text data from 
		@ret:
			text data represented as a string
	"""
	if elm.text and elm.tag != 'c':
		data = elm.text 
	else:
		data = ""
	for child in elm:
		data = data + get_original(child)
	if elm.tail:
		data = data + elm.tail
	return data

def get_vcorrected(elm):
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
		if err_type == 'AGV' or (len(err_type) > 1 and err_type[1] == 'V' and err_type[0] != 'M' and err_type[0] != 'U'): #for all verb corrections
			for i in elm:
				if i.tag == 'c':
					i.set('use', 'yes')
				elif i.tag == 'i':
					i.set('use', 'no')
	for child in elm:
		data = data + get_vcorrected(child)
	if elm.tail:
		data = data + elm.tail
	return data

def get_hit_stats(method_verbs, gold_verbs, orig_verbs):
	"""Return the 'hit' statistics ie return a 4-tuple of
		(True positives, false positives, true negatives, false negatives)
	"""

def evaluate(method_out, gold_out, orig_out):
	"""Evaluate the results of the method against gold standard
		@params:
			xmlfilename method_out - the output from the method we are testing   *output from Stanford parser*
			xmlfilename gold_out - the output using the annoatations from fce corpus (gold standard) 
		@ret:
			a triplet (precision, recall, f-score)
	"""
	test_sents = pd.read_xml(method_out)
	gold_sents = pd.read_xml(gold_out)
	orig_sents = pd.read_xml(orig_out)
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
		

		

if __name__ == "__main__":
	infile = sys.argv[1]
	read_fce_xml(infile)
		
