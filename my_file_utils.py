import tkinter as tk

def printDict(dict):
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
    reqs = []
    with open(filepath) as file:
        while line := file.readline():
            line = line.strip()
            line = line.strip("\'\"")
            reqs.append(line.strip())
        file.close()
    return reqs

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

