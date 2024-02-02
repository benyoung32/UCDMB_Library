from math import ceil
import shutil
from xml.dom.minidom import Document
import pdf_reader as reader
import tkinter as tk
import fitz
import json
import os
import argparse
import sys
from part.py import *

ERROR_PATH = 'no_match' 
folderlist = ""
files = None

REMOVED_CHARS = ['\\','/',':','.','_','-','bb','Bb','&','+','pdf']
IGNORED_WORDS = ['full']

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

def getUniqueParts(parts: list[str]):
    unique_parts = list(set(parts))
    unique_parts.sort()
    # insert part to the back
    drum_parts = [drum for drum in unique_parts if drum in DRUMS]
    unique_parts = [part for part in unique_parts if part not in drum_parts]
    unique_parts.extend(drum_parts)
    return unique_parts

def openPartFiles(unique_parts: list[str], part_filepaths: list[str]) -> dict:
    part_doc_dict = {}
    for part in unique_parts:
        files = part_filepaths[part]
        files = [file for file in files if file != ERROR_PATH]
        part_doc_dict[part] = reader.openDocuments(files).values()
    return part_doc_dict

def combineAndSavePartDocs(part_dict:dict[str, Document], output_folder: str) -> None:
    for part, docs in part_dict.items():
        combined_doc = reader.combineDocuments(docs)
        part_name = part.replace('0', '').strip()
        part_name = matchPart(part_name,True,True).strip()
        new_filepath = output_folder + '\\' + part_name + ".pdf"
        reader.saveDocument(combined_doc, new_filepath, '', close = False)

def moveFiles(parts: list[str], part_file_dict: dict[str, str], output_folder:str):
    for p in parts:
        files = part_file_dict[p]
        files = [file for file in files if file != ERROR_PATH]
        part_name = p.split()[0]
        new_folder = output_folder + '\\' + part_name
        try:
            os.mkdir(new_folder)
        except:
            print('folder already exists')
        i = 1
        for file in files:
            shutil.copy(file, new_folder + '\\' + os.path.basename(file))

def buildTopBottomDocument(parts: list[str], part_doc_dict: dict, ):
    final_page_count = 0
    unique_parts = getUniqueParts(parts)
    for part in unique_parts:
        if part in DRUMS: continue
        for part_doc in part_doc_dict[part]:
            final_page_count += 0.5 * part_doc.page_count * parts.count(part)
    final_page_count = ceil(final_page_count)
    w, h = fitz.paper_rect('letter').width, fitz.paper_rect('letter').height
    final_combined_doc.new_page(width = w, height = h)
    print(final_page_count, len(parts))
    page = 0
    top = True
    top_rect = final_combined_doc[0].bound()
    top_rect.y1 = top_rect.y1 / 2
    bot_rect = final_combined_doc[0].bound()
    bot_rect.y0 = bot_rect.y1 / 2
    r = top_rect
    for _ in range(parts.count(part)): 
        final_combined_doc.insert_pdf(part_docs[j])
    for group in instrument_groups:
        for j in range(len(folderlist)):
            for part in group:
                images = getTopHalf(part_docs[j])
                for p in range(parts.count(part)):
                    # print(p)
                    for img in images:
                        final_combined_doc[page].insert_image(r, pixmap=img)
                        print(part, page)
                        page += 1
                        if page > final_page_count - 1:
                            top = False
                            page = 0
                            r = bot_rect
                        if top: final_combined_doc.new_page(width = w, height = h)

def groupInstruments(parts: list[str]):
    instrument_groups = []
    group = []
    unique_parts = getUniqueParts(parts)
    for p in unique_parts:
        if group == [] or p.split()[0] == group[0].split()[0]:
            group.append(p)
        else:
            instrument_groups.append(group)
            group = [p]
    if group != []: instrument_groups.append(group)
    return instrument_groups

def createCombinedDocument():
    pass

def saveGroupJSON(instrument_groups: list[str], part_files: dict[str, str], 
                  out_filepath = "groups.json") -> None:
    output_dict = {}
    for group in instrument_groups:
        lead_instrument = group[0].split()[0]
        output_dict[lead_instrument] = {}
        for instrument in group:
            files = part_files[instrument]
            if type(files) is not list:
                files = [files]
            output_dict[lead_instrument][instrument] = files
    json_str = json.dumps(output_dict, indent=4)
    print(json_str)
    f = open(out_filepath, "w")
    f.write(json_str)
    f.close()

    return

