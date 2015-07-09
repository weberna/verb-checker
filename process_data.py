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
			
def read_xml(filename, check=True):
	"""Parse the xml output from filename made by the Stanford Core NLP Annotators
		and extract syntatic and dependecy features 
		@params: String filename,
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
		#	elif p[0] == 'V' or p == 'MD':
			elif l == 'be' or l == 'have' or p == 'MD':
				prev_isverb = True
			else:
				prev_isverb = False
			#end check code
			tok = Token(w, l, p, t)
			sen_data.add_word(tok)
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
	outfile = sys.argv[2]
	sents = read_xml(infile)
	if len(sys.argv) > 3:
		if sys.argv[3] == 'nolabels':
			create_data(sents, outfile, True)
		else:
			create_data(sents, outfile, True, sys.argv[3])
	else:
		create_data(sents, outfile)
	print("done")


		







