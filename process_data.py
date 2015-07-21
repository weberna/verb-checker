##########################################################
#     Script to read relevent information from the output
#     of the Stanford Core NLP Annotator Program
#	  and then parse features from the data in order to generate
#	  data to use with Mallet 		
############################################################
from nltk.corpus import verbnet
from lingstructs import *
import lxml.etree as xml
import sys
			
def read_xml(filename, getdeps=True, check=True):
	"""Parse the xml output from filename made by the Stanford Core NLP Annotators
		and extract syntatic and dependecy features 
		@params: String filename,
				bool deps - whether to include dependencies
				bool check - if true, double check if verb is incorrectly tagged as something else 
		@ret: A list of Sentence objects storing each sentence in the file
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
		File with delimiters is only tokenized and split by sentences, used to indicate where
		delimiters should be placed
		@params: String filename - name of file with non delimited pos tagged data,
				 String del_filename - name of file with delimited tokenized data
   				 bool deps - whether to include dependencies
				 bool check - if true, double check if verb is incorrectly tagged as something else 
		@ret: A list of Sentence objects storing each sentence in the file, with delimiters included
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
	for (sen, delsen) in zip(sentences, delsents):
		tokens = sen[0] #a single sentence split into tokens
		deptypes = sen[1:] #the dependency relations (of various kinds) for the words in the sentence
		sen_data = Sentence()	
		prev_isverb = False #whether the previous word is a verb
		delindex = 0
		in_del_phrase = False #if we are currently in a delimited phrase
		for i in tokens: #get data from single token
			t = int(i.get("id"))
			w = i.find("word").text
			l = i.find("lemma").text
			p = i.find("POS").text
			sd = False #start delim
			ed = False #end delim
			#make sure verb was not incorrectly tagged as noun or adjective
			if check and (p[0] == 'N' or p[0] == 'J') and prev_isverb and in_verblist(l):  
				p = 'VB' 
				prev_isverb = False #usually we only need to correct the last verb in verbchain
			elif l == 'be' or l == 'have' or p == 'MD':   #tagger usually has problems tagging verbs comming after these 
				prev_isverb = True
			else:
				prev_isverb = False
			#end check code
			if delsen[0][delindex].find("word").text == '@@' and w != '@@': #check for delimited words (errors)
				if not in_del_phrase:
					sd = True
					in_del_phrase = True
					delindex = delindex + 1
				else:
					ed = True
					in_del_phrase = False
					delindex = delindex + 1
#			elif training and delsen[0][delindex].find("word").text == '$$' and w != '$$': #check for delimited words (corrections)
#NEED TO ADD THIS
			tok = Token(w, l, p, t, sd, ed)
			delindex = delindex + 1
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



def in_verblist(lem):
	"""Return true if the given lemma is found in the verbnet verb list"""
	verblist = verbnet.lemmas()
	if lem in verblist:
		return True
	else:
		return False

def create_data(sents, filename='data_mallet.txt', unlabeled=False, labels_file=None):
	"""Write a data file that can be used for training
		or testing CRFs in Mallet. The data is written 
		in the following form:
		Each line represents a verb instance.
		Every line is written in the standard 
		Mallet form <feature> <feature> ... <label>
		where label is the specific verb POS
		@params:
			list of Sentences sents - the data created from read_xml()
			string filename - file to write to 
	"""
	prev_sen = None
	outfile = open(filename, 'w')
	if labels_file:
		lfile = open(labels_file, 'w')
	for s in sents:
		for tok in s.sen:
			if tok.isverb() and tok.pos != 'MD': 
				feats = Features(tok, s, prev_sen)
				if unlabeled:
					lab = feats.fvect.pop() #get rid of label
					if labels_file:  #write the label to the seperate label file
						lfile.write("{}\n".format(lab))	
				str_feats = " ".join([str(x) for x in feats.fvect])
				outfile.write("{}\n".format(str_feats))
#				if last_in_chain(tok, s):   #sequence ends at verb phrase
#					outfile.write("\n")
			if tok.word == '.':				#sequence ends at sentence end
				outfile.write("\n")
				if labels_file:
					lfile.write("\n")
		prev_sen = s
	outfile.close()
		
if __name__ == "__main__":	
	infile = sys.argv[1]
#	outfile = sys.argv[2]
#	sents = read_xml(infile)
#	if len(sys.argv) > 3:
#		if sys.argv[3] == 'nolabels':
#			create_data(sents, outfile, True)
#		else:
#			create_data(sents, outfile, True, sys.argv[3]) #create origianl label file
#	else:
#		create_data(sents, outfile)
#	print("done")

#	sents = read_xml(infile)
#	for s in sents:
#		chains = s.get_vchains()	
#		for c in chains:
#			#print(c.tostring())
#			print(get_aspect(c))
	a = generate_aspect(['', 'PAST', 'PERFECT'])
	b = generate_aspect(['1ST', 'PRESENT', 'PROGRESSIVE'])
	c = generate_aspect(['PLURAL', 'PAST', 'PROGRESSIVE'])
	d = generate_aspect(['PLURAL', 'PRESENT', 'PROGRESSIVE'])
	e = generate_aspect(['3RD', 'PRESENT', 'PROGRESSIVE'])
	f = generate_aspect(['1ST', '', 'PERFECT PROGRESSIVE'])
	print(a)
	print(b)
	print(c)
	print(d)
	print(e)
	print(f)

	print(get_aspect2(a.split))
	print(get_aspect2(b.split))
	print(get_aspect2(c.split))
	print(get_aspect2(d.split))
	print(get_aspect2(e.split))
	print(get_aspect2(f.split))
	







