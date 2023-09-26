from math import ceil
import shutil
import pdf_reader as reader
import tkinter as tk
import fitz
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
    '''
    Open a system file dialog prompting user to select a folder
    :return: Filepath to selected folder
    '''
    # get file info
    answer = tk.filedialog.askdirectory(
            initialdir=os.getcwd(),
            title="Please select a folder:")
    # return filepath
    return answer

def printDict(dict:dict):
    '''
    For each key in input dict, print each corresponding value 
    on its own line
    :param dict: Dict to print 
    :return: None
    '''
    for k,v in dict.items():
        print(k, end = ':\n')
        if v is list:
            for n in v:
                print(n)
        else:
            print(v)

def main(folderlist: list[str], parts: list[str], output:str, combine:bool = False, move:bool = False) -> None:
    '''
    Find all files corresponding to each part in parts in dir and its subdirs.
    Output results to output path, should be a folder. 
    :param dir: directory to search, including subdirs
    :param parts: list of parts to search for
    :param output: filepath of output folder
    :pararm combine: If true, combine all found parts into one pdf
    :param move: If true, move all found part files into one folder per part
    :return: None
    '''
    # global folderlist, files
    # folderlist = dir
    found_parts = findMatches(folderlist, parts)
    # printDict(found_parts)
    final_combined_doc = fitz.Document()
    unique_parts = list(set(parts))
    unique_parts.sort()
    # insert part to the back
    drums = [matchPart(drum) for drum in ['snare','quads','cymbals','basses']]
    drum_parts = [drum for drum in unique_parts if drum in drums]
    unique_parts = [part for part in unique_parts if part not in drum_parts]
    unique_parts.extend(drum_parts)
    print(unique_parts)
    part_doc_dict = {}
    for part in unique_parts:
        files = found_parts[part]
        # print(files)
        changed_files = [file for file in files if file != ERROR_PATH]
        part_docs = reader.openDocuments(changed_files).values()
        if combine:
            part_doc_dict[part] = part_docs
        if changed_files == []: # check if there are any files
            continue
        combined_doc = reader.combineDocuments(part_docs)
        part_name = part.replace('0', '').strip()
        new_filepath = output + '\\' + part_name + ".pdf"
        if move:
            new_folder = output + '\\' + part_name
            try:
                os.mkdir(new_folder)
            except:
                print('folder already exists')
            i = 1
            for file in changed_files:
                shutil.copy(file, new_folder + '\\' + os.path.basename(file))

        reader.saveDocument(combined_doc, new_filepath, '', close = False)
    if combine:
        for part in unique_parts:
            # drums = [matchPart(drum) for drum in ['snare','quads','cymbals','basses']]
            # print every count of drums because their pages are whole pages, not halves
            if part in drums:
                count = parts.count(part)
            else:
                count = ceil(parts.count(part) / 2)
            # for each requested song, put each part count times
            for j in range(len(folderlist)):
                part_docs = list(part_doc_dict[part])
                if part_docs != []:
                    for i in range(count):
                        final_combined_doc.insert_pdf(part_docs[j])
        final_combined_doc.save(output + '\\all_parts' + '.pdf')

def findMatches(folder_paths:list[str],parts:list[str]) -> dict[str,str]:
    '''
    From a list of folders, folder_paths, and a list of parts
    find a match from each folder for each part in parts.
    :param folder_paths: list of folder paths to search in
    :param parts: list of parts to search for
    :return: Returns a dictionary with a key for each part with value
    containing list of found parts 
    '''
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
            print("no pdf files found: " + os.basename(os.path.normpath(folder)))
            continue
        new_part_dict = getPartNameFromPath(files,parts)
        # printDict(new_part_dict)
        for k,v in new_part_dict.items():
            if k not in part_dict.keys():
                part_dict[k] = []
            # print(type(v))
            if type(v) is list:
                # print('sublist')
                for subpath in v:
                    # print(subpath)
                    part_dict[k].append(subpath)
                    # print(part_dict[k])
            else:
                part_dict[k].append(v)
    return part_dict

