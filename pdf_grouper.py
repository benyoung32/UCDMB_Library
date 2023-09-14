from math import ceil
from numpy import require
import pdf_reader as reader
import tkinter as tk
import fitz
import itertools
import tkinter.filedialog
import json
import os
import argparse
import sys

ALIAS_FILE = "alias.json"
SUBSTITUTION_FILE = 'substitution.json'
ERROR_PATH = 'no_match'
ERROR_PART = 'nan 0'
f = open(ALIAS_FILE)
alias = json.load(f)
f = open(SUBSTITUTION_FILE)
subs = json.load(f)
alias_flat = []# all alias words in list
for k,v in alias.items():
    for s in v:
        alias_flat.append(s)
folderlist = ""
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

def printDict(dict):
    for k,v in dict.items():
        print(k, end = ':\n')
        if v is list:
            for n in v:
                print(n)
        else:
            print(v)

def main(dir: str, parts: list[str], output:str, combine:bool = False) -> None:
    global folderlist, files
    folderlist = dir
    found_parts = findMatches(folderlist, parts)
    # printDict(found_parts)
    final_combined_doc = fitz.Document()
    unique_parts = list(set(parts))
    unique_parts.sort()
    part_doc_dict = {}
    for part in unique_parts:
        files = found_parts[part]
        # print(files)
        changed_files = [file for file in files if file != ERROR_PATH]
        part_docs = reader.openDocuments(changed_files).values()
        combined_doc = reader.combineDocuments(part_docs)
        if combine:
            part_doc_dict[part] = combined_doc
            
        combined_doc.save(output + '\\' + part.replace('0', '').strip() + ".pdf")
    if combine:
        for part in unique_parts:
            count = ceil(parts.count(part) / 2)
            # print(part, ': ', count)
            for i in range(count):
                final_combined_doc.insert_pdf(part_doc_dict[part])
        final_combined_doc.save(output + '\\all_parts' + '.pdf')
# given a list of parts and filepath to a folder, return a dict with each part as a key and the value being the corresponding filepath
def findMatches(folder_paths:list[str],parts:list[str]) -> dict[str,str]:
    # iterate over subfolders
    folders = []
    for path in folder_paths:
        # print(path)
        folders = (reader.getSubFolders(path))
    for folder in folders:
        print(folder)
    part_dict = {}
    # get all files in listed folders
    # for i in range(len(parts)):
    #     parts[i] = matchPart(parts[i])
    for folder in folders:
        files = reader.getSubFiles(folder, [], ignore_altered=False,recursive=False)
        # print(files)
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
def matchPart(part:str, quiet:bool = False) -> str:
    part = part.lower().strip()
    part_name = ERROR_PART
    if part == '':
        return part_name
    words = part.split()
    # words = [word for word in words if word not in ['in','eb','bb','full','ab','c']]
    # print(words)
    # check last word for part number or n/a
    if words[-1] in ['n/a']:
        part_number = 0
        name = ' '.join(words[0:-1])
    else:
        for c in words[-1]:
            if c in PART_NUMBERS:
                part_number = c
                name = ' '.join(words[0:-1])
                break
        else:
            name = part.lower()
            part_number = 0 
    for p, names in alias.items():
        for n in names:
            if name == n:
                part_name = p
                break
    if part_name == ERROR_PART:
        # double check all words for looser match
        for word in words:
            for p, names in alias.items():
                for n in names:
                    if word == n:
                        part_name = p
                        break
                else:
                    continue
            else:
                continue
        # still nothing found
        if part_name == ERROR_PART:
            if not quiet:
                print('NO PART NAME FOUND FOR:', part)
            return ERROR_PART
    return ' '.join([part_name, str(part_number)])

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
        # print(words)
        name_extra = ''
        instrument = ''
        part_number = ' 1'
        for j in range(len(words)-1,-1,-1):
            word = words[j].lower()
            # print(word)
            if word in IGNORED_WORDS: # ignored words
                pass
            elif word in ['saxophone', 'sax', 'bugle', 'drum', 'drums', 'horn', 'bc', 'tc']: # recombine "descriptor" words into preceding word
                name_extra = ' ' + word
            elif word in alias_flat: # make sure that words like saxophone or other identifying words make it through
                instrument = word # make sure that the word gets through
            elif word in PART_NUMBERS or word in PART_NUMBERS_FANCY: # combine part numbers into preceding word, e.g. [...'saxophone', '1'] -> [...,'saxophone 1', ...]
                part_number = ' ' + word[0]
        part_name = ''.join([instrument,name_extra,part_number])
        # print(part_name)
        # print(matchPart(part_name))
        part_dict[matchPart(part_name)] = paths[i]
    found_parts = {}
    # printDict(part_dict)
    # print(parts)
    for part in parts:
        # print(part)
        part_number = part[-1]
        part_name = part[0:-2]
        # no part number specified, return all parts
        if part_number == str(0):
            found_parts[part] = ' '
            for n in [0,*PART_NUMBERS]:
                try_part = part_name + " " + str(n)
                if try_part in part_dict.keys():
                    found_parts[part] = part_dict[try_part] 
            if found_parts[part] == ' ':
                print("no file found for:", part,"in folder:", paths[0])
        else: # return only part specified
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
                # print(part_number)
                if part_number == '0':
                    print('|| WARNING || no file found for:', part)
                    found_parts[part] = [ERROR_PATH]
        # if found_parts[part] == []:
        #     found_parts[part] = ERROR_PATH
    # print(found_parts)
    return found_parts # keep word as long as its not in all strings

def readFile(request_filepath:str) -> list[str]:
    reqs = []
    with open(request_filepath) as file:
        while line := file.readline():
            reqs.append(line.strip())
    return reqs

if __name__ == "__main__":
    # init(openFolder())
    # init("C:\\Users\\Ben\\Downloads\\ADJ_Everybody Talks - Ty Pon-20230907T050832Z-001")
    parser = argparse.ArgumentParser(sys.argv[0])
    parser.add_argument('folder list',type=str, nargs = '?',
                    default="folders.txt")
    parser.add_argument('request list',nargs='?',type=str,default='request.txt')
    parser.add_argument('output',nargs='?',type=str,default='./output')
    parser.add_argument('-c',dest ='combine',action='store_true')
    print(parser.parse_args())
    folderlist, partlist, outputfolder, combine = vars(parser.parse_args()).values()
    partlist = readFile(partlist)
    if folderlist in ['p','prompt']:
        folders = [openFolder()]
    else:
        folders = readFile(folderlist)
    for i in range(len(partlist)):
        partlist[i] = matchPart(partlist[i])
    partlist = [part for part in partlist if part != ERROR_PART]
    partlist.sort()
    print(partlist)
    main(folders, partlist, outputfolder, combine)
    # init("C:\\Users\\benyo\\Downloads\\folder\\Roaring 20's", parts)