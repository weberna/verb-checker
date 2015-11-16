##########################################################
#       lingstructs.py
#       Various classes to hold linguistic data parsed
#       from the xml output produced by the Stanford CoreNLP
#       pipeline
############################################################
import fst
import string
from nltk.corpus import verbnet

class Token:
    'Holds the data for a single token'
    def __init__(self, word, lemma, pos, tid, delim=False):
        self.word = word.lower()  #lower() added 
        self.lemma = lemma
        self.pos = pos
        self.tid = tid #token id (ie position in sentence)
        self.in_delim = delim #whether or not this token is in a delimited (error) phrase 

    def singular_noun(self):
        """Return whether Token is singular or plural noun"""
        if self.pos == 'NNS' or self.pos == 'NNPS' or self.word in ['we', 'they', 'us', 'them']:
            return False
        else:
            return True

    def noun_person(self):
        """If token is noun return whether token is 3rdSingular, Plural, or 1stSingular,
            return a string from the set {3rdSingular, Plural, 1stSingular}
            else return false if not a noun
        """
        if self.word.lower() == 'i' or self.word.lower() == 'me':
#           return 'FirstSingular'
            return 'FirstPerson'
        elif self.pos == 'NN' or self.pos == 'NNP' or self.word.lower() in ['he', 'she', 'it', 'him', 'her']:
#           return 'ThirdSingular'
            return 'ThirdPerson'
        elif self.word.lower() in ['we', 'us']:
#           return 'FirstPlural'
            return 'FirstPerson'
        elif self.word.lower() in ['they', 'them'] or self.pos == 'NNS' or self.pos == 'NNPS':
#           return 'ThirdPlural'
            return 'ThirdPerson'
        elif self.word.lower() == 'you':
            return 'SecondPerson'
        else:
            return False

    def isverb(self):
        """Return true if token is a verb or modal verb"""
        if self.pos[0] == 'V' or self.pos == 'MD':
            return True
        else:
            return False
    
    def abbv_to_word(self):
        """Convert abbreviated words (ie 'nt, 've 'd) to their word form"""
        if self.word == "'m":
            return 'am'
        elif self.word == "'ve":
            return 'have'
        elif self.word == "'s":
            return 'is'
        elif self.word == "'re":
            return 'are'
        elif self.word == "'d":
            return 'would'
        else:
            return self.word

    def copy(self):
        return Token(self.word, self.lemma, self.pos, self.tid, self.in_delim)

    def isvalid(self):
        """Return True is token is a non null or root (tid==0) token"""
        if self.tid > 0:
            return True
        else:
            return False

    def isaux(self):
        """return True if verb is auxiliary verb"""
        auxlist = ['be', 'have', 'do']
        if not self.isverb():
            return False
        elif self.lemma in auxlist or self.pos == 'MD':
            return True
        else:
            return False

    def isadverb(self):
        if self.pos[0] == 'R':
            return True
        else:
            return False

#note that most token/token property searching methods just return a NullToken object if 
#no sutiable token/token property could be found
class NullToken(Token):
    'NullToken class represents non exsistent Tokens, use for error handeling'
    def __init__(self):
        self.word = '__NULL__TOKEN'
        self.lemma = '__NULL__TOKEN'
        self.pos = '__NULL__TOKEN'
        self.tid = -1

class VChain:
    'Represents a chain of verb Token objects'
    def __init__(self, chain, start=None, end=None, position=-1,):
        """@params:
                List of Tokens chain
                int start, end - tid of where the verb chain starts (inclusive),
                                 and where it ends (exclusive)
        """
        if start == None:
            start = chain[0].tid
        if end == None:
            end = chain[len(chain)-1].tid
        self.chain = chain  
        self.start = start
        self.end = end
        self.position = position #what number verb chain it is in the sentence
        self.length = len(self.chain)
    
    def length(self):
        return self.length
    
    def range(self):
        """Return (start tid, end tid) tuple"""
        return (self.start, self.end)
    
    def tostring(self):
        return " ".join([x.word for x in self.chain])
    
    def first(self):
        return self.chain[0]
    
    def last(self):
        return self.chain[self.length - 1]

    def head(self):
        """Return head of verb chain (return the last verb pretty much)"""
        found = False
        for i in self.chain:
            if i.isverb():
                found = True
                head = i
        if not found:
            head = self.last()
        return head

    def fst_sequence(self):
        """Return a representation of the verb chain that can be used in the fst"""
        seq = []
        other_aux = ['be', 'being', 'having', 'doing']  
        for i in self.chain:
            if i.isaux() and i.pos != 'MD' and (i not in other_aux):
                seq.append(i.abbv_to_word())
            elif (not i.isadverb() or (i in other_aux) or i.tid == self.head().tid) and i.pos != 'MD':
                seq.append(i.pos)
        return seq

