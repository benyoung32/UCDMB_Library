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

def splitPDFs(filename:str, outnamepath:str, simple:bool = False, pages_override = None, rotate = False):
    # open document
    filenames = reader.getSubFiles(filename)
    docs = reader.openDocuments(filenames,size = 'letter')
    print(filenames)
    fmt = fitz.paper_rect('letter')
    if rotate:
        print('rotating')
        for doc in docs.values():
            for page in doc:
                page.set_rotation(180)
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
    if outnamepath:
        songs = grouper.readFile(outnamepath)
    else:
        songs = []
    template = cv.imread('.\\template.png.', cv.IMREAD_GRAYSCALE)
    method = eval('cv.TM_CCOEFF_NORMED')
    for filepath, doc in docs.items():
        i = 0
        if not pages_override:
            last_pages = []
            for page in doc:
                # print(page.rect)
                page.set_rotation(90)
                crop.savePageImage(page, 'temp2.png')
                img = cv.imread('temp2.png', cv.IMREAD_GRAYSCALE)
                last_pages.append(isLastPage(img, template, method))
                # res = cv.matchTemplate(img, template, eval(method))
                # min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)
                # max_vals.append(max_val)
                # showMaxMatch(res, img)
            # i = i + 1
        else:
            last_pages = pages_override
        print(last_pages)
        j = 1
        new_doc = fitz.open()
        for i in range(len(last_pages)):
            # end of song
            new_page = new_doc.new_page()
            new_page.show_pdf_page(new_page.rect, doc, i)
            if last_pages[i] == True:
                if i < len(songs):
                    song = songs[i] + ' - '
                else:
                    song = str(j) + ' '
                    j = j + 1
                # new_path = os.path.dirname(filepath) + "\\" + song  + os.path.basename(filepath)
                directory = os.path.dirname(filepath)
                base = os.path.basename(filepath).strip('.pdf')
                new_folder = directory + '\\' + base
                try:
                    os.mkdir(new_folder)
                except:
                    pass
                reader.saveDocument(new_doc, new_folder + '\\' + base + '.pdf', song) # save and close old doc
                new_doc = fitz.open() # start new one

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
        print('redo...')
        res = cv.matchTemplate(img[-len(img)//2:-1], template, method)
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)
        # showMaxMatch(res, img[-len(img)//2:-1])
    print(max_val)
    threshold = max_val - FUZZY_THRESHOLD
    loc = np.where(res >= threshold)
    points = list(zip(*loc[::-1]))[0:10]
    print(points)
    if len(points) > 1:
        distances = [dist(p1, p2) for p1, p2 in combinations(points, 2)]
        avg_distance = sum(distances) / len(distances)
    else:
        avg_distance = 0
    print(avg_distance)
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

def getPartFromImage(img):
    pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe' 
    # Read image from which text needs to be extracted
    img = img[0:len(img)//5]
    # Preprocessing the image starts
    # Convert the image to gray scale
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    # Performing OTSU threshold
    ret, thresh1 = cv.threshold(gray, 0, 255, cv.THRESH_OTSU | cv.THRESH_BINARY_INV)
    
    # each word instead of a sentence.
    rect_kernel = cv.getStructuringElement(cv.MORPH_RECT, (18, 18))
    
    # Applying dilation on the threshold image
    dilation = cv.dilate(thresh1, rect_kernel, iterations = 1)
    
    # Finding contours
    contours, hierarchy = cv.findContours(dilation, cv.RETR_EXTERNAL,
                                                    cv.CHAIN_APPROX_NONE)
    im2 = img.copy()
    # A text file is created and flushed
    # file.write("")
    # file.close()
    # Looping through the identified contours
    for cnt in contours:
        x, y, w, h = cv.boundingRect(cnt)
        rect = cv.rectangle(im2, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cropped = im2[y:y + h, x:x + w]
        # file = open(outfile, "a")
        text = pytesseract.image_to_string(cropped)
        # check if instrument
        part = grouper.matchPart(text, quiet = True)
        if part != grouper.ERROR_PART:
            return part
    return grouper.ERROR_PART

if __name__ == "__main__":
    parser = argparse.ArgumentParser(sys.argv[0])
    parser.add_argument('filename',type=str, nargs = '?',
                help = 'The file that will be split',
                default=".\\output\\alto saxophone 1.pdf")
    parser.add_argument('-page_names', type=str, nargs = '?',
                help = 'File containing the names for each page on their own line',
                default=None)
    parser.add_argument('-last_pages', type=reader.strtobool, nargs = '*',
                help = 'Override the page separation with custom list',
                default= None)
    parser.add_argument('-s', dest = 'simple', 
                help = 'Simply split the pdf into 1 page chunks',
                action = 'store_true')
    parser.add_argument('-r', dest = 'rotate', 
                help = 'Rotate the input documents 90 degrees',
                action = 'store_true')
    args = parser.parse_args()
    print(args.filename)
    # print(args.last_pages)
    # grouper.matchPart('eb alto saxophone/horn in eb')
    splitPDFs(args.filename, args.page_names, args.simple, args.last_pages,args.rotate)
