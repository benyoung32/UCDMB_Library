import pdf_reader as reader
import tkinter as tk
import itertools
import tkinter.filedialog
import json
import os
import argparse
import sys

ALIAS_FILE = "alias.json"
SUBSTITUTION_FILE = 'substitution.json'
ERROR_PATH = 'no_match'
f = open(ALIAS_FILE)
alias = json.load(f)
f = open(SUBSTITUTION_FILE)
subs = json.load(f)
alias_flat = []# all alias words in list
for k,v in alias.items():
    for s in v:
        alias_flat.append(s)
folder = ""
files = None

PART_NUMBERS = ['1','2','3','4','5']
PART_NUMBERS_FANCY = ['1st','2nd','3rd','4th','5th']
REMOVED_CHARS = ['\\','/',':','.','_','-','bb','Bb','&','+','pdf']
IGNORED_WORDS = []
def openFolder() -> str: 
    # get file info
    answer = tk.filedialog.askdirectory(
            initialdir=os.getcwd(),
            title="Please select a folder:")
    # return filepath
    return answer

def init(dir: str, parts: list[str], output:str) -> None:
    global folder, files
    folder = dir
    found_parts = findMatches(folder, parts)
    # print(found_parts)
    for k,v in found_parts.items():
        print(k, end = ':\n')
        for n in v:
            print(n)
    for part, files in found_parts.items():
        # strip errored files our before sending to reader
        changed_files = [file for file in files if file != ERROR_PATH]
        # print(changed_files)
        combined_doc = reader.combineDocuments(reader.openDocuments(changed_files).values())
        combined_doc.save(output + '\\' + part + ".pdf")

# given a list of parts and filepath to a folder, return a dict with each part as a key and the value being the corresponding filepath
def findMatches(folder_path:str,parts:list[str]) -> dict[str,str]:
    # iterate over subfolders
    folders = reader.getSubFolders(folder_path)
    part_dict = {}
    # get all files in listed folders
    for i in range(len(parts)):
        parts[i] = matchPart(parts[i])
    for folder in folders:
        files = reader.getSubFiles(folder, [], ignore_altered=False,recursive=False)
        if len(files) == 0: # no files found
            print("no pdf files found: " + os.path.basename(os.path.normpath(folder)))
            continue
        new_part_dict = getPartNameFromPath(files,parts)
        # print(new_part_dict)
        for k,v in new_part_dict.items():
            if k in part_dict.keys():
                part_dict[k].append(v)
            else:
                part_dict[k] = [v]
    return part_dict

# given part name, try to find match in alias
def matchPart(part:str) -> str:
    if part == '':
        return 'nan'
    part_name = part.split()[0].lower().strip()
    # check for saxophone
    words = part.split()
    if len(words) > 1 and words[1] in ['sax','saxophone']:
        part_name = part_name + ' saxophone'
    # check last character for part number
    part_number = 0
    if part[-1] in PART_NUMBERS:
        part_number = part[-1]
        # part_name = part_name[0:-1].strip()
    # print(part_name, part_number, part)
    for p, names in alias.items():
        for n in names:
            if part_name == n:
                return p + " " + str(part_number)
    print('NO PART NAME FOUND FOR:', part_name)
    return "nan"

def getPartNameFromPath(paths:list[str], parts:list[str]) -> dict[str,str]:
    cleaned_files = [None] * len(paths)
    for i in range(len(paths)):
        cleaned_files[i] = os.path.basename(os.path.normpath(paths[i]))
        for rm in REMOVED_CHARS:
            cleaned_files[i] = cleaned_files[i].replace(rm, ' ')
            cleaned_files[i] = cleaned_files[i].strip()
    part_dict = {}
    for i in range(len(paths)):
        words = cleaned_files[i].split()
        name_extra = ''
        instrument = ''
        part_number = ' 1'
        # print(words)
        for j in range(len(words)-1,-1,-1):
            word = words[j].lower()
            # print(word)
            if word in IGNORED_WORDS: # ignored words
                pass
            elif word in ['saxophone', 'sax', 'bugle', 'drum', 'drums', 'horn']: # recombine "descriptor" words into preceding word
                name_extra = ' ' + word
            elif word in alias_flat: # make sure that words like saxophone or other identifying words make it through
                instrument = word # make sure that the word gets through
            elif word in PART_NUMBERS or word in PART_NUMBERS_FANCY: # combine part numbers into preceding word, e.g. [...'saxophone', '1'] -> [...,'saxophone 1', ...]
                part_number = ' ' + word[0]
        part_name = ''.join([instrument,name_extra,part_number])
        # print(matchPart(part_name))
        part_dict[matchPart(part_name)] = paths[i]
    found_parts = {}
    # print(part_dict)
    for part in parts:
        part_number = part[-1]
        part_name = part[0:-2]
        # print(part,part_number,part_name)
        # no part number specified, return all parts
        if part_number == str(0):
            found_parts[part_name] = ' '
            for n in [0,*PART_NUMBERS]:
                try_part = part_name + " " + str(n)
                # print(part)
                if try_part in part_dict.keys():
                    found_parts[part_name] = part_dict[try_part] 
        else: # return only part specified
            print
            if part in part_dict.keys():
                found_parts[part] = part_dict[part]
            else:
                # print('substitute')
                while int(part_number) > 0:
                    try_part = part_name + ' ' + part_number
                    # print('trying:', part)
                    try:
                        found_parts[part] = part_dict[try_part]
                        # print('found',part)
                        break
                    except:
                        part_number = str(int(part_number) - 1)
                print(part_number)
                if part_number == '0':
                    print('no file found for:', part)
                    found_parts[part] = [ERROR_PATH]
        # if found_parts[part] == []:
        #     found_parts[part] = ERROR_PATH
    # print(found_parts)
    return found_parts # keep word as long as its not in all strings

def readRequest(request_filepath:str) -> list[str]:
    reqs = []
    with open(request_filepath) as file:
        while line := file.readline():
            reqs.append(line.strip())
    return reqs


if __name__ == "__main__":
    # init(openFolder())
    # init("C:\\Users\\Ben\\Downloads\\ADJ_Everybody Talks - Ty Pon-20230907T050832Z-001")
    parser = argparse.ArgumentParser(sys.argv[0])
    parser.add_argument('folder list',type=str,default="C:\\Users\\benyo\\Downloads\\folder")
    parser.add_argument('request list',type=str,default='request.txt')
    parser.add_argument('output',type=str,default=os.getcwd())
    folder, parts, output = vars(parser.parse_args()).values()
    print(vars(parser.parse_args()))
    # print(parser.parse_args())
    print(folder, parts, output)
    parts = readRequest(parts)
    for i in range(len(parts)):
        parts[i] = matchPart(parts[i])
    print(parts)
    init(folder, parts, output)
    # init("C:\\Users\\benyo\\Downloads\\folder\\Roaring 20's", parts)
    # print(reader.getSubFolders("C:\\Users\\Ben\\Downloads\\folder", []))