class CorrectionPair:
    'Represents a error annotated verb phrase and its corresponding correction'
    def __init__(self, error, corr):
        """@params: (VChain) error, corr"""
        self.error = error
        self.correction = corr
    
    def tostring(self):
        return "{} -> {}".format(self.error.tostring(), self.correction.tostring()) 
                
class Dependency:
    'Holds a dependency relation for tokens in a sentence'
    def __init__(self, dtype, gov, dependent):
        """@params: 
                string dtype - type of relation
                2-Tuple gov - a tuple (governer string, idx) for governer 
                2-Tuple dependent - tuple (dependent string, idx) for dependent
        """
        #For a list of dependency types used see http://universaldependencies.github.io/docs/en/dep/all.html
        self.dtype = dtype
        self.gov = gov 
        self.dependent = dependent

    def gov_id(self):
        return self.gov[1]

    def gov_word(self):
        return self.gov[0]

    def dependent_id(self):
        return self.dependent[1]

    def dependent_word(self):
        return self.dependent[0]

class CorrectionFeatures:   
    'Creates and stores features for a verb phrase error and correction, can be used as a baseclass for other feature vectors'
    def __init__(self, createfrom, s):
        """
        CorrectionFeatures can be created from scratch (when createfrom is a CorrectionPair)
        or can be created from an exsisting CorrectionFeature object (when createfrom is a CorrectionFeature)
        @params: 
            CorrectionPair pair     
            Sentence s - the sentence in which verb appears in 

        """
        if isinstance(createfrom, CorrectionPair): #create from scratch
            pair = createfrom
            self.sentence = s
            self.instance = pair
            self.fvect = self.create_fvect() #holds all features
            self.target = self.get_target()  #target feature (label of instance)
        elif isinstance(createfrom, CorrectionFeatures):
            self.sentence = createfrom.sentence
            self.instance = createfrom.instance 
            self.fvect = self.create_fvect(createfrom.fvect)
            self.label = self.get_target()

    def create_fvect(self, createfrom=None): 
        """
            adds features to feature vector, this function does not add labels, that is up to 
            classes that derive from the CorrectionFeatures class
            @params
                list createfrom - a feature vector list to base this feature vector on (append to createfrom)
        """
        if createfrom:
            fvect = createfrom
        else:
            fvect = []

        corr = self.instance.correction
        error = self.instance.error
        #extract data needed for features
        subj = self.sentence.get_subject_token()[0]
        left = self.sentence.get_token_left(error.first().tid)
        right = self.sentence.get_token_right(error.last().tid)

        left2 = self.sentence.get_token_left(left.tid)
        left3 = self.sentence.get_token_left(left2.tid)
        left4 = self.sentence.get_token_left(left3.tid)
        right2 = self.sentence.get_token_right(right.tid)
        right3 = self.sentence.get_token_right(right2.tid)
        right4 = self.sentence.get_token_right(right3.tid)

        leftnoun = closest_noun(error.first(), self.sentence, True)
        rightnoun = closest_noun(error.last(), self.sentence, False)
        gov_tuple = self.sentence.get_gov(error.head().tid)
        gov_token = self.sentence.get_token(gov_tuple[1])
        governee_list = self.sentence.get_governees(error.head().tid)
        governee_tuple = governee_list[0]
        governee_token = self.sentence.get_token(governee_tuple[1])
        prevphrase = prev_vphrase(error, self.sentence)

        ladv = time_adverb(error.first(), self.sentence, True)
        radv = time_adverb(error.last(), self.sentence, False)

        governee_rels = [x[0] + "governeerel" for x in governee_list]
        governees = [self.sentence.get_token(x[1]).abbv_to_word() + "governee" for x in governee_list]
        governeespos = [self.sentence.get_token(x[1]).pos + "governee" for x in governee_list]

        det = self.sentence.get_det(subj.tid) 

        vnet_classes = verbnet.classids(error.head().lemma)
        if not vnet_classes:
            vnet_class = []
        else:
            vnet_class = ["".join([x for x in classes if str.isalpha(x)]) for classes in vnet_classes]
            vnet_class = [x + "class" for x in vnet_class]

        if prevphrase:
            prevhead = prevphrase.head()
            c = verbnet.classids(prevhead.lemma)
            if not c:   
                prevclass = None 
            else:
                prevclass = c[0] 
                prevclass = "".join([x for x in prevclass if str.isalpha(x)])
            prevaspect = get_aspect(prevphrase)
        else:
            prevhead = None
            prevclass = None  
            prevaspect = None

        fvect.append(error.head().abbv_to_word() + "self")