# given part name, try to find match in alias

def getPartNameFromPath(paths:list[str], parts:list[str]) -> dict[str,str]:
    '''
    From list of filepaths, paths, matches each path to a part name,
    searching for parts in parts list
    :param paths: list of paths to match to a part name
    :param parts: list of parts to search for
    :return: Returns a dict with a key for each part in parts, 
    with a list of matching paths as the value
    '''
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
    for part in parts:
        part_number = part[-1]
        part_name = part[0:-2]
        # no part number specified, return all parts
        if part_number == str(0):
            found_parts[part] = []
            for n in [0,*PART_NUMBERS]:
                try_part = part_name + " " + str(n)
                if try_part in part_dict.keys():
                    found_parts[part].append(part_dict[try_part]) 
            if found_parts[part] == []:
                print('|| WARNING || no file found for:', part,
                      'in folder:','\"' + os.path.dirname(os.path.normpath(paths[0])) + '\"')
                found_parts[part] = ERROR_PATH
        else: # return only part specified
            if part in part_dict.keys():
                found_parts[part] = part_dict[part]
            else:
                while int(part_number) > 0:
                    try_part = part_name + ' ' + part_number
                    try:
                        found_parts[part] = part_dict[try_part]
                        break
                    except:
                        part_number = str(int(part_number) - 1)
                if part_number == '0':
                    print('|| WARNING || no file found for:', part,
                      'in folder:','\"' + os.path.dirname(os.path.normpath(paths[0]) + '\"'))
                    found_parts[part] = ERROR_PATH
        # if found_parts[part] == []:
        #     found_parts[part] = ERROR_PATH
    return found_parts # keep word as long as its not in all strings

def matchPart(part:str, quiet:bool = False, pretty = False) -> str:
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
    if pretty:
        if str(part_number) == '0':
            pnumstr = ''
        else:
            pnumstr = str(part_number)
        return (' '.join([part_name, pnumstr])).title()
            
    else:
        return ' '.join([part_name, str(part_number)])


def readFile(filepath:str) -> list[str]:
    '''
    Open and read input filepath line by line into a list
    :param filepath: file to read
    :return: A list containing each line of the file at filepath
    '''
    reqs = []
    with open(filepath) as file:
        while line := file.readline():
            reqs.append(line.strip())
        file.close()
    return reqs

if __name__ == "__main__":
    # init(openFolder())
    # init("C:\\Users\\Ben\\Downloads\\ADJ_Everybody Talks - Ty Pon-20230907T050832Z-001")
    parser = argparse.ArgumentParser(sys.argv[0])
    parser.add_argument('folder list',type=str,
                help = '''Filepath to text file containing on each line 
                        a folder to search through.
                        Subfolders will also be searched''')
    parser.add_argument('request list',type=str,
                        help = '''Filepath to text file containing on 
                        each line a part to find.
                        If using combine, duplicate parts will be included 
                        multiple times in final output file''')
    parser.add_argument('output',nargs='?',type=str,default='./output',
                        help = '''Filepath to folder to store output files''')
    parser.add_argument('-c',dest ='combine',action='store_true',
                        help = 'Combine found files into one file')
    parser.add_argument('-m',dest = 'move',action='store_true',
                        help= 'Copy found files into one folder per part')
    print(parser.parse_args())
    folderlist, partlist, outputfolder, combine, move = vars(parser.parse_args()).values()
    partlist = readFile(partlist)
    if folderlist in ['p','prompt']:
        folders = [openFolder()]
    else:
        folders = readFile(folderlist)
    for i in range(len(partlist)):
        partlist[i] = matchPart(partlist[i])
    partlist = [part for part in partlist if part != ERROR_PART]
    # partlist.sort()
    # print(partlist)
    main(folders, partlist, outputfolder, combine, move)
    # init("C:\\Users\\benyo\\Downloads\\folder\\Roaring 20's", parts)