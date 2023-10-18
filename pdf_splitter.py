import argparse
import shutil
import sys
import os
import pdf_reader as reader
import crop_tool as crop
import pdf_grouper as grouper
import fitz
import tkinter as tk
import cv2 as cv
import math
from itertools import combinations

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # print('running in a PyInstaller bundle')
    frozen = True
else:
    # print('running in a normal Python process')
    frozen = False
    from matplotlib import pyplot as plt
    import numpy as np
    import pytesseract
MAX_AVERAGE_DISTANCE = 100
FUZZY_THRESHOLD = 0.02
# MIN_FOUND_VAL = 0.47

def printDict(dict):
    for k,v in dict.items():
        print(k, end = ':\n')
        if v is list:
            for n in v:
                print(n)
        else:
            print(v)

def main(filename:str):
    pass

def save_list(l:list, outfilepath:str) -> None:
    page_file = open(outfilepath, 'w+')
    for b in l:
        page_file.write(str(b) + '\n')
    page_file.close()

def splitPDFs(filename:str, output_names_filepath:str = None, simple:bool = False, 
              pages_override: list[bool] = None, rotate = None,from_part:bool = False,
              no_save:bool = False, **kwargs):
    filenames = reader.getSubFiles(filename)
    docs = reader.openDocuments(filenames)
    fmt = fitz.paper_rect('letter')
    if rotate:
        print('rotating')
        for doc in docs.values():
            for page in doc:
                page.set_rotation(rotate)
    if simple:
        for filepath, doc in docs.items():
            k = 1
            directory = os.path.dirname(filepath)
            base = os.path.basename(filepath).strip('.pdf')
            # new_folder = directory + '\\' 
            try:
                os.mkdir(directory + '\\' + base)
            except:
                pass
            for src_page in doc:
                new_doc = fitz.Document(rect=fmt)
                new_doc.insert_pdf(doc, from_page=src_page.number,to_page=src_page.number)
                # page = new_doc.new_page()
                # print(filepath)
                new_doc.save(directory + '\\' + base + '\\' + base + str(k) + '.pdf',
                            deflate = True, 
                            deflate_images = True, garbage = 4, clean = True)
                new_doc.close()
                k = k + 1
        return
    for filepath, doc in docs.items():
        i = 1
        if from_part: part_file = open('parts' + str(i) + '.txt', 'w+')
        last_pages = [None] * doc.page_count
        if pages_override:
            for index,b in enumerate(pages_override):
                if index >= len(last_pages):
                    break
                last_pages[index] = b
        if not frozen:
            template = cv.imread('.\\template.png.', cv.IMREAD_GRAYSCALE)
            method = eval('cv.TM_CCOEFF_NORMED')
            for index, page in enumerate(doc):
                if last_pages[index] == None:    
                    crop.savePageImage(page, 'temp2.png')
                    img = cv.imread('temp2.png', cv.IMREAD_GRAYSCALE)
                    last_pages[index] = isLastPage(img, template, method)
                    if from_part: part_file.write(getPartFromImage(img) + '\n')
                    print('page ', str(index), '...')   
        if from_part: part_file.close()
        save_list(last_pages, os.path.basename(filepath).strip('.pdf') + '.txt')
        if from_part:
            songs = grouper.readFile('parts.txt')
        elif output_names_filepath:
            songs = grouper.readFile(output_names_filepath)
        else:
            songs = []
        i = i + 1
        if no_save:
            continue # return only if saving is not needed
        split_pdf(filepath,last_pages,songs)

def split_pdf(filepath:str,last_pages:list[bool], 
              page_titles:list[str],separate_folders:bool = False, add:bool = True) -> None:
    doc = fitz.open(filepath)
    fmt = fitz.paper_rect('letter')
    new_doc = fitz.Document(rect=fmt)
    # print(page_titles)
    directory = os.path.dirname(filepath)
    base = os.path.basename(filepath).strip('.pdf')
    if not separate_folders:
        new_folder = directory + '\\' + base
        try:
            os.mkdir(new_folder)
        except:
            pass
    song_counter = 0 # counter for where you are in page_titles array
    for k in range(len(last_pages)):
        new_doc.insert_pdf(doc,from_page=k, to_page=k)
        if last_pages[k] == True:
            if song_counter < len(page_titles):
                extra = page_titles[song_counter]
            else:
                extra = str(song_counter) + ' '
            # new_doc[0].add_freetext_annot(new_doc[0].bound() - (-30,-30,100,100),str(k+1),text_color=(0,0,1),fontsize=22)
            if separate_folders:
                new_folder = directory + '\\' + extra
                try:
                    os.mkdir(new_folder)
                except:
                    pass
                reader.saveDocument(new_doc, new_folder + '\\' + extra + ' - ' + base + '.pdf', '')
            else: 
                if add:
                    reader.saveDocument(new_doc, new_folder + '\\' + base + ' - ' + extra + '.pdf', '') # save and close old doc
                else:
                    reader.saveDocument(new_doc, new_folder + '\\' + extra + '.pdf', '')
            new_doc = fitz.open()
            # print(last_pages[k], ', ' + str(k))
            song_counter = song_counter + 1

def dist(p1, p2) -> float:
    (x1, y1), (x2, y2) = p1, p2
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def isLastPage(img ,template, method = cv.TM_CCOEFF_NORMED) -> bool:
    if frozen:
        print('|| ERROR || Running inside bundle, some features unavailable :(')
        return True
    # first check only the bottom of the page 
    bottom_img = img[-len(img)//5:-1]
    res = cv.matchTemplate(bottom_img, template, method)
    min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)
    # if nothing found, search whole page
    if max_val < 0.2:
        # print('redo...')
        res = cv.matchTemplate(img[-len(img)//2:-1], template, method)
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)
        # showMaxMatch(res, img[-len(img)//2:-1])
    # print(max_val)
    threshold = max_val - FUZZY_THRESHOLD
    loc = np.where(res >= threshold)
    points = list(zip(*loc[::-1]))[0:10]
    # print(points)
    if len(points) > 1:
        distances = [dist(p1, p2) for p1, p2 in combinations(points, 2)]
        avg_distance = sum(distances) / len(distances)
    else:
        avg_distance = 0
    # print(avg_distance)
    return avg_distance < MAX_AVERAGE_DISTANCE
    
def showMaxMatch(res, img) -> None:
    if frozen:
        print('|| ERROR || Running inside bundle, some features unavailable :(')
        return
    min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)
    threshold = max_val - 0.02
    loc = np.where(res >= threshold)
    # print(top_left, bottom_right)
    for pt in zip(*loc[::-1]):
        top_left = pt
        bottom_right = (pt[0] + 100, pt[1] + 100)
        cv.rectangle(img,top_left,bottom_right, (0,0,255), 10)
    plt.subplot(121),plt.imshow(res,cmap = 'gray')
    plt.title('Matching Result'), plt.xticks([]), plt.yticks([])
    plt.subplot(122),plt.imshow(img,cmap = 'gray')
    plt.title('Detected Point'), plt.xticks([]), plt.yticks([])
    plt.suptitle('result')
    plt.show()

