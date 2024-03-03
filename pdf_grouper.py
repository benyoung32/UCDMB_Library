from math import ceil
import shutil
import pdf_reader as reader
import tkinter as tk
import fitz
import json
import os
import argparse
import sys
import my_file_utils as my_file
from part import *

ERROR_PATH = 'no_match' 
folderlist = ""
files = None

DRUMS = [Part(drum) for drum in ['snare','quads','cymbals','basses']]
PART_NUMBERS = ['1','2','3','4','5']
PART_NUMBERS_FANCY = ['1st','2nd','3rd','4th','5th']
IGNORED_WORDS = ['full']

def getUniqueParts(parts: list[Part]):
    unique_parts = list(set(parts))
    unique_parts.sort()
    # insert part to the back
    drum_parts = [drum for drum in unique_parts if drum in DRUMS]
    unique_parts = [part for part in unique_parts if part not in drum_parts]
    unique_parts.extend(drum_parts)
    return unique_parts

def openPartFiles(unique_parts: list[Part], part_filepaths: dict[Part, str]) -> dict:
    part_doc_dict = {}
    for part in unique_parts:
        files = part_filepaths[part]
        files = [file for file in files if file != ERROR_PATH]
        part_doc_dict[part] = reader.openDocuments(files)
    return part_doc_dict

def combineAndSavePartDocs(instrument_groups: list[list[Part]], part_dict:dict[Part, list[fitz.Document]], output_folder: str) -> None:
    for group in instrument_groups:
        for part in group:
            all_docs = []
            docs = part_dict[part]
            for doc in docs:
                if doc not in all_docs: all_docs.append(doc)
            if (all_docs == []): continue
            combined_doc = reader.combineDocuments(all_docs)
            new_filepath = output_folder + '\\' + str(part) + ".pdf"
            reader.saveDocument(combined_doc, new_filepath, '', close = False)

def moveFiles(parts: list[Part], part_file_dict: dict[Part, str], output_folder:str):
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

def saveGroupJSON(parts: list[Part], part_files: dict[Part, str], 
                  out_filepath = "groups.json") -> None:
    output_dict = {}
    groups = {}
    instrument_groups = groupInstruments(parts)
    for group in instrument_groups:
        lead_instrument = group[0].instrument
        groups[lead_instrument] = {}
        for part in group:
            files = part_files[part]
            if type(files) is not list:
                files = [files]
            groups[lead_instrument][str(part)] = {}
            groups[lead_instrument][str(part)]['files'] = files
            groups[lead_instrument][str(part)]['count'] = parts.count(part)
    output_dict['groups'] = groups
    max_count = 0
    for v in part_files.values():
        max_count = max(max_count, len(v))
    output_dict['song count'] = max_count
    json_str = json.dumps(output_dict, indent=4)
    print(json_str)
    f = open(out_filepath, "w")
    f.write(json_str)
    f.close()
    return

def buildTopBottomDocument(json_path: str) -> fitz.Document:
    f = open(json_path)
    part_json = json.load(f)
    all_part_info = []
    for group in part_json['groups'].values():
        for part, values in group.items():
            docs = reader.openDocuments(values['files'])
            docs = [doc for doc in docs if doc != ERROR_PATH]
            all_part_info.append((Part(part) in DRUMS, values['count'], docs))
            print(Part(part),(Part(part) in DRUMS, values['count'], docs))
    
    total_pages = 0
    for part_info in all_part_info:
        if not part_info[0]:
            for doc in part_info[2]:
                total_pages += part_info[1] * doc.page_count * 0.5
    total_pages = ceil(total_pages)
    print(total_pages)

    final_doc = fitz.Document()
    w, h = fitz.paper_rect('letter').width, fitz.paper_rect('letter').height
    final_doc.new_page(width = w, height = h)
    
    top_rect = final_doc[0].bound()
    bot_rect = final_doc[0].bound()
    top_rect.y1 = top_rect.y1 / 2
    bot_rect.y0 = bot_rect.y1 / 2
    r = top_rect
    page = 0
    top = True
    for part_info in all_part_info: 
        full_page = part_info[0]
        for _ in range(part_info[1]):
            for doc in part_info[2]:
                if full_page:
                    final_doc.insert_pdf(doc)
                    continue
                images = topHalfPixmaps(doc)
                for img in images:
                    print(page, doc)
                    final_doc[page].insert_image(r, pixmap=img)
                    page += 1
                    if page > total_pages - 1:
                        top = False
                        page = 0
                        r = bot_rect
                    if top: final_doc.new_page(width = w, height = h)
    return final_doc

