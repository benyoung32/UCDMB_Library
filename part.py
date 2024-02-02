import sys
import json

ERROR_PART = 'nan 0'
PART_NUMBERS = ['1','2','3','4','5']
PART_NUMBERS_FANCY = ['1st','2nd','3rd','4th','5th']
KEY = ['bb', 'f', 'eb', 'ab', 'c']
DECORATOR = ['horn', 'sax']
FLUFF = ['in']

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # print('running in a PyInstaller bundle')
    ALIAS_FILE = ".\\_internal\\alias.json"
    SUBSTITUTION_FILE = '.\\_internal\\substitution.json'
else:
    # print('running in a normal Python process')
    ALIAS_FILE = "alias.json"
    SUBSTITUTION_FILE = 'substitution.json'


f = open(ALIAS_FILE)
alias = json.load(f)
f = open(SUBSTITUTION_FILE)
subs = json.load(f)
alias_flat = []# all alias words in list
for k,v in alias.items():
    for s in v:
        alias_flat.append(s)
class Part:
    def __init__(self, raw_string: str):
        '''
        Finds a matching standardized part name from input part 
        using a part name alias
        :param part: Input part name string
        :param quiet: If true, do not print warning messages
        :param pretty: If true, return part name in "prettier format",
        e.g. hanging 0 is removed, words capitalized
        :return: Returns matching part name, or ERROR_PART if 
        no match could be found
        '''
        self.decorator = ''
        self.instrument = 'nan'
        self.part_number = '0'
        if raw_string == '': return
        remainder = []
        for word in raw_string.lower().strip().split():
            if word in PART_NUMBERS or PART_NUMBERS_FANCY:
                self.part_number = word
            elif word in KEY:
                self.key = word
            elif word in DECORATOR:
                self.decorator = word
            elif word in FLUFF:
                continue
            else:
                remainder.append(word)
        for instrument, aliases in alias.items():
            for a in aliases:
                for word in remainder:
                    if ' '.join(word, self.decorator) == a:
                        self.instrument = instrument
                        break
        else:
            print('NO PART NAME FOUND FOR:', raw_string, file=sys.stderr)
            return 

    def getPartNameFromString(self, input:str) -> str:
        '''
        From string, split up string into words and search
        for matching part name from alias. Works best on filepaths
        :param input: input string
        :return: returns found part name from within input string
        '''
        # first clean file name, remove seperators etc.
        cleaned_input = os.path.basename(os.path.normpath(input))
        cleaned_input = cleaned_input.replace('Piccolo-Flute','Flute')
        for rm in REMOVED_CHARS:
            cleaned_input = cleaned_input.replace(rm, ' ')
            cleaned_input = cleaned_input.strip()
        words = cleaned_input.split()
        name_extra = ''
        instrument = ''
        part_number = ' 1'
        for j in range(len(words)-1,-1,-1):
            word = words[j].lower()
            if word in IGNORED_WORDS: # ignored words
                pass
            elif word in ['saxophone', 'sax', 'bugle', 'drum', 'drums', 'horn', 'bc', 'tc']: # recombine "descriptor" words into preceding word
                name_extra = ' ' + word
            elif word in alias_flat: # make sure that words like saxophone or other identifying words make it through
                instrument = word # make sure that the word gets through
            elif word in PART_NUMBERS or word in PART_NUMBERS_FANCY: # combine part numbers into preceding word, e.g. [...'saxophone', '1'] -> [...,'saxophone 1', ...]
                part_number = ' ' + word[0]
        # print(''.join([instrument,name_extra,part_number]), input)
        return matchPart(''.join([instrument,name_extra,part_number]))

    def matchPart(self, part:str, quiet:bool = False, pretty = False) -> str:

    def getPartNumber(partname:str) -> str:
        for c in partname[::-1]:
            if c in PART_NUMBERS:
                return c
        # if nothing found, return 0
        return '0'