#########################################################
#			vcorrect.py
# Script to take in a xml representation of a text, and output
# the corrected form of the text to a different text file
#########################################################
import process_data as pd
import lingstructs as ling
import subprocess as sub
import sys

def vcorrect(infile, seqfile, outfile='corrected.txt'): 
	"""
	Takes in the xml data outputted from the Stanford CoreNlp,
	a file containing the correct sequence for verbs in that file,
	and rewrites the original test with the corrections
	@params:
		string infile - filename for the xml data
		string seqfile - filename for the sequence data
		(the ith line in file should represent the ith verb in the text
		and contain the correct label for that verb)
		string outfile - file to write corrected text to
	"""
	sfile = open(seqfile, 'r')
	seq = sfile.readlines() #get list containing seqence from file
	sfile.close()
	seq = [x for x in seq if x != '\n'] #remove blank lines
	seq.reverse() #reverse so first element at end
	sents = pd.read_xml(infile)
	corrected = ""
	for s in sents:
		for tok in s.sen: 
			if tok.pos[0] == 'V':
				label = seq.pop() #get the form this verb should be
				tok.word = change_vform(tok.lemma, label) #change the verb form
		corrected = corrected + s.tostring() #add corrected sentence to text
	#now write all corrected text
	corrfile = open(outfile, 'w')
	corrfile.write(corrected + "\n")
	corrfile.close()

def change_vform(lemm, outlabel):
	"""
	Change the form of a verb from one form to another
	Note: This method uses an external Perl script written by [Cite]
	@params:
		string lemm - the lemma of the verb to change
		string inlabel - the currect form label of the verb (use same labels as in the sequence file)
		string outlabel - the form to change to
	@ret: the string form of the changed verb
	"""
	#the perl script represents the forms by numbers
	if str.strip(outlabel) == 'VBP[auxplural]': 
		return 'are'
	elif str.strip(outlabel) == 'VBD[auxplural]':
		return 'were'
	elif lemm == 'be' and str.strip(outlabel) == 'VBP':
		return 'am'
	elif lemm == 'be' and str.strip(outlabel) == 'VBZ':
		return 'is'
	elif lemm == 'be' and str.strip(outlabel) == 'VBD':
		return 'was'
	else:
		out_form = get_label_id(outlabel)
		outverb = sub.check_output(["./verbTenseChanger.pl", lemm, '0', str(out_form)])
		return outverb.decode('utf-8')

def get_label_id(label):
	"""Return the integer id for the corresponding label that can be given to the perl script"""	
	if label == 'VB' or label == 'VB[be]': #base form
		return 0
	elif label[2] == 'D': #past simple tense
		return 1
	elif label[2] == 'N': #past participle
		return 2
	elif label[2] == 'Z': #3rd person singular
		return 3
	elif label[2] == 'G': #present participle
		return 4
	else:
		return 0


if __name__ == "__main__":					
	xmlfile = sys.argv[1]
	seqfile = sys.argv[2]
	if len(sys.argv) > 3: #if the output file is specified
		vcorrect(xmlfile, seqfile, sys.argv[3])
	else:
		vcorrect(xmlfile, seqfile)
	print("done")