def groupInstruments(parts: list[Part]):
    instrument_groups = []
    group = []
    unique_parts = getUniqueParts(parts)
    for p in unique_parts:
        if group == [] or p.instrument == group[0].instrument:
            group.append(p)
        else:
            instrument_groups.append(group)
            group = [p]
    if group != []: instrument_groups.append(group)
    return instrument_groups

def createCombinedDocument():
    pass

def combineUniqueParts(parts: list[Part], part_doc_dict: dict[Part, str], output = 'all parts.pdf'):
    unique_parts = getUniqueParts(parts)
    final_doc = fitz.Document()
    for part in unique_parts:
        part_docs = list(part_doc_dict[part])
        for doc in part_docs:
            final_doc.insert_pdf(doc)
    reader.saveDocument(final_doc,output, '')

def main(folders: list[str], parts: list[Part], output_folder:str, combine:bool = False, move:bool = False) -> None:
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
    part_files = findPartFiles(folders, unique_parts)
    part_doc_dict = openPartFiles(unique_parts, part_files)
    combineAndSavePartDocs(groupInstruments(unique_parts), part_doc_dict, output_folder)
    if move: moveFiles(part_files, output_folder)
    json_output = output_folder + '\\groups.json'
    saveGroupJSON(parts, part_files, json_output)
    combineUniqueParts(unique_parts, part_doc_dict, output_folder + '\\all_parts' + '.pdf')
    final = buildTopBottomDocument(json_output)
    reader.saveDocument(final, output_folder + '\\all_parts' + '.pdf', '')

def topHalfPixmaps(docs: list[fitz.Document]) -> list[fitz.Pixmap]:
    out = []
    if type(docs) is not list:
        docs = [docs]
    for doc in docs:
        for page in doc:
            r = page.bound()
            r.y1 /= 2
            page.set_cropbox(r)
            out.append(page.get_pixmap(dpi=300))
    return out 

def findPartFiles(folder_paths:list[str],parts:list[Part]) -> dict[Part,str]:
    '''
    From a list of folders (folder_paths) and a list of parts
    find a match from each folder for each part in parts.
    :param folder_paths: list of folder paths to search in
    :param parts: list of parts to search for
    :return: Returns a dictionary with a key for each part with value
    containing list of found parts 
    '''
    folders = []
    part_dict = {}
    # iterate over subfolders
    for path in folder_paths:
        folders = reader.getSubFolders(path)
    for folder in folders:
        files = reader.getSubFiles(folder, [],ignore_prefix= None, recursive=False)
        if len(files) == 0: # no files found
            print("no pdf files found: " + os.path.basename(os.path.normpath(folder)))
            continue
        for k,v in createPartDictFromPaths(files,parts).items():
            if k not in part_dict.keys():
                part_dict[k] = []
            if type(v) is list: 
                for subpath in v: part_dict[k].append(subpath)
            else: part_dict[k].append(v)
    return part_dict

def createPartDictFromPaths(paths:list[str], parts:list[Part]) -> dict[Part,str]:
    '''
    From list of filepaths, paths, matches each path to a part name,
    searching for parts in parts list
    :param paths: list of paths to match to a part name
    :param parts: list of parts to search for
    :return: Returns a dict with a key for each part in parts, 
    with a list of matching paths as the value
    '''
    part_path_dict = {}
    found_parts = {}
    for path in paths:
        part = getPartFromFilepath(path)
        part_path_dict[part] = path
    for part in parts:
        # no part number specified, return all parts
        found_parts[part] = []
        if part.number == str(0): search = [0, *PART_NUMBERS]
        else: search = range(int(part.number), 0-1, -1)
        for n in search:
            try_part = Part(part.instrument + " " + str(n))
            if try_part in part_path_dict.keys():
                found_parts[part].append(part_path_dict[try_part]) 
                if not part.number == str(0): break
        # nothing was found
        if found_parts[part] == []:
            print('|| WARNING || no file found for:', part,
                    'in folder:','\"' + os.path.dirname(os.path.normpath(paths[0])) + '\"')
            found_parts[part] = ERROR_PATH
    return found_parts

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
    folderlist, partlist, outputfolder, combine, move = vars(parser.parse_args()).values()
    partlist = my_file.readFile(partlist)
    if folderlist in ['p','prompt']:
        folders = [openFolder()]
    else:
        folders = my_file.readFile(folderlist)
    for i in range(len(partlist)):
        partlist[i] = Part(partlist[i])
    partlist = [part for part in partlist if part != ERROR_PART]
    main(folders, partlist, outputfolder, combine, move)
    # init("C:\\Users\\benyo\\Downloads\\folder\\Roaring 20's", parts)