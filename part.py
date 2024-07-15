import sys
import json
import os
import pdb
from typing import Any

ERROR_PART = 'nan 0'
PART_NUMBERS = ['1','2','3','4','5']
PART_NUMBERS_FANCY = ['1st','2nd','3rd','4th','5th']
KEY = ['bb', 'f', 'eb', 'ab', 'c']
DECORATOR = ['horn', 'sax', 'saxophone', 'hn', 'drum', 'drums']
REMOVED_CHARS = ['\\','/',':','.','_','-','&','+','pdf']
FLUFF = ['in']

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # print('running in a PyInstaller bundle')
    ALIAS_FILE = '.\\_internal\\alias.json'
    SUBSTITUTION_FILE = '.\\_internal\\substitution.json'
else:
    # print('running in a normal Python process')
    ALIAS_FILE = 'part_config/alias.json'
    SUBSTITUTION_FILE = 'part_config/substitution.json'


f = open(ALIAS_FILE)
alias = json.load(f)
f = open(SUBSTITUTION_FILE)
subs = json.load(f)
alias_flat = []# all alias words in list
for k,v in alias.items():
    for s in v:
        alias_flat.append(s)

class Part:
    def __init__(self, raw_string: str) -> None:
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
        self.instrument = 'nan'
        self.number = '0'
        self.decorator = ''
        self.key = ''
        if raw_string == '': return
        remainder = []
        for word in raw_string.lower().strip().split():
            if word in PART_NUMBERS or word in PART_NUMBERS_FANCY:
                for c in word:
                    if c in PART_NUMBERS:
                        self.number = c
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
                    test_name = ' '.join([word, self.decorator]).strip()
                    if test_name == a:
                        self.instrument = instrument
                        break
        if self.instrument == 'nan':
            print('NO PART NAME FOUND FOR:', raw_string, file=sys.stderr)
            return
        
    def __key(self) -> tuple[str | Any, str]:
        return (self.instrument, self.number)

    def __hash__(self) -> int:
        return hash(self.__key())

    def __lt__(self, other) -> bool:
        return str(self) < str(other)
        
    def __eq__(self, other) -> bool:
        return str(self) == str(other)    

    def __str__(self) -> str:
        # if self.key: out = ' '.join([self.key, self.instrument]) 
        out = self.instrument
        if self.number != '0': out += ' ' + self.number
        return out.title().strip()

    def __repr__(self) -> str:
        return self.__str__()

def getPartFromFilepath(input:str) -> Part:
    '''
    From string, split up string into words and search
    for matching part name from alias. Works best on filepaths
    :param input: input string
    :return: returns found part name from within input string
    '''
    # first clean file name, remove seperators etc.
    cleaned_input = os.path.basename(os.path.normpath(input))
    cleaned_input = cleaned_input.replace('Piccolo-Flute','Flute')
    for c in REMOVED_CHARS:
        cleaned_input = cleaned_input.replace(c, ' ')
        cleaned_input = cleaned_input.strip()
    return Part(cleaned_input)

def getPartNumber(partname:str) -> str:
    for c in partname[::-1]:
        if c in PART_NUMBERS:
            return c
    # if nothing found, return 0
    return '0'