#       fvect.extend(vnet_class)

        if prevhead:    
            fvect.append(prevhead.abbv_to_word() + "prevword")
            fvect.append(prevhead.pos + "prevpos")
#       if prevclass:
#           fvect.append(prevclass + "prevclass")
        if prevaspect:
            fvect.append(prevaspect + "prevaspect")

#       fvect.append(right2.abbv_to_word())
#       fvect.append(left2.abbv_to_word())
#       fvect.append(right2.pos)
#       fvect.append(left2.pos)

#       fvect.append(right3.word + "right")
#       fvect.append(left3.word + "left")
#       fvect.append(right3.pos + "right")
#       fvect.append(left3.pos + "left")
#
#       fvect.append(right4.word + "right")
#       fvect.append(left4.word + "left")
#       fvect.append(right4.pos + "right")
#       fvect.append(left4.pos + "left")

        fvect.append(right.abbv_to_word() + "right")
        fvect.append(right.pos + "right")
        fvect.append(left.abbv_to_word() + "left")
        fvect.append(left.pos + "left")


        fvect.append(subj.pos + "subj")
        fvect.append(subj.abbv_to_word() + "subjlem")
        fvect.append(str(subj.noun_person()) + "subj")
        fvect.append(str(subj.singular_noun()) + "subj")
#       fvect.append(det.word + "det")
        fvect.append(str(self.sentence.ispassive()) + "passive")
#       if leftnoun.isvalid():
#           fvect.append(str(leftnoun.singular_noun()) + "leftn")
#           fvect.append(str(leftnoun.noun_person()) + "leftn")
#       fvect.append(leftnoun.pos + "leftn")
#           fvect.append(leftnoun.abbv_to_word() + "leftn")
#       if rightnoun.isvalid():
#           fvect.append(str(rightnoun.noun_person()) + "rightn")
#           fvect.append(str(rightnoun.singular_noun()) + "rightn")
#       fvect.append(rightnoun.pos + "rightn")
#           fvect.append(rightnoun.abbv_to_word() + "rightn")
#       fvect.extend(governee_rels)
#       fvect.extend(governees)
#       fvect.extend(governeespos)

        fvect.append(gov_token.word + "gov")
        fvect.append(gov_token.pos + "gov")
        fvect.append(gov_tuple[0] + "govrel")
        fvect.append(governee_token.word + "governee")
        fvect.append(governee_token.pos + "governee")
        fvect.append(governee_tuple[0] + "governeerel")
        if ladv.isvalid():
            fvect.append(ladv.word + "adverb")
        if radv.isvalid():
            fvect.append(radv.word + "adverb")

        return fvect

    def get_target(self):
        return 'NO TARGET FEATURE'
    
        
#ids for feature type so methods can indicate which type of features they want
ASPECT_FEATS = 1
PERSON_NUM_FEATS = 2

