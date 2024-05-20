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

all_parts = ['flute', 'clarinet', 'alto', 'tenor', 'baritone sax', 
            'trumpet', 'mellophone','trombone', 'baritone', 'sousaphone',
            'glock', 'snare', 'cymbal', 'quads', 'basses']
SCORE_ORDER = [Part(p) for p in all_parts]


class Packet: 
    '''This class defines a set of songs and parts, with a mapping between each part
    and its corresponding PDF for each song. This is used to build 'packets' which 
    can be printed and distributed.'''
    def __init__(self, parts: list[Part], filepaths: dict[Part, list[str]]) -> None:
        self.parts = parts
        # self.folders = folders
        self.unique_parts = getUniqueParts(parts)
        self.instrument_groups = groupInstruments(self.parts)
        self.sortInstrumentGroupsByScoreOrder()
        self.non_drums = [part for part in self.unique_parts if part not in DRUMS]
        self.drums = [part for part in self.unique_parts if part in DRUMS]
        
        self.filepaths = filepaths
        self.docs = openFiles(self.unique_parts, self.filepaths)
        return
    
    def saveGroupJSON(self, out_filepath = "groups.json") -> None:
        output_dict = {}
        json_groups = {}
        
        max_count = 0
        for v in self.filepaths.values():
            max_count = max(max_count, len(v))
        output_dict['song count'] = max_count

        for group in self.instrument_groups:
            lead_instrument = group[0].instrument
            json_groups[lead_instrument] = {}
            for part in group:
                files = self.filepaths[part]
                if type(files) is not list:
                    files = [files]
                json_groups[lead_instrument][str(part)] = {}
                json_groups[lead_instrument][str(part)]['files'] = files
                json_groups[lead_instrument][str(part)]['count'] = self.parts.count(part)
        output_dict['groups'] = json_groups
                
        json_str = json.dumps(output_dict, indent=4)
        f = open(out_filepath, "w")
        f.write(json_str)
        f.close()
        return
    
    def sortInstrumentGroupsByScoreOrder(self) -> None:
        sorted = []
        for p in SCORE_ORDER:
            for group in self.instrument_groups:
                if (group[0].instrument == p.instrument):
                    sorted.append(group)
        self.instrument_groups = sorted
    def buildDocument(self) -> fitz.Document:
        final_combined_doc = fitz.Document()

        final_page_count = self.getNonDrumPageCount()
        page = 0
        top = True
        w, h = fitz.paper_rect('letter').width, fitz.paper_rect('letter').height
        final_combined_doc.new_page(width = w, height = h)

        top_rect = final_combined_doc[0].bound()
        top_rect.y1 = top_rect.y1 / 2
        bot_rect = final_combined_doc[0].bound()
        bot_rect.y0 = bot_rect.y1 / 2
        r = top_rect

        for group in self.instrument_groups:
            # for i in range(self.getSongCount()):
                for part in group:
                    # some parts may be missing some documents
                    # if i > len(self.docs[part]): break
                    
                    if part in DRUMS:
                        for i in range(self.getSongCount()):
                            for _ in range(self.parts.count(part)):
                                final_combined_doc.insert_pdf(self.docs[part][i])
                        continue
                    
                    # imgs = topHalfPixmaps([self.docs[part][i]])
                    imgs = topHalfPixmaps(self.docs[part])
                    for _ in range(self.parts.count(part)):
                        for img in imgs:
                            final_combined_doc[page].insert_image(r, pixmap=img) # type: ignore
                            print(part, page)
                            page += 1
                            if page > final_page_count - 1:
                                top = False
                                page = 0
                                r = bot_rect
                            if top: final_combined_doc.new_page(width = w, height = h)

        return final_combined_doc

    def getSongCount(self) -> int:
        return max(len(docs) for docs in self.docs.values())

    def getNonDrumPageCount(self) -> int:
        page_count = 0
        for part in self.non_drums:
            for doc in self.docs[part]:
                page_count += 0.5 * doc.page_count * self.parts.count(part)
        return ceil(page_count)

    def saveUniqueParts(self, output_path = 'all parts.pdf'):
        final_doc = fitz.Document()
        for part in self.unique_parts:
            part_docs = list(self.docs[part])
            for doc in part_docs:
                final_doc.insert_pdf(doc)
        reader.saveDocument(final_doc,output_path, '')

    def saveGroupPartDocs(self, output_folder: str) -> None:
        for group in self.instrument_groups:
            for part in group:
                all_docs = []
                docs = self.docs[part]
                for doc in docs:
                    if doc not in all_docs: all_docs.append(doc)
                if (all_docs == []): continue
                combined_doc = reader.combineDocuments(all_docs)
                new_filepath = output_folder + '\\' + str(part) + ".pdf"
                reader.saveDocument(combined_doc, new_filepath, '', close = False)

    def moveFiles(self, output_folder:str):
        for p in self.parts:
            files = self.filepaths[p]
            files = [file for file in files if file != ERROR_PATH]
            part_name = str(p)
            new_folder = output_folder + '\\' + part_name
            try:
                os.mkdir(new_folder)
            except:
                print('folder already exists')
            i = 1
            for file in files:
                shutil.copy(file, new_folder + '\\' + os.path.basename(file))

