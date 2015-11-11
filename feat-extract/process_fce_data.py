################################################################
#
#				process_fce_data
#				Author: Noah Weber
# Various methods for handeling error annotated FCE corpus data
#
################################################################
import lxml.etree as xml
import sys

def read_fce_xml(datafile, corrected=True):
	"""Read the the fce xml file from datafile and return the text data
		as a string. 
		@params:
			string datafile - fce xml file
			bool corrected - If True, return the data with verb errors corrected, 
							else return original
		@returns:
			text contents of the fce xml file
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

def create_delimited(datafile):
	"""Create String data with error annotations 
		@params:
			string datafile - fce xml file
		@returns:
			Annotated data as a string
	"""
	sents = []
	xfile = open(datafile, 'r')
	data = xml.parse(xfile)
	root = data.getroot()
	strdata = ""
	for p in root.iter('p'):
		strdata = strdata + delimit_data(p) + " "
	return strdata

def delimit_data(elm):
	"""Get String data for training (delimit verb errors with @@ and corrections with $$)
		@params:
			lxml.Element elm
		@returns:
			Delimited string data
	"""
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

#Note dont use this method to delimit data, just pass a single argument
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

if __name__ == '__main__':
	if sys.argv[1] == 'extract': #extract both fce corrected plain text or fce original plain text
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
		#Delimit fce error annotated data 
		else: 
			infile = sys.argv[2] #fce xml file
			textout = sys.argv[3]
			dataout_delim = sys.argv[4]
			text_file = open(textout, 'w')
			delim_file = open(dataout_delim, 'w')	
			text_file.write(read_fce_xml(infile, corrected=False))
			delim_file.write(create_delimited(infile))