class AspectFeatures(CorrectionFeatures):   
    'Feature vector where tense/aspect is used as a label'
    def __init__(self, createfrom, s):
        """
        AspectFeatures can be created from scratch (when createfrom is a CorrectionPair)
        or can be created from an exsisting CorrectionFeature object (when createfrom is a CorrectionFeature)
        """
        CorrectionFeatures.__init__(self, createfrom, s)

    def create_fvect(self, createfrom=None): 
        if createfrom:
            fvect = createfrom
        else: 
            fvect = CorrectionFeatures.create_fvect(self) 

        fvect.append(get_vchain_labels(self.instance.error)[0] + "origLabel") #put original verb phrase aspect down as feature
        return fvect

    def get_target(self):
        #insert label at end
        err_label = get_vchain_labels(self.instance.error)[0]
        corr_label = get_vchain_labels(self.instance.correction)[0]
        #if err_label and err_label != 'ERROR' and not err_label.isspace():
        if valid_label(err_label) and valid_label(corr_label):
           return corr_label #label
        else:
            return 'ERROR'

class PersonNumFeatures(CorrectionFeatures):   
    'Feature vector where person/number is used as a label'
    def __init__(self, pair, s):
        """
        PersonNumFeatures can be created from scratch (when createfrom is a CorrectionPair)
        or can be created from an exsisting CorrectionFeature object (when createfrom is a CorrectionFeature)
        """
        CorrectionFeatures.__init__(self, createfrom, s)

    def create_fvect(self, createfrom=None): 
        if createfrom:
            fvect = createfrom
        else: 
            fvect = CorrectionFeatures.create_fvect(self) 

        fvect.append(get_vchain_labels(self.instance.error)[1] + "origLabel") #put original verb phrase aspect down as feature
        return fvect

    def get_target(self):
        #insert label at end
        err_label = get_vchain_labels(self.instance.error)[1]
        corr_label = get_vchain_labels(self.instance.correction)[1]
        #if err_label and err_label != 'ERROR' and not err_label.isspace():
        if valid_label(err_label) and valid_label(corr_label):
           return corr_label #label
        else:
            return 'ERROR'


#------------------------------------------------------------
#       Various general helping functions
#-----------------------------------------------------------
def get_aspect(vseq):
    """Find the aspect of a verb chain vseq (represented as VChain object)"""
    filtered = [x for x in vseq.chain if (x.isverb() and x.pos != 'MD')]
    if vseq.first().pos == 'TO' and vseq.length > 1:
        aspect = 'INF'
    elif len(filtered) == 1: #only 1 non model verb
        if filtered[0].pos == 'VBD' or filtered[0].pos == 'VBN':    
            aspect = 'PA_SIMPLE'
        else:
            aspect = 'PR_SIMPLE'
    else:
        seq = vseq.fst_sequence()
        transducer = fst.forgiving_vchain_transducer()
        aspect_list = transducer.transduce(seq)
        if 'ERROR' in aspect_list:
            aspect = 'ERROR'
        else:
            temp = ['PL', 'SING', '1ST', '3RD'] #these two lines added for testing
            aspect_list = [x for x in aspect_list if x not in temp]
            
            aspect = "_".join(aspect_list)
    return aspect

def valid_label(label):
    """Return true if string label is valid (not empty of full of spaces or equal to ERROR)"""
    if label and label != 'ERROR' and not label.isspace():
        return True
    else:
        return False