def getUniqueParts(parts: list[Part]):
    unique_parts = list(set(parts))
    unique_parts.sort()
    # insert drum parts to the back
    drum_parts = [drum for drum in unique_parts if drum in DRUMS]
    unique_parts = [part for part in unique_parts if part not in drum_parts]
    unique_parts.extend(drum_parts)
    return unique_parts

def openFiles(parts: list[Part], 
              filepaths: dict[Part, list[str]]) -> dict[Part, list[fitz.Document]]:
    docs = {}
    for part in parts:
        # skip repeats
        if part not in docs:
            files = filepaths[part]
            files = [file for file in files if file != ERROR_PATH]
            docs[part] = reader.openDocuments(files)
    return docs

def loadJSON(json_path: str) -> Packet:
    f = open(json_path)
    part_json = json.load(f)
    parts = []
    filepaths = {}
    for group in part_json['groups'].values():
        for part_str, values in group.items():
            part = Part(part_str)
            filepaths[part] = values['files']
            for _ in range(values['count']): parts.append(part)
    return Packet(parts, filepaths)

def groupInstruments(parts: list[Part]) -> list[list[Part]]:
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
    # unique_parts = getUniqueParts(parts)
    # filepaths = findPartFiles(folders, unique_parts)
    # packet = Packet(parts, filepaths)
    # part_doc_dict = openFiles(unique_parts, filepaths)
    # packet.combineAndSavePartDocs(output_folder)
    # if move: packet.moveFiles(output_folder)
    # json_output = output_folder + '\\groups.json'
    # packet.saveGroupJSON(json_output)
    # packet.combineUniqueParts(output_folder + '\\all_parts' + '.pdf')
    # final_packet = loadJSON(json_output)
    # reader.saveDocument(packet.buildDocument(), output_folder + '\\all_parts' + '.pdf', '')

def topHalfPixmaps(docs: list[fitz.Document]) -> list[fitz.Pixmap]:
    out = []
    if type(docs) is not list:
        docs = [docs] # type: ignore
    for doc in docs:
        for page in doc:
            r = page.bound()
            r.y1 /= 2
            page.set_cropbox(r)
            out.append(page.get_pixmap(dpi=300))
            r.y1 *= 2
            page.set_cropbox(r)
    return out 

def findPartFiles(folder_paths:list[str],parts:list[Part]) -> dict[Part, list[str]]:
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
    parser.add_argument('folders',type=str,nargs='?', default = '',
                        help = '''Filepath to text file containing on 
                        each line a folder to search through for files matching to 
                        parts contained in the parts file.
                        Subfolders will also be searched''')
    
    parser.add_argument('parts',type=str,nargs='?', default = '',
                        help = '''Filepath to text file containing on 
                        each line a part to find.
                        If using combine, duplicate parts will be included 
                        multiple times in final output file''')
    
    parser.add_argument('output',nargs='?',type=str,default='.\\test',
                        help = '''Filepath to folder to store output files''')
    
    parser.add_argument('-c',dest ='combine',action='store_true',
                        help = 'Combine found files into one file')
    
    parser.add_argument('-m',dest = 'move',action='store_true',
                        help= 'Copy found files into one folder per part')
    
    parser.add_argument('-j', '-json', dest ='json_path',
                        help= '''Load a packet stored in JSON and build the combined documents.
                                Folder list and request list will be ignored''')
    
    args = parser.parse_args()
    output_folder = args.output
    if args.json_path:
        packet = loadJSON(args.json_path)
    else:
        if (args.folders == '' or args.parts ==''):
            parser.print_help()
            raise Exception("Folder paths and parts list is required if no JSON was provided")
        parts = my_file.readFile(args.parts)
        parts = [Part(s) for s in parts if s != ERROR_PART]
        folders = my_file.readFile(args.folders)
        filepaths = findPartFiles(folders, parts)
        packet = Packet(parts, filepaths)
        packet.saveGroupJSON(output_folder + "\\groups.json")
    
    if args.combine: 
        reader.saveDocument(packet.buildDocument(), output_folder + "\\all_parts.pdf", prefix = '')
    if args.move: packet.moveFiles(output_folder)
    packet.saveGroupPartDocs(output_folder)