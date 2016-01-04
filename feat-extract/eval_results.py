###################################################
#         eval_results.py
#    Module that evaluates the corrections made
#    on FCE data and checks it aginst fce data set
#    and returns recall, precision
###################################################
from lingstructs import *
import sys

#DEPRECATED 
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

#DEPRECATED
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

def get_hit_stats(method_lab, gold_lab, orig_lab, false_neg_file=None):
	"""Take in the results of the classifier, the golden results, and the original results
		and return relevent hit statistics.
		Label files must be correctly aligned for this to work!
		@params:
			string method_lab - a list of tense aspect labels from method
			string gold_lab - results from golden (corrected) labels
			string orig_lab - list of original labels
		@ret:
			a tuple - (true_pos, false_pos, inv_pos, false_neg)
	"""

	if false_neg_file:
		f = open(false_neg_file, 'w')
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
				if false_neg_file:
					f.write(("{} {} {}\n".format(i, method_lab[i], gold_lab[i])))
			else:						#fixed error incorrectly
				inv_pos = inv_pos + 1
				print("InvPos: {} {} {}".format(method_lab[i], gold_lab[i], orig_lab[i]))
		elif method_lab[i] != gold_lab[i]:   #there is no error but we detected one
			false_pos = false_pos + 1
			print("FalsePos: {} {} {}".format(method_lab[i], gold_lab[i], orig_lab[i]))

	return (true_pos, false_pos, inv_pos, false_neg)

#DEPERACATED
def find_false_instances(fneg_file, inst_file, out_file):
	ifile = open(inst_file, 'r')
	fnegfile = open(fneg_file, 'r')
	outfile = open(out_file, 'w')
	instances = [x.strip('\n') for x in ifile.readlines()]
	fneg_names = [x.strip('\n') for x in fnegfile.readlines()]
	for i in fneg_names:
		inst_data = i.split(None, 1)
		index = inst_data[0]
		outfile.write("{} {}\n".format(instances[int(index)], inst_data[1]))

def evaluate(method_out, gold_out, orig_out, get_fnegs=False):
	"""Evaluate the results of the method against gold standard
		@params:
			filename method_out - output labels from method
			filename gold_out - output labels from corrected data
			filename orig_out - output labels from original data
            get_fnegs - tells whether to print all false negatives to a seperate file (DEPRECATED)
		@ret:
			a tuple (precision, recall)
	"""
	mf = open(method_out, 'r')
	gf = open(gold_out, 'r')
	of = open(orig_out, 'r')
	method_labs = [x.strip('\n') for x in mf.readlines()]
	gold_labs = [x.strip('\n') for x in gf.readlines()]
	orig_labs = [x.strip('\n') for x in of.readlines()]

	if get_fnegs:
		stats = get_hit_stats(method_labs, gold_labs, orig_labs, 'false_negs')
	else:
		stats = get_hit_stats(method_labs, gold_labs, orig_labs)
	print("Final Stats: {} {} {} {}".format(stats[0],stats[1],stats[2],stats[3]))
	if stats:
		prec = (stats[0] + stats[2]) / (stats[0] + stats[2] + stats[1])
		recall = stats[0] / (stats[0] + stats[2] + stats[3])
		return (prec, recall)
	else:
		return (None, None)

if __name__ == "__main__":
	#ARGS: eval_results.py method-out gold-out orig-out
	if sys.argv[1] == 'fneg':
		inst = sys.argv[2]
		fneg = 'false_negs'
		out = sys.argv[3]
		find_false_instances(fneg, inst, out)	
	else:
		method = sys.argv[1]	
		gold = sys.argv[2]
		orig = sys.argv[3]
		results = evaluate(method, gold, orig)
		print("Precision: {}".format(results[0]))
		print("Recall: {}".format(results[1]))


		

		