def get_vchain_labels(vseq):
    """Get the labels for a verb chain. Labels are the tense/aspect, and person/number
        @params:
            VChain vseq - verb chain to find labels for
        @ret:
            tuple labels - tuple of labels, (tense/aspect, person/number)
    """
    #a value of ERROR indicates no value for the property, the reason for this may or may not be due to an error
    filtered = [x for x in vseq.chain if (x.isverb() and x.pos != 'MD')]
    aspect=''
    person_number=''
    #check for other possible aspects
    if vseq.first().pos == 'TO' and vseq.length > 1:
        aspect = 'INF'
        person_number = 'ERROR'
    elif len(filtered) == 1: #only 1 non model verb
        if filtered[0].pos == 'VBD' or filtered[0].pos == 'VBN':    
            aspect = 'PA_SIMPLE'
            person_number = 'ERROR'
        else:
            aspect = 'PR_SIMPLE'
            if filtered[0].pos == 'VBZ':
                person_number = '3RD'
            else:
                person_number = '1ST'

    else:
        seq = vseq.fst_sequence()
    #    transducer = fst.forgiving_vchain_transducer()
        transducer = fst.vchain_transducer()
        labels_list = transducer.transduce(seq)
        if 'ERROR' in labels_list:
            labels = ('ERROR', 'ERROR')
        else:
            number_labels = ['PL'] #dont include SING since its implied if PL is not present 
            person_labels = [ '1ST', '3RD']
            aspect_list = [x for x in labels_list if x not in number_labels and x not in person_labels]

            person_list = [x for x in labels_list if x in person_labels]
            number_list = [x for x in labels_list if x in number_labels]

            person_list.extend(number_list) 
            aspect = "_".join(aspect_list)
            person_number = "_".join(person_list)
    return (aspect, person_number)

def generate_aspect(seq):
    transducer = fst.vchain_generator()
    aspect = " ".join(transducer.transduce(seq))
    return aspect

def last_in_sentence(tok, sentence):
    index = tok.tid
    index = index + 1   
    last = True
    while not (index >= len(sentence.sen)):
        temptok = sentence.get_token(index)
        if temptok.isverb():
            last = False
        index = index + 1
    return last

def time_adverb(tok, sentence, left=False):
        """look for time adverb to the left/right of tok in sentence"""
        adverb_list = ['now', 'then', 'today', 'tomorrow', 'tonight', 'yesterday', 'usually', 
                        'later', 'yet', 'still', 'already' 'recently', 'sometimes', 'always', 'ago']
        index = tok.tid 
        if left:
            index = index - 1
            while not (index <= 0):
                temptok = sentence.get_token(index)
                if temptok.word.lower() in adverb_list:
                    return temptok
                else:
                    index = index - 1
        else: #search right
            index = index + 1
            while not (index >= len(sentence.sen)):
                temptok = sentence.get_token(index)
                if temptok.word.lower() in adverb_list:
                    return temptok
                else:
                    index = index + 1

        return NullToken() #return null if no time adverb in sentence
    
def prev_vphrase(vphrase, sentence):
    """return the previous verb phrase"""
    chains = sentence.get_vchains()
    if vphrase.position == 0:
        if sentence.prev and sentence.prev.get_vchains():
            prevchains = sentence.prev.get_vchains()
            return prevchains[len(prevchains) - 1] 
        else:
            return None
    elif vphrase.position > 0:
        return chains[vphrase.position - 1]
    else:
        return None
        
def closest_nonverb(tok, sentence, left=False):
    """Helping function to return the nonverb/nonadverb token that is closest to 
        tok in the Sentence object sentence.
        If left = True, then look left, else look right
    """
    index = tok.tid
    closest_tok = NullToken() 
    if left:
        index = index - 1
        while not (index < 0):
            temptok = sentence.get_token(index)
            if temptok.pos[0] != 'V' and temptok.pos[0] != 'R' and (str.isalpha(temptok.word) or temptok.word == '.') and temptok.pos != 'MD':
                closest_tok = temptok
                break
            index = index - 1
    else:
        index = index + 1
        while not (index > len(sentence.sen)):
            temptok = sentence.get_token(index)
            if temptok.pos[0] != 'V' and temptok.pos[0] != 'R' and (str.isalpha(temptok.word) or temptok.word == '.') and temptok.pos != 'MD':
                closest_tok = temptok
                break
            index = index + 1
    return closest_tok

