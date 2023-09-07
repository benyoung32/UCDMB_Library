import pdf_reader as reader
import tkinter as tk
import tkinter.filedialog
import operator as op
import json
import os

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
folder = ""
files = None

part_numbers = ['1','2','3','4','5']
part_numbers_fancy = ['1st','2nd','3rd','4th','5th']

def openFolder() -> str: 
    # get file info
    answer = tk.filedialog.askdirectory(
            initialdir=os.getcwd(),
            title="Please select a folder:")
    # return filepath
    return answer

def init(dir: str, parts: list[str]) -> None:
    global folder, files
    folder = dir
    parts = findMatches(folder, parts)
    for k,v in parts.items():
        print(k, end = ':\n')
        for n in v:
            print(n)
    for part, files in parts.items():
        combined_doc = reader.combineDocuments(reader.openDocuments(files).values())
        combined_doc.save(folder + '\\' + part + ".pdf")

# given a list of parts and filepath to a folder, return a dict with each part as a key and the value being the corresponding filepath
def findMatches(folder_path:str,parts:list[str]) -> dict[str,str]:
    # find matches for requested parts
    print(matchPart(parts[0]))
    # iterate over subfolders
    folders = reader.getSubFolders(folder_path)
    part_dict = {}
    # get all files in listed folders
    for folder in folders:
        files = reader.getSubFiles(folder, [], ignore_altered=False,recursive=False)
        if len(files) == 0: # no files found
            print("no pdf files found: " + os.path.basename(os.path.normpath(folder)))
            continue
        removed_chars = ['\\','/',':','.','_','-','bb','Bb','&','+']
        cleaned_files = [None] * len(files) # list of filenames with base path and separated into words
        for i in range(len(files)):
            # print(i)
            cleaned_files[i] = os.path.basename(os.path.normpath(files[i]))
            for rm in removed_chars:
                cleaned_files[i] = cleaned_files[i].replace(rm, ' ')
        # print(cleaned_files)
        filtered = common_words_filter(cleaned_files)
    # combine part names into dict with filename 
        for i in range(len(filtered)):
            # print(filtered[i] + ', ' + files[i])
            name = matchPart(filtered[i])
            if name in part_dict.keys():
                part_dict[name].append(files[i])
            else:
                part_dict[name] = [files[i]]
    # for k,v in part_dict.items():
    #     print(k, end = ':\n')
    #     for n in v:
    #         print(n)
    # successfully found parts
    found_parts = {}
    for part in parts:
        part = matchPart(part)
        part_number = part[-1]
        part_name = part[0:-2]
        print(part,part_number,part_name)
        # no part number specified, return all parts
        if part_number == str(0):
            found_parts[part_name] = []
            for n in [0,*part_numbers]:
                part = part_name + " " + str(n)
                # print(part)
                if part in part_dict.keys():
                    found_parts[part_name].extend(part_dict[part]) 
        else: # return only part specified
            if part in part_dict.keys():
                found_parts[part] = part_dict[part]
    return found_parts

# given part name, try to find match in alias
def matchPart(part_name:str) -> str:
    part_name = part_name.lower()
    # check last character for part number
    part_number = 0
    if part_name[-1] in part_numbers:
        part_number = part_name[-1]
        part_name = part_name[0:-2]
    for p, names in alias.items():
        for n in names:
            if part_name == n:
                return p + " " + str(part_number)
    print('NO PART NAME FOUND FOR:', part_name)
    return "nan"

def common_words_filter(strings:list[str]):
    my_word_count = {}
    REMOVE = len(strings) + 1
    for string in strings:
        words = string.split()
        for i in range(len(words)-1,0,-1):
            word = words[i].lower()
            if word.split()[0] in ['saxophone', 'sax', 'bugle', 'drum', 'drums', 'horn']: # recombine "descriptor" words into preceding word
                my_word_count[word] = REMOVE # essentially delete this word
                words[i-1] = words[i-1] + ' ' + word # append this word to next
            elif word in alias_flat: # make sure that words like saxophone or other identifying words make it through
                my_word_count[word] = 1 # make sure that the word gets through
            elif word in part_numbers: # combine part numbers into preceding word, e.g. [...'saxophone', '1'] -> [...,'saxophone 1', ...]
                words[i-1] = words[i-1] + ' ' + word # append this word to previous   
                my_word_count[word] = REMOVE # essentially delete this word 
            elif word in part_numbers_fancy:
                my_word_count[word] = REMOVE # delete this word
                if words[i+1].split()[0] in alias_flat: # if the following word is a proper part name, join this word into that one
                    my_word_count[words[i+1]] = REMOVE
                    words[i+1] =  words[i+1] + " " + word[0]
                    my_word_count[words[i+1]] = 1
            else:
                my_word_count[word] = my_word_count.get(word, 0) + 1
    return [word for word in my_word_count if my_word_count[word] < len(strings)-1] # keep word as long as its not in all strings

def readRequest(request_filepath:str) -> list[str]:
    reqs = []
    with open(request_filepath) as file:
        while line := file.readline():
            reqs.append(line.strip())
    return reqs


if __name__ == "__main__":
    # init(openFolder())
    # init("C:\\Users\\Ben\\Downloads\\ADJ_Everybody Talks - Ty Pon-20230907T050832Z-001")
    parts = readRequest('request.txt')
    print(parts)
    init("C:\\Users\\Ben\\Downloads\\folder", parts)
    # print(reader.getSubFolders("C:\\Users\\Ben\\Downloads\\folder", []))