def main(folders: list[str], parts: list[str], output_folder:str, combine:bool = False, move:bool = False) -> None:
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
    final_combined_doc = fitz.Document()
    unique_parts = getUniqueParts(parts)
    part_files = findMatches(folders, unique_parts)
    part_doc_dict = openPartFiles(unique_parts, part_files)
    combineAndSavePartDocs(part_doc_dict, output_folder)
    if move: moveFiles(part_files, output_folder)
    if not combine: return
    i = 0
    instrument_groups = groupInstruments(parts)
    print(instrument_groups)
    saveGroupJSON(instrument_groups, part_files)
    return
    for group in instrument_groups:
        for j in range(len(folders)):
            for part in group:
                part_docs = list(part_doc_dict[part])
                if j >= len(part_docs): break
                else: 
                    # drums take up whole page, while other parts take half
                    if part in DRUMS: count = parts.count(part)
                    else: count = ceil(parts.count(part) / 2)
                    # for each requested song, put each part count times
                    for i in range(count):
                        final_combined_doc.insert_pdf(part_docs[j])
    reader.saveDocument(final_combined_doc,output_folder + '\\all_parts' + '.pdf','')

def getTopHalf(doc:fitz.Document) -> list[fitz.Pixmap]:
    out = []
    for page in doc:
        r = page.bound()
        r.y1 /= 2
        page.set_cropbox(r)
        out.append(page.get_pixmap(dpi=300))
    return out 

def findMatches(folder_paths:list[str],parts:list[str]) -> dict[str,str]:
    '''
    From a list of folders (folder_paths) and a list of parts
    find a match from each folder for each part in parts.
    :param folder_paths: list of folder paths to search in
    :param parts: list of parts to search for
    :return: Returns a dictionary with a key for each part with value
    containing list of found parts 
    '''
    # iterate over subfolders
    folders = []
    part_dict = {}
    for path in folder_paths:
        folders = reader.getSubFolders(path)
    for folder in folders:
        files = reader.getSubFiles(folder, [],ignore_prefix= None, recursive=False)
        if len(files) == 0: # no files found
            print("no pdf files found: " + os.path.basename(os.path.normpath(folder)))
            continue
        new_part_dict = createPartDictFromPaths(files,parts)
        for k,v in new_part_dict.items():
            if k not in part_dict.keys():
                part_dict[k] = []
            if type(v) is list:
                for subpath in v:
                    part_dict[k].append(subpath)
            else:
                part_dict[k].append(v)
    return part_dict

def createPartDictFromPaths(paths:list[str], parts:list[str]) -> dict[str,str]:
    '''
    From list of filepaths, paths, matches each path to a part name,
    searching for parts in parts list
    :param paths: list of paths to match to a part name
    :param parts: list of parts to search for
    :return: Returns a dict with a key for each part in parts, 
    with a list of matching paths as the value
    '''
    part_dict = {}
    for i in range(len(paths)):
        part_name = getPartNameFromString(paths[i])
        part_dict[part_name] = paths[i]
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

def readFile(filepath:str) -> list[str]:
    '''
    Open and read input filepath line by line into a list
    :param filepath: file to read
    :return: A list containing each line of the file at filepath
    '''
    reqs = []
    with open(filepath) as file:
        while line := file.readline():
            line = line.strip()
            line = line.strip("\'\"")
            reqs.append(line.strip())
        file.close()
    return reqs

DRUMS = [matchPart(drum) for drum in ['snare','quads','cymbals','basses']]

if __name__ == "__main__":
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
    # print(parser.parse_args())
    folderlist, partlist, outputfolder, combine, move = vars(parser.parse_args()).values()
    partlist = readFile(partlist)
    if folderlist in ['p','prompt']:
        folders = [openFolder()]
    else:
        folders = readFile(folderlist)
    # print(folders)
    for i in range(len(partlist)):
        partlist[i] = matchPart(partlist[i])
    partlist = [part for part in partlist if part != ERROR_PART]
    # partlist.sort()
    # print(partlist)
    main(folders, partlist, outputfolder, combine, move)
    # init("C:\\Users\\benyo\\Downloads\\folder\\Roaring 20's", parts)