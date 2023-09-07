import pdf_reader as reader
import tkinter as tk
import tkinter.filedialog
import operator as op
import json
import os

ALIAS_FILE = "alias.json"
f = open(ALIAS_FILE)
alias = json.load(f)
folder = ""
files = None

def openFolder() -> str: 
    # get file info
    answer = tk.filedialog.askdirectory(
            initialdir=os.getcwd(),
            title="Please select a folder:")
    # return filepath
    return answer

def init(dir: str) -> None:
    global folder, files
    folder = dir
    files = reader.getSubFiles(folder, [], ignore_altered=False)
    # print(files)
    removed_chars = ['\\','/',':','.','_','p_','-']
    for i in range(len(files)):
        for rm in removed_chars:
           files[i] = files[i].replace(rm, ' ')
        # print(files[i])
    print(common_words_filter(files))
    # print(files)

def common_words_filter(strings):
    my_word_count = {}
    part_numbers = ['1','2','3','4','5','1st','2nd','3rd','4th','5th']
    for string in strings:
        for i, word in enumerate(string.split()):
            if word in part_numbers:
                
            else:
                my_word_count[word] = my_word_count.get(word, 0) + 1
    return [word for word in my_word_count if my_word_count[word] < len(strings)]



if __name__ == "__main__":
    # init(openFolder())
    init("C:\\Users\\benyo\\Downloads\\folder\\ADJ_Everybody Talks - Ty Pon")