def closest_noun(tok, sentence, left=False):
    """Helping function to return the noun token that is closest to 
        tok in the Sentence object sentence.
        If left = True, then look left, else look right
    """
    index = tok.tid
    closest_tok = NullToken() 
    if left:
        index = index - 1
        while not (index < 0):
            temptok = sentence.get_token(index)
            #if temptok.pos[0] == 'N':
            if temptok.pos[0] == 'N' or temptok.pos == 'PRP' or temptok.pos == 'PRP$':
                closest_tok = temptok
                break
            index = index - 1
    else:
        index = index + 1
        while not (index > len(sentence.sen)):
            temptok = sentence.get_token(index)
            #if temptok.pos[0] == 'N':
            if temptok.pos[0] == 'N' or temptok.pos == 'PRP' or temptok.pos == 'PRP$':
                closest_tok = temptok
                break
            index = index + 1
    return closest_tok

def last_in_chain(tok, sentence):
    """test whether the Token object tok, in the Sentence object sentence
        if the final verb in its respective verb chain
    """
    if not tok.isverb():
        return False
    last = False
    right = sentence.get_token(tok.tid + 1)
    if not right.isverb():
        #if its an adverb, we need to see if there is a verb after it
        if right.pos[0] == 'R':
            if not sentence.get_token(right.tid + 1).isverb(): 
                last = True
        else:
            last = True
    return last
    
def first_in_chain(tok, sentence):
    """test whether the Token object tok, in the Sentence object sentence
        if the first verb in its respective verb chain
    """
    if not tok.isverb():
        return False
    first = False
    left = sentence.get_token(tok.tid - 1)
    if not left.isverb():
        #if its an adverb, we need to see if there is a verb before it
        if left.pos[0] == 'R':
            if not sentence.get_token(left.tid - 1).isverb(): 
                first = True
        else:
            first = True
    return first
         