def getPartFromImage(img) -> str:
    pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe' 
    # Read image from which text needs to be extracted
    img = img[0:len(img)//5]
    # Preprocessing the image starts
    # Convert the image to gray scale
    # gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    # Performing OTSU threshold
    ret, thresh1 = cv.threshold(img, 0, 255, cv.THRESH_OTSU | cv.THRESH_BINARY_INV)
    
    # each word instead of a sentence.
    rect_kernel = cv.getStructuringElement(cv.MORPH_RECT, (18, 18))
    
    # Applying dilation on the threshold image
    dilation = cv.dilate(thresh1, rect_kernel, iterations = 1)
    
    # Finding contours
    contours, hierarchy = cv.findContours(dilation, cv.RETR_EXTERNAL,
                                                    cv.CHAIN_APPROX_NONE)
    im2 = img.copy()
    # Looping through the identified contours
    for cnt in contours:
        x, y, w, h = cv.boundingRect(cnt)
        rect = cv.rectangle(im2, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cropped = im2[y:y + h, x:x + w]
        # file = open(outfile, "a")
        text = pytesseract.image_to_string(cropped)
        # check if instrument
        # print(text)
        part = grouper.matchPart(text, quiet = True, pretty = True)
        if part != grouper.ERROR_PART:
            return part
    return grouper.ERROR_PART

class SplitGUI(tk.Toplevel):
    def __init__(self, parent, filepath:str, output_names:list[str] = None, last_pages:list[bool] = None) -> None:
        # set up window
        tk.Toplevel.__init__(self, parent)
        self.title('Split PDF')
        doc = fitz.open(filepath)
        self.doc = doc
        self.basename = os.path.basename(filepath).strip('.pdf')
        self.directory = os.path.dirname(filepath)
        self.filepath = filepath
        br = doc[0].bound().br
        self.geometry('{0}x{1}'.format(int(br.x)*2+50, int(br.y)+200))
        
        # set up internal arrays
        if last_pages:
            self.last_pages = [True] * doc.page_count
            for i, b in enumerate(self.last_pages):
                if i >= len(last_pages):
                    break
                self.last_pages[i] = last_pages[i]
        else:
            try:
                self.last_pages = grouper.readFile(self.directory + '//' + self.basename + ' pages.txt')
                self.last_pages = [reader.strtobool(s) for s in self.last_pages]
                print('opened file')
            except:
                self.last_pages = [True] * doc.page_count
                print('no last pages found')
        # print(output_names)
        if output_names:
            self.output_names = output_names
        else:
            try:
                self.output_names = grouper.readFile(self.directory + '//' + self.basename + ' outputnames.txt')
                print('opened file')
            except:
                self.output_names = [self.basename + ' - '] * doc.page_count
                print('no output files found')
        self.output_index = 0

        # holds all subframes
        self.main_frame = tk.Frame(self, bg='yellow')
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(0, weight=1,minsize=100)
        self.main_frame.rowconfigure(1, weight=1)
        # init buttons
        # holds buttons on the bottom
        button_frame = tk.Frame(self.main_frame, bg='blue',height=100,width = int(br.x)*1.5)
        self.separate_var = tk.BooleanVar(button_frame)
        done_button = tk.Button(button_frame, text='Split PDF', command=self.done,font=crop.MYFONT)
        separate_button = crop.CheckButtonWithLabel(button_frame,'Put into seperate folders?',self.separate_var)
        separate_button.label.configure(font=crop.MYFONT)
        if output_names:
            add_button = tk.Button(button_frame, text='Add Song', command=self.add,font=crop.MYFONT)
            add_button.grid(row = 1, column=0, padx=20)
            skip_button = tk.Button(button_frame, text='Skip', command=self.skip,font=crop.MYFONT)
            skip_button.grid(row = 1, column=1, padx=20)
        self.output_entry = crop.EntryWithLabel(button_frame, 'Output File Name')
        self.output_entry.label.configure(font=crop.MYFONT)
        self.output_entry.entry.configure(font=crop.MYFONT,width=30)
        self.output_entry.entry.insert(0,self.output_names[0])
        done_button.grid(row=0,column=0,padx=30)
        separate_button.grid(row=0,column=1,columnspan=2,padx=30)
        self.output_entry.grid(row=0,column=3,columnspan=2,padx=30)
        # init page canvases, which display the pdf pages 
        # holds page canvases in the center
        self.canvas_frame= tk.Frame(self.main_frame,bg='orange')
        self.page_label1 = tk.StringVar(self)
        self.page_label2 = tk.StringVar(self)
        self.page_canvas1 = crop.PDFCanvas(self.canvas_frame, doc, self.page_label1)
        # page_canvas2 displays 1 page after page_canvas1, such that there are two adjacent pages displayed at once
        self.page_canvas2 = crop.PDFCanvas(self.canvas_frame, doc, self.page_label2)
        self.pagenum = 0
        self.after(500,self.setupCanvases) # only load images after opening
        # set up element grids
        self.canvas_frame.columnconfigure(0, weight=1)
        self.canvas_frame.columnconfigure(1, weight=1)
        self.page_canvas1.grid(row=0,column=0)
        self.page_canvas2.grid(row=0,column=1)
        self.canvas_frame.grid(row=1,column=0,padx=0,pady=20)
        button_frame.grid(row=0,column=0,padx=10,pady=10,sticky='nwes')
        # button_frame.pack(fill='both')
        self.bind("<Destroy>", self.kill_root)
        self.main_frame.bind('<Button-1>', lambda e : self.focus_set())
        self.bind('<KeyPress>', self.key_input)
        self.bind('<Configure>', self.resize)
        # self.main_frame.pack(fill='y',expand=True)
        self.main_frame.pack()
        self.mainloop()

    def resize(self, event) -> None:
        pass
        # print(event)
        # self.main_frame.config(width=event.width, height=event.height)
        # self.canvas_frame.configure(width=event.width,height=event.height)
        # self.page_canvas1.configure(width=event.width/2, height=event.height/2)
        # self.main_frame.pack(fill ='y',expand=True)

    def setupCanvases(self) -> None:
        self.page_canvas1.preloadImages()
        self.page_canvas2.page_images = self.page_canvas1.page_images
        self.set_page_num(0)

    def key_input(self, event) -> None:
        if self.focus_get() != self:
            # print('not in focus')
            return
        key = event.keysym
        if key == 'a':
            if self.pagenum == 0:
                return
            newpage = self.pagenum - 1
        elif key == 'd':
            if self.pagenum == self.doc.page_count - 1:
                self.page_canvas2.clear()
                return
            newpage = self.pagenum + 1
        elif key == 's':
            self.last_pages[self.pagenum] = not self.last_pages[self.pagenum]
            if self.pagenum != self.doc.page_count - 1:
                newpage = self.pagenum + 1

        # print(self.pagenum)
        self.set_page_num(newpage)

    def done(self) -> None:
        save_list(self.last_pages,self.directory + '//' + self.basename + ' pages.txt')
        save_list(self.output_names,self.directory + '//' + self.basename + ' output.txt')
        split_pdf(self.filepath,self.last_pages,self.output_names,self.separate_var.get(),False)

    def add(self) -> None:
        self.output_names.insert(self.getOutputIndexAtPage(self.pagenum),self.output_entry.get())
    
    def skip(self) -> None:
        print(self.output_names.pop(self.getOutputIndexAtPage(self.pagenum)))

    def set_page_num(self, num:int) -> None:
        pc1,pc2,entry = self.page_canvas1, self.page_canvas2,self.output_entry.entry
        self.page_label1.set(str(num + 1))
        self.page_label2.set(str(num + 2))
        new_index = self.getOutputIndexAtPage(num)
        if new_index == self.output_index:
            # print('same')
            pass
        else:
            self.output_names[self.output_index] = entry.get() # save inputted value
            self.output_index = new_index
        if self.last_pages[num] == False:
            entry.config(state='disabled',width=30)
        else:
            entry.config(state='normal',width=30)
        entry.delete(0, tk.END)
        entry.insert(0, self.output_names[new_index])
        self.pagenum = num
        if num < 0:
            pc1.clear()
            pc2.clear()
            return
        if num < self.doc.page_count:
            if self.last_pages[num]:
                pc1.configure(bg='green',width=pc1.winfo_width(),height=pc1.winfo_height())
            else:
                pc1.configure(bg='red',width=pc1.winfo_width(),height=pc1.winfo_height())
            self.page_canvas1.updatePage(num)
        if num < self.doc.page_count - 1:
            if self.last_pages[num+1]:
                pc2.configure(bg='green',width=pc2.winfo_width(),height=pc2.winfo_height())
            else:
                pc2.configure(bg='red',width=pc2.winfo_width(),height=pc2.winfo_height())
            self.page_canvas2.updatePage(num + 1)

    def getOutputIndexAtPage(self,pagenum:int): 
        counter = 0
        for i in range(pagenum):
            if self.last_pages[i]:
                counter = counter + 1
        return counter

    def kill_root(self, event) -> None:
        if event.widget == self and self.master.winfo_exists():
            self.master.destroy()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(sys.argv[0])
    parser.add_argument('filename',type=str,
                help = 'The file that will be split')
    parser.add_argument('-p','-page_names', dest = 'output_names_filepath',type=str, nargs = '?',
                help = 'File containing the names for each page on their own line',
                default=None)
    parser.add_argument('-o', dest = 'last_page_file', type=str, nargs = '?',
                help = 'Override the page separation with custom list in specified file',
                default= None)
    parser.add_argument('-f', dest = 'from_part', action= 'store_true',
                help = '''Get the part name from the pdf using text recognition,
                        and store in an output file''',
                default= None)
    parser.add_argument('-n','-ns','-no_save', dest = 'no_save', action= 'store_true',
            help = '''Use to not save the resulting documents, 
                    only create part and page text files''',
            default= None)
    parser.add_argument('-s', dest = 'simple', 
                help = 'Simply split the pdf into 1 page chunks',
                action = 'store_true')
    parser.add_argument('-r', dest = 'rotate', 
                help = 'Rotate the input documents 90 degrees',
                type = int)
    parser.add_argument('-g', dest = 'gui', 
                help = 'Rotate the input documents 90 degrees',
                action = 'store_true')
    args = parser.parse_args()
    print(args.filename)
    if args.last_page_file:
        last_pages = grouper.readFile(args.last_page_file)
        last_pages = [reader.strtobool(s) for s in last_pages]
    else:
        last_pages = None
    args.pages_override = last_pages
    if args.output_names_filepath:
        output_names = grouper.readFile(args.output_names_filepath)
    else:
        output_names = None
    # files = reader.getSubFiles(args.filename)
    # # files = [grouper.getPartNameFromString(file) for file in files]
    # files = [file for file in files if grouper.getPartNameFromString(file) == 'clarinet 2']
    # # print(files)
    # for f in files:
    #     # d = f
    #     d = f[0:-5] + '1.pdf'
    #     # print(d)
    #     shutil.copy(f,d)
    if args.gui or frozen:
        root = tk.Tk()
        root.withdraw()
        SplitGUI(root,args.filename,output_names,last_pages)
    else:
        splitPDFs(**vars(args))
