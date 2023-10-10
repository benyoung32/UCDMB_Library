import argparse
from cProfile import label
import sys
import os
from turtle import width
import pdf_reader as reader
import crop_tool as crop
import pdf_grouper as grouper
import fitz
import tkinter as tk
from matplotlib import pyplot as plt
import numpy as np
import cv2 as cv
import math
from itertools import combinations
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
    template = cv.imread('.\\template.png.', cv.IMREAD_GRAYSCALE)
    method = eval('cv.TM_CCOEFF_NORMED')
    for filepath, doc in docs.items():
        i = 1
        if from_part: part_file = open('parts' + str(i) + '.txt', 'w+')
        last_pages = [None] * doc.page_count
        if pages_override:
            for index,b in enumerate(pages_override):
                if index >= len(last_pages):
                    break
                last_pages[index] = b
        for index, page in enumerate(doc):
            if last_pages[index] == None:    
                crop.savePageImage(page, 'temp2.png')
                img = cv.imread('temp2.png', cv.IMREAD_GRAYSCALE)
                last_pages[index] = isLastPage(img, template, method)
                if from_part: part_file.write(getPartFromImage(img) + '\n')
                # print(last_pages)
                print('page ', str(index), '...')   
        if from_part: part_file.close()
        # save last_pages to file
        page_file = open(os.path.basename(filepath).strip('.pdf') + '.txt', 'w+')
        for b in last_pages:
            page_file.write(str(b) + '\n')
        page_file.close()
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
              page_titles:list[str],separate_folders:bool = False) -> None:
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
            reader.saveDocument(new_doc, new_folder + '\\' + base + ' - ' + extra + '.pdf', '') # save and close old doc
            new_doc = fitz.open()
            # print(last_pages[k], ', ' + str(k))
            song_counter = song_counter + 1

def dist(p1, p2) -> float:
    (x1, y1), (x2, y2) = p1, p2
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def isLastPage(img ,template, method = cv.TM_CCOEFF_NORMED):
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
    def __init__(self, parent, doc:fitz.Document, output_names:list[str]) -> None:
        # set up window
        tk.Toplevel.__init__(self, parent)
        self.title('Split PDF')
        self.doc = doc
        br = doc[0].bound().br
        self.geometry('{0}x{1}'.format(int(br.x)*2+50, int(br.y)+200))
        
        # set up internal arrays
        self.last_pages = [True] * doc.page_count
        print(output_names)
        if output_names:
            self.output_names = output_names
        else:
            self.output_names = [''] * doc.page_count
        print(self.output_names)
        # holds all subframes
        self.main_frame = tk.Frame(self, bg='yellow')
        # init buttons
        # holds buttons on the bottom
        button_frame = tk.Frame(self.main_frame, bg='blue',height=100,width = int(br.x)*1.5)
        self.separate_var = tk.BooleanVar(button_frame)
        done_button = tk.Button(button_frame, text='Split PDF', command=self.done,font=crop.MYFONT)
        separate_button = crop.CheckButtonWithLabel(button_frame,'Put into seperate folders?',self.separate_var)
        separate_button.label.configure(font=crop.MYFONT)
        self.output_entry = crop.EntryWithLabel(button_frame, 'Output File Name')
        self.output_entry.label.configure(font=crop.MYFONT)
        self.output_entry.entry.configure(font=crop.MYFONT)
        done_button.grid(row=0,column=0,padx=40)
        separate_button.grid(row=0,column=1,columnspan=2,padx=40)
        self.output_entry.grid(row=0,column=3,columnspan=2,padx=40)
        # init page canvases, which display the pdf pages 
        # holds page canvases in the center
        canvas_frame= tk.Frame(self.main_frame,bg='orange')
        self.page_label1 = tk.StringVar(self)
        self.page_label2 = tk.StringVar(self)
        self.page_canvas1 = crop.PDFCanvas(canvas_frame, doc, self.page_label1)
        # page_canvas2 displays 1 page after page_canvas1, such that there are two adjacent pages displayed at once
        self.page_canvas2 = crop.PDFCanvas(canvas_frame, doc, self.page_label2)
        self.pagenum = 0
        # self.after(1,self.setupCanvases) # only load images after opening
        # set up element grids
        self.page_canvas1.grid(row=0,column=0)
        self.page_canvas2.grid(row=0,column=1,)
        canvas_frame.grid(row=0,column=0,padx=0,pady=20)
        button_frame.grid(row=1,column=0,padx=10,pady=10,sticky='nwes')

        self.bind("<Destroy>", self.kill_root)
        self.main_frame.bind('<Button-1>', lambda e : self.focus_set())
        self.bind('<KeyPress>', self.key_input)
        self.main_frame.pack(fill='y',expand=True)
        self.mainloop()
    
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
            self.pagenum = self.pagenum - 1
        elif key == 'd':
            if self.pagenum == self.doc.page_count - 1:
                self.page_canvas2.clear()
                return
            self.pagenum = self.pagenum + 1
        elif key == 's':
            self.last_pages[self.pagenum] = not self.last_pages[self.pagenum]
            if self.pagenum != self.doc.page_count - 1:
                self.pagenum = self.pagenum + 1

        # print(self.pagenum)
        self.set_page_num(self.pagenum)

    def done():
        pass

    def set_page_num(self, num:int) -> None:
        pc1,pc2 = self.page_canvas1, self.page_canvas2
        self.page_label1.set(str(num + 1))
        self.page_label2.set(str(num + 2))
        if self.last_pages[num] == False:
            self.output_entry.entry.config(state='disabled')
        else:
            self.output_entry.entry.config(state='normal')
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
    if args.gui:
        root = tk.Tk()
        root.withdraw()
        SplitGUI(root,fitz.open(args.filename),output_names)
    else:
        splitPDFs(**vars(args))
