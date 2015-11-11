##########################################################
#			process_data 
#		Author: Noah Weber
#     Script to read relevent information from the output
#     of the Stanford Core NLP Annotator Program
#	  and then parse features from the data in order to generate
#	  data to use with Mallet 		
############################################################
from nltk.corpus import verbnet
from lingstructs import *
import lxml.etree as xml
import sys
import pickle
			
def read_xml(filename, getdeps=True, check=True):
	"""Parse the xml output from filename made by the Stanford Core NLP Annotators
		and extract syntatic and dependecy features 
		@params:
				String filename,
				bool deps - whether to include dependencies
				bool check - if true, double check if verb is incorrectly tagged as something else 
		@ret: 
			A list of Sentence objects storing each sentence in the file
	"""
	sents = []
	xfile = open(filename, 'r')
	data = xml.parse(xfile)
	root = data.getroot()
	sentences = root[0][0] #get the sentences tree
	for sen in sentences:
		tokens = sen[0] #a single sentence split into tokens
		deptypes = sen[1:] #the dependency relations (of various kinds) for the words in the sentence
		sen_data = Sentence()	
		prev_isverb = False #whether the previous word is a verb
		for i in tokens: #get data from single token
			t = int(i.get("id"))
			w = i.find("word").text
			l = i.find("lemma").text
			p = i.find("POS").text
			#make sure verb was not incorrectly tagged as noun or adjective
			if check and (p[0] == 'N' or p[0] == 'J') and prev_isverb and in_verblist(l):  
				p = 'VB' 
				prev_isverb = False #usually we only need to correct the last verb in verbchain
			elif l == 'be' or l == 'have' or p == 'MD':   #tagger usually has problems tagging verbs comming after these 
				prev_isverb = True
			else:
				prev_isverb = False
			#end check code
			tok = Token(w, l, p, t)
			sen_data.add_word(tok)
		if getdeps:
			for deps in deptypes:
				if deps.get("type") == "collapsed-ccprocessed-dependencies":
					for i in deps: #i is a single dependency relation
						t = i.get("type")	
						gov = (i.find("governor").text.lower(), int(i.find("governor").get("idx"))) #note: just added lower()
						dep = (i.find("dependent").text.lower(), int(i.find("dependent").get("idx")))
						relation = Dependency(t, gov, dep)
						sen_data.add_dep(relation)
		sents.append(sen_data)
	xfile.close()
	return sents

def read_delimited_xml(filename, del_filename, getdeps=True, check=True):
	"""Read xml with delimiters around verb phrase. Need to process a
		file without delimiters so the Stanford parser does not get confused by the delimiters.
		File with correction delimiters is should be pos tagged, does not need dep parsing
		@params: 
				String filename - name of file with non delimited pos tagged data and dependency parse (xml output from Stanford tagger/parser),
				 String del_filename - name of file with pos tagged data (xml output from Stanford tagger)
   				 bool deps - whether to include dependencies
				 bool check - if true, double check if verb is incorrectly tagged as something else 
		@ret: 
			A list of Sentence objects storing each sentence in the file, with delimiters included
	"""
	sents = []
	xfile = open(filename, 'r')
	delfile = open(del_filename, 'r')
	data = xml.parse(xfile)
	deldata = xml.parse(delfile)
	root = data.getroot()
	delroot = deldata.getroot()
	sentences = root[0][0] #get the sentences tree
	delsents = delroot[0][0]
	prev = None #previous sentence
	for (sen, delsen) in zip(sentences, delsents):
		tokens = sen[0] #a single sentence split into tokens
		deptypes = sen[1:] #the dependency relations (of various kinds) for the words in the sentence
		sen_data = Sentence()	
		prev_isverb = False #whether the previous word is a verb
		delindex = 0
		in_error_phrase = False #if we are currently in a delimited error or correction phrase
		pairs = [] #list of error/correction pairs
		error_phrase = []
		for i in tokens: #get data from single token
			t = int(i.get("id"))
			w = i.find("word").text
			l = i.find("lemma").text
			p = i.find("POS").text
			#make sure verb was not incorrectly tagged as noun or adjective
			if check and (p[0] == 'N' or p[0] == 'J') and prev_isverb and in_verblist(l):  
				p = 'VB' 
				prev_isverb = False #usually we only need to correct the last verb in verbchain
			elif l == 'be' or l == 'have' or p == 'MD': #tagger usually has problems tagging verbs comming after these
				prev_isverb = True
			else:
				prev_isverb = False
			#end check code
			if delsen[0][delindex].find("word").text == '@@' and w != '@@': #check for delimited words (errors)
				delindex = delindex + 1
				if not in_error_phrase:
					in_error_phrase = True
				else:  #if we are in error phrase and see delimiter, it is ending delimiter, add error phrase to CorrectionPair list
					in_error_phrase = False
					if delsen[0][delindex].find("word").text == '##': #get correction phrase
						delindex = delindex + 1
						corr_phrase = []
						while delsen[0][delindex].find("word").text != '##':  #till end of correction phrase
							c = delsen[0][delindex]
							ct = int(c.get("id"))
							cw = c.find("word").text
							cl = c.find("lemma").text
							cp = c.find("POS").text
							ctok = Token(cw, cl, cp, ct) 
							corr_phrase.append(ctok)
							delindex = delindex + 1
						pairs.append(CorrectionPair(VChain(list(error_phrase)), VChain(list(corr_phrase))))
						delindex = delindex + 1
					error_phrase = [] #reset error phrase
			tok = Token(w, l, p, t, in_error_phrase)
			delindex = delindex + 1
			sen_data.add_word(tok)
			if in_error_phrase: 
				error_phrase.append(tok)
		sen_data.add_pairs(pairs)
		if getdeps:
			for deps in deptypes:
				if deps.get("type") == "collapsed-ccprocessed-dependencies":
					for i in deps: #i is a single dependency relation
						t = i.get("type")	
						gov = (i.find("governor").text.lower(), int(i.find("governor").get("idx"))) #note: just added lower()
						dep = (i.find("dependent").text.lower(), int(i.find("dependent").get("idx")))
						relation = Dependency(t, gov, dep)
						sen_data.add_dep(relation)
		sen_data.prev = prev
		prev = sen_data
		sents.append(sen_data)
	xfile.close()
	return sents

