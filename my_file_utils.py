import tkinter as tk
import os
import glob

def printDict(dict):
    '''
    For each key in input dict, print each corresponding value 
    on its own line
    :param dict: Dict to print 
    :return: None
    '''
    for k,v in dict.items():
        print(k, end = ':\n')
        if isinstance(v, list):
            for n in v:
                print(n)
        else:
            print(v)

def save_list(l:list, outfilepath:str) -> None:
    page_file = open(outfilepath, 'w+')
    for b in l:
        page_file.write(str(b) + '\n')
    page_file.close()

def readFile(filepath:str) -> list[str]:
    '''
    Open and read input filepath line by line into a list
    :param filepath: file to read
    :return: A list containing each line of the file at filepath
    '''
    lines = []
    print(filepath)
    with open(filepath) as file:
        while line := file.readline():
            line = line.strip()
            line = line.strip("\'\"")
            lines.append(line.strip())
        file.close()
    return lines

def openFolder() -> str: 
    '''
    Open a system file dialog prompting user to select a folder
    :return: Filepath to selected folder
    '''
    # get file info
    answer = tk.filedialog.askdirectory( # type: ignore
            initialdir=os.getcwd(),
            title="Please select a folder:")
    # return filepath
    return answer


def getSubFiles(paths: list[str], files:list[str] = [], 
                ignore_prefix:str = 'p_', recursive:bool = True) -> list[str]:
    '''
    For each path in paths, append pdf path to files list. 
    If path is a folder, also apend all paths within folder.
    If recursive is true, check folders within folders
    Ignore any paths that contain ignore_prefix
    :param paths: Paths to search
    :param files: Currently found files (for recursion)
    :param ignore_prefix: Ignore any files containing this substring
    :param recursive: If true, recurse into subfolders as well 
    :return: List of pdf files found
    '''
    if not isinstance(paths, list):
        print(f"getSubFiles input must be a list, not {paths}")
        return []
    for f in paths:
        if os.path.exists(f):
            if os.path.isdir(f):
                if recursive:
                    getSubFiles(glob.glob(f + "/*"), files, ignore_prefix)
                else:
                    getSubFiles(glob.glob(f + '/*.pdf'),files, ignore_prefix)
            if '.pdf' in f and (not ignore_prefix or ignore_prefix not in f):
                files.append(f)
        else:
            print(f'{f} - file not found')
    return files

def getSubFolders(folderpaths: list[str], folders = None) -> list[str]:
    '''
    Search through each path in folderpaths for subfolders.
    Append subfolders to folders list, and recursively search subfolders
    See also, getSubFiles
    :param folderpaths: list of folders to search through
    :param folders: list of folders found already (for recursion)
    :return: List of found folder paths
    '''
    if not isinstance(folderpaths, list):
        print(f"getSubFolders input must be a list, not {folderpaths}")
        return []
    if not folders:
        folders = []
    for f in folderpaths:
        if os.path.exists(f):
            if os.path.isdir(f):
                folders.append(f)
                getSubFolders(glob.glob(f + "/*"), folders)
        else:
            print(f'{f} - file not found')
    return folders