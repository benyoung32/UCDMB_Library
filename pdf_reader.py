import fitz
import sys
import os
import glob

from numpy import full

prefix = 'p_'

def openFolder():
    for filename in os.listdir(os.getcwd()):
        if filename.endswith(".pdf") and (not prefix in filename):
            doc = fitz.open(filename)
            alt = duplicateAndScale(doc)
            doc.close()
            alt.save("prefix" + filename, deflate = True, deflate_images = True, garbage = 4, clean = True)

def clearAlt():
    for filename in os.listdir(os.getcwd()):
        if filename.endswith('.pdf') and (prefix in filename):
            os.remove(filename)

def getSubFiles(filenames, files = []):
    if not type(filenames) == list:
        filenames = [filenames]
    for f in filenames:
        if os.path.exists(f):
            if os.path.isdir(f):
                getSubFiles(glob.glob(f + "/*.pdf"), files)
            if '.pdf' in f:
                files.append(f)
    return files

def test(filename = 'pdfs/example13.pdf'):
    files = getSubFiles(filename)
    print('found:')
    print(files)
    process_docs(files)

# open, convert, close and save list of filenames
def process_docs(filenames, prefix = prefix):
    if not type(filenames) == list:
        filenames = [filenames]
    new_files = []
    for file in filenames:
        doc = fitz.open(file)
        alt = duplicateAndScale(doc)
        new_filename = prefix + os.path.basename(file)
        alt.save(new_filename, deflate = True, deflate_images = True, garbage = 4, clean = True)
        doc.close()
        alt.close()
        new_files.append(new_filename)
    # return list of new filenames
    return new_files

# convert a4 size paper to two a5 sized documents
def duplicateAndScale(src, two_in_one = False, full_size = True, expand = False, rotate = 270):
    doc = fitz.open() # create new empty doc
    for page in src: # loop over each page
        page.set_rotation(0)   # ensure page is rotated correctly
        new_page = doc.new_page() # create new empty page
        r = page.mediabox
        top_mg = 15
        left_mg = 15
        right_mg = 0
        bottom_mg = 20
        
        if full_size: # only use one
            croprect = fitz.Rect(left_mg, top_mg, r.x1-right_mg, r.y1-top_mg)
        elif rotate == 0: 
            croprect = fitz.Rect(left_mg, top_mg, r.x1 - right_mg, r.y1 / 2 - bottom_mg)
            # croprect = fitz.Rect(20, 40, r.x1 - 300, r.y1 - 275)
        else:
            croprect = fitz.Rect(r.x1 / 2 - top_mg, bottom_mg, r.x1 - right_mg, r.y1 - left_mg)
        
        if two_in_one: # for duplicating ones that are already half size and two pages
            page.set_cropbox(croprect)
            src_pix = page.get_pixmap(dpi = 300)
            ins_image(new_page, src_pix, expand, rotate)
            if expand: 
                page.set_cropbox(fitz.Rect(left_mg, (r.y1 / 2) - top_mg, r.x1 - right_mg, r.y1-bottom_mg))
                src_pix2 = page.get_pixmap(dpi = 300)
                new_page2 = doc.new_page()
                ins_image(new_page2, src_pix2, expand,rotate)
        else: # for duplicating ones that are already half size
            page.set_cropbox(fitz.Rect(croprect))
            src_pix = page.get_pixmap(dpi = 300)
            ins_image(new_page, src_pix, expand, rotate)
    return doc 

def ins_image(page, src_pix, expand = False, rotate = 0):
    r = page.bound()
    if expand:
        page.set_rotation(90)
        page.insert_image(r, pixmap= src_pix, rotate = 90)
    else:
        page.insert_image(fitz.Rect(0, 0, r.x1 * .85, r.y1 / 2 - 20), pixmap= src_pix, rotate = rotate)
        page.insert_image(fitz.Rect(0, r.y1 / 2, r.x1 * 0.85, r.y1 - 20), pixmap= src_pix, rotate = rotate)

def rotateDoc(src: fitz.Document):
    for page in src:
       page.set_rotation(90)

def getImage(src: fitz.Document):
    imgs = []
    for page in src:
        imgs.append(page.get_pixmap(dpi = 300))
    return imgs

# open given list of filenames into document objects 
def openDocuments(filenames):
    return {filename: fitz.open(filename) for filename in filenames}

# close all documents in list/dict
def closeDocuments(docs):
    for doc in docs.values(): doc.close()

if __name__ == "__main__":
    print('going')
    if (len(sys.argv) > 1):
        for filename in sys.argv[1:]:
            test(filename)
    else:
        test()
    