#Keep this around just in case, we dont really need it however
def create_crf_data(sents, filename='data_mallet.txt', unlabeled=False, labels_file=None, corrs=False):
	"""Write a data file that can be used for training or testing CRFs in Mallet. The data is written 
		in the following form:
		<feature> <feature> ... <label>
		A newline seperates different sequences
		@params:
			list of Sentences sents - the data created from read_xml()
			string filename - file to write to 
	"""
	outfile = open(filename, 'w')
	if labels_file:
		lfile = open(labels_file, 'w')
	for s in sents:
		corrected = False
		if corrs:
			for pair in s.corr_pairs:
				feats = CorrectionFeatures(pair, s)
				if unlabeled:
					lab = feats.fvect.pop() #get rid of label
					if labels_file:  #write the label to the seperate label file
						lfile.write("{}\n".format(lab))	
				str_feats = " ".join([str(x) for x in feats.fvect])
				outfile.write("{}\n".format(str_feats))
				corrected = True
		else:
			for chain in s.get_vchains():
				feats = Features(chain, s)
				if feats.fvect[len(feats.fvect) - 1] != 'ERROR':
					if unlabeled:
						lab = feats.fvect.pop() #get rid of label
						if labels_file:  #write the label to the seperate label file
							lfile.write("{}\n".format(lab))	
					str_feats = " ".join([str(x) for x in feats.fvect])
					outfile.write("{}\n".format(str_feats))
					corrected = True 
		if corrected:
			outfile.write("\n")
			if labels_file:
				lfile.write("\n")
	outfile.close()

def in_verblist(lem):
	"""Return true if the given lemma is found in the verbnet verb list"""
	verblist = verbnet.lemmas()
	if lem in verblist:
		return True
	else:
		return False

#dont really need this anymore, keep around just incase
def write_all_instances(sents, filename, labels_file=None):
	"""Write a instance file representation in a form that can be
		read by Mallet's Csv2Vectors script (this converts the data into binary form for Mallet's classifiers)
		Data form:
			<instance name> <label> <feature> ...
		This gets all verb chain instances, use this for gathering instance data for language model, not for correction
		model
		@params:
			list of Sentences sents - the data created from read_xml() 
			string filename - file to write to 
			labels_file - File to print labels to (include them in instance file if no label file provided)
	"""
	outfile = open(filename, 'w')
	if labels_file:
		lfile = open(labels_file, 'w')
	name = 0 #for instance names just give unique number starting at 0
	for s in sents:
		li = s.get_vchains()
		for i in li:
			feats = Features(i, s)
			label = feats.fvect.pop() 
			if label != 'ERROR': #for now, ignore data too malformed to get all features for
				str_feats = " ".join([str(x) for x in feats.fvect])
				if labels_file:  #write the label to the seperate label file
					lfile.write("{}\n".format(label))	
					outfile.write("{} {}\n".format(name, str_feats))
				else:
					outfile.write("{} {} {}\n".format(name, label, str_feats))
				name = name + 1
	outfile.close()
	if labels_file:
		lfile.close()

