import argparse
import sys
import os
import pdf_reader as reader
import crop_tool as crop
import pdf_grouper as grouper
import fitz
# import tkinter as tk
from matplotlib import pyplot as plt
import numpy as np
import cv2 as cv
import math
from itertools import combinations
import pytesseract

MAX_AVERAGE_DISTANCE = 100
FUZZY_THRESHOLD = 0.02
# MIN_FOUND_VAL = 0.47
# root = tk.Tk()
# root.title("Split pdf")
# root.withdraw()
# root.geometry("1000x1000")
# main_frame = tk.Frame(master=root, background = 'grey')
# pdf_canvas = tk.Canvas(main_frame, background = 'light blue',width = 400, height = 400)
# pdf_canvas.grid(row = 0, column = 0, sticky = 'nwes')
# button_frame = tk.Frame(main_frame,  background = 'yellow', width = 400, height = 100)
# button_frame.grid(row = 1, column= 0, sticky = 'nwes')
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
              pages_override = None, rotate = None,from_part:bool = False,
              no_save:bool = False, **kwargs):
    # open document
    filenames = reader.getSubFiles(filename)
    docs = reader.openDocuments(filenames)
    # reader.saveDocument(list(docs.values())[0],'./test.pdf','')
    print(filenames)
    fmt = fitz.paper_rect('letter')
    if rotate:
        print('rotating')
        for doc in docs.values():
            for page in doc:
                page.set_rotation(rotate)
    if simple:
        for filepath, doc in docs.items():
            i = 1
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
                new_doc.save(directory + '\\' + base + '\\' + base + str(i) + '.pdf',
                            deflate = True, 
                            deflate_images = True, garbage = 4, clean = True)
                new_doc.close()
                i = i + 1
        return
    template = cv.imread('.\\template.png.', cv.IMREAD_GRAYSCALE)
    method = eval('cv.TM_CCOEFF_NORMED')
    for filepath, doc in docs.items():
        i = 1
        if from_part: part_file = open('parts.txt', 'w+')
        if not pages_override:
            last_pages = []
            for page in doc:
                crop.savePageImage(page, 'temp2.png')
                img = cv.imread('temp2.png', cv.IMREAD_GRAYSCALE)
                last_pages.append(isLastPage(img, template, method))
                if from_part: part_file.write(getPartFromImage(img) + '\n')
                # res = cv.matchTemplate(img, template, eval(method))
                # min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)
                # max_vals.append(max_val)
                # showMaxMatch(res, img)
                print('page ', str(i), '...')   
                i = i + 1
        else:
            last_pages = pages_override
        if from_part: part_file.close()
        # save last_pages to file
        page_file = open('pages.txt', 'w+')
        for b in last_pages:
            page_file.write(str(b) + '\n')
        page_file.close()
        j = 1
        if from_part:
            songs = grouper.readFile('parts.txt')
        elif output_names_filepath:
            songs = grouper.readFile(output_names_filepath)
        else:
            songs = []
        new_doc = fitz.Document(rect=fmt)
        if no_save:
            return # return only if saving is not needed
        for i in range(len(last_pages)):
            # end of song
            new_doc.insert_pdf(doc,from_page=i, to_page=i)
            if last_pages[i] == True:
                extra = str(j) + ' '
                j = j + 1
                if i < len(songs):
                    extra = songs[i]
                # new_path = os.path.dirname(filepath) + "\\" + song  + os.path.basename(filepath)
                directory = os.path.dirname(filepath)
                base = os.path.basename(filepath).strip('.pdf')
                new_folder = directory + '\\' + base
                try:
                    os.mkdir(new_folder)
                except:
                    pass
                # reader.saveDocument(new_doc, new_folder + '\\' + base + '.pdf', song) # save and close old doc
                reader.saveDocument(new_doc, new_folder + '\\' + base + ' - ' + extra + '.pdf', '') # save and close old doc
                new_doc = fitz.open() # start new document

def dist(p1, p2):
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(sys.argv[0])
    parser.add_argument('filename',type=str, nargs = '?',
                help = 'The file that will be split')
    parser.add_argument('-p','-page_names', dest = 'page_names',type=str, nargs = '?',
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
    args = parser.parse_args()
    print(args.filename)
    if args.last_page_file:
        last_pages = grouper.readFile(args.last_page_file)
        last_pages = [reader.strtobool(s) for s in last_pages]
    else:
        last_pages = None
    # print(args.last_pages)
    # print(grouper.matchPart('eb alto saxophone/horn in eb ',pretty = True))
    # print(vars(args))
    splitPDFs(**vars(args))