class Sentence:
    'Holds the data for a instance of a sentence parsed from the xml output of Core NLP'
    def __init__(self, s=None, d=None, pairs=None, prev=None):
        if not s:
            s = []
        if not d:
            d = []
        if not pairs:
            pairs = []
        self.sen = s #sentence is a list of tokens
        self.deps = d #the dependency relations of sentence, a list of Dependency objects
        self.corr_pairs = pairs
        self.prev = prev #previous sentence
    
    def get_token(self, tid): 
        """return token given by token id, return None if out of bounds"""
        if tid > len(self.sen) or tid < 0:
            return NullToken()
        if tid == 0:
            return Token("ROOT", "ROOT", "ROOT", 0)
        else:
            tid = tid-1
            return self.sen[tid]

    def add_word(self, token):
        """Append a token to the sentence"""
        self.sen.append(token)

    def add_dep(self, dep):
        self.deps.append(dep)
    
    def dep_tostring(self):
        """Print the dependency relations in the sentence"""
        for i in self.deps:
            print("{}({}, {})".format(i.dtype, i.gov, i.dependent))

    def tostring(self):
        """Return a single string representation of the words in the sentence"""
        return " ".join([x.word for x in self.sen])
    
    def token_tostring(self):
        """Return a string with all infomation for each token, not just the word"""
        return " ".join("[{}, {}, {}, {}]".format(x.word, x.lemma, x.pos, x.tid) for x in self.sen)
    
    def get_subject_list(self): #do not use this method
        """Return a list of indices of the subject tokens of the sentence"""
        subs = []
        for i in self.deps:
            if i.dtype == 'nsubj' or i.dtype == 'nsubjpass' or i.dtype == 'expl': 
                subs.append(i.dependent_id())
        return list(subs)

    def get_token_left(self, tid):
        curr = tid
        while curr > 0:
            tok = self.get_token(curr - 1)
            if tok.word not in string.punctuation:
                return tok
            else:
                curr = curr - 1
        return NullToken()

    def get_token_right(self, tid):
        curr = tid
        while curr < len(self.sen):
            tok = self.get_token(curr + 1)
            if tok.word not in string.punctuation:
                return tok
            else:
                curr = curr + 1
        return NullToken()
    
        
    def ispassive(self):
        """return true if there is a passive contruct in sentence"""
        p = False   
        for d in self.deps:
            if d.dtype == 'nsubjpass' or d.dtype == 'csubjpass':
                passive = True
                break
        return p

    def get_subject_token(self):
        """Return a list of the subject tokens of the sentence"""
        subs = []
        for i in self.deps:
            if i.dtype == 'nsubj' or i.dtype == 'nsubjpass' or i.dtype == 'expl': 
                subs.append(self.get_token(i.dependent_id()))
        if not subs:
            subs.append(NullToken())
        return list(subs)

    def get_root(self):
        """Return the root of the sentence as a Token object"""
        root = 'None'
        for i in self.deps:
            if i.dtype == 'root':
                root = self.get_token(i.dependent_id())
                break   
        return root

    def get_governees(self, token_index):
        """Return the a list of governees and relations of the token 
            with tid equal to token index
            @ret: list of 2-Tuples with form (relation type, governee id)
        """
        governees = []
        for i in self.deps:
            if i.gov_id() == token_index:
                governees.append((i.dtype, i.dependent_id()))
        if not governees: #no governees for token
            return [('None', -1)]   
        else:
            return governees

    def get_gov(self, token_index): #note that all tokens have a single governor (which may be ROOT)
        """Return the governor of the token with tid equal to token_index
            as well as its relation type.
            @ret: 2-Tuple - (relation type, governor index) 
        """
        for i in self.deps:
            if i.dependent_id() == token_index:
                return (i.dtype, i.gov_id())
        print("Token not found in sentence")
        return False

    def get_det(self, token_index):
        """Return the determiner (surface form) for the token with given index"""
        for i in self.deps:
            if i.dtype == 'det' and i.gov_id() == token_index:
                return self.get_token(i.dependent_id())
        return NullToken() 
    
    def add_pair(self, pair):
        """Add a correction pair to the sentence's corr_pairs list
            @params: CorrectionPair pair
        """
        self.corr_pairs.append(pair)
    
    def add_pairs(self, pairs):
        """Like add_pair but adds a list of CorrectionPairs to corr_pairs"""
        self.corr_pairs = self.corr_pairs + pairs
    
    def print_pairs(self):
        """Print correction pairs of sentence"""
        for i in self.corr_pairs:
            print(i.tostring())
    
    def isdelimited(self):
        if self.corr_pairs:
            return True
        else:
            return False

    def get_vchains(self):
        """Return list of VChain objects for all verb chains in the sentence"""
        chains = []
        started = False #whether we have started building chain
        num_chains = 0
        for tok in self.sen:
            if not started:
                poss = []  #possible chain
            if tok.isverb() or tok.isadverb() or ((not started) and tok.word == 'to' and self.get_token(tok.tid + 1).isverb()): #only accept 'to' if at start of chain 
                started = True
                poss.append(tok)
            else:
                started = False
                #check for possible chain that is not just a single adverb, a 'to' or single modal
                if poss and not (len(poss) == 1 and (poss[0].isadverb() or poss[0].pos == 'TO' or poss[0].pos == 'MD')): 
                    chain = VChain(list(poss), poss[0].tid, poss[len(poss)-1].tid, num_chains)
                    chains.append(chain)
                    num_chains = num_chains + 1
                if tok.pos == 'TO' and self.get_token(tok.tid + 1).isverb(): #if current token is 'to' add it to the start of new chain
                    poss = [tok]
                    started = True
        return chains
                
                
    def get_feats(self, corr=True):
        """Return a list of Correction Features for all verb chains in sentence, if a verb chain is 
            already correct, then its correction is the same as the error, only return features for instances 
            where the correction is equal to the verb chain
            @params:
                corr - Whether to return features as CorrectionFeatures as opposed to regular Features (outdated, has no effect now)
        """
        ret = []
        corr_stack = list(self.corr_pairs)
        corr_stack.reverse()
        for c in self.get_vchains():
            if all(x.in_delim for x in c.chain) and corr_stack: #if verb phrase is an error use the correct label
                if corr_stack[len(corr_stack)-1].error.tostring() == c.tostring(): #only add data where the verb chain and error annotation match
                    corrfeats = CorrectionFeatures(corr_stack.pop(), self)
                    ret.append(corrfeats)
                else:
                    corr_stack.pop()  #just dont use this correction instance if the verb chain/error annotation doesnt match
            else:
                corrfeats = CorrectionFeatures(CorrectionPair(c, c), self)
                ret.append(corrfeats)
        return ret
                    