def write_clean_instances(sents, filename, labels_file=None, corr=True):
	"""Get cleaned instance data needed for training. The difference between this and all_instance_data() is 
		that this method only includes instances that do not have a label that equals ERROR for both its
		corresponding Features and CorrectionFeatures object (this ensures that we can correctly analyze 
		the quality of our results)  
		Use this method to get regular instance data for testing or correction instance data for training
		@params:
			list of Sentences sents - the data created from read_xml() 
			string filename - file to write to 
			labels_file - File to print labels to (include them in instance file if no label file provided)
			bool corr - whether or not to use CorrectionFeatures or regular Features
	"""
	if labels_file:
		lfile = open(labels_file, 'w')
	outfile = open(filename, 'w')
	name = 0 #for instance names just give unique number starting at 0
	for s in sents:
		flist = s.get_feats(corr) #list of all features in sentence
		for feats in flist:
			label = feats.fvect.pop()
			if label != 'ERROR':
				str_feats = " ".join([str(x) for x in feats.fvect])
				if labels_file:  #write labels to seperate file
					outfile.write("{} {}\n".format(name, str_feats))
					lfile.write("{}\n".format(label))
				else:
					outfile.write("{} {} {}\n".format(name, label, str_feats))
				name = name + 1
	outfile.close()
	if labels_file:
		lfile.close()

def write_testing_instances(sents, filename, labels_file, orig_file):
	"""Create correction instance data for testing, puts all CorrectionFeature instances
		in one file (without labels), with the correct labels in another file (use these as the gold label set
		for testing), and the original labels in another file
		@params:
			list of Sentences sents - the data created from read_xml() 
			string filename - file to write to 
			labels_file - File to print labels to 
			orig_file - File to print original labels to 
	"""
	lfile = open(labels_file, 'w')
	ofile = open(orig_file, 'w')
	outfile = open(filename, 'w')
	name = 0 #for instance names just give unique number starting at 0
	for s in sents:
		flist = s.get_feats(True) #list of all CorrectionFeatures in sentence
		for feats in flist:
			correction = feats.fvect.pop()
			if correction != 'ERROR':
				str_feats = " ".join([str(x) for x in feats.fvect])  #get all features
				outfile.write("{} {}\n".format(name, str_feats))
				lfile.write("{}\n".format(correction))	
				ofile.write("{}\n".format(feats.fvect[0][:len(feats.fvect[0])-10]))
				name = name + 1
	outfile.close()
	lfile.close()

if __name__ == "__main__":	
#Delimited only needs to be used for training data!
	arg = sys.argv[1]
	if arg == 'prep':
	#ARGS prep inxml [delimitedxml] outfile.p
	#If both xml files are passed in assume delimited output
		if len(sys.argv) > 4: #delimited
			inxml = sys.argv[2]
			delimxml = sys.argv[3]
			outfile = sys.argv[4]
			sents = read_delimited_xml(inxml, delimxml)
			pickle.dump(sents, open(outfile, 'wb'))
		else:
			inxml = sys.argv[2]
			outfile = sys.argv[3]
			sents = read_xml(inxml)
			pickle.dump(sents, open(outfile, 'wb'))
	elif arg == 'training': #create CorrectionFeatures instance data for correction model training from error delimed data
	#ARGS corr-train outfile.in sentfile.p 
		outfile = sys.argv[2]
		sentfile = sys.argv[3] #make pickle file last arg
		sents = pickle.load(open(sentfile, 'rb'))
		write_clean_instances(sents, outfile, None, True)
	elif arg == 'testing': #create CorrectionFeatures instance data for testing, along with gold labels and original labels
	#ARGS gold outfile.in corrlabels sentfile.p	
		outfile = sys.argv[2]
		labelfile = sys.argv[3]
		origfile = sys.argv[4]
		sentfile = sys.argv[5]
		sents = pickle.load(open(sentfile, 'rb'))
		write_testing_instances(sents, outfile, labelfile, origfile)
	#ARGS outfile.in sentfile.p 
	else:  #get all instance data for language model training
		outfile = sys.argv[1] 
		sentfile = sys.argv[2] #make pickle file last arg
		sents = pickle.load(open(sentfile, 'rb'))
		write_all_instances(sents, outfile)

	print("done")
