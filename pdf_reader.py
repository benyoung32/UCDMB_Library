from fitz import *  
import argparse
import sys
import os
import glob

prefix = 'p_'

def clearAlt() -> None:
    for filename in os.listdir(os.getcwd()):
        if filename.endswith('.pdf') and (prefix in filename):
            os.remove(filename)

def getSubFiles(filenames, files = []) -> list:
    if not type(filenames) == list:
        filenames = [filenames]
    for f in filenames:
        if os.path.exists(f):
            if os.path.isdir(f):
                print("folder found")
                getSubFiles(glob.glob(f + "/*.pdf"), files)
            if '.pdf' in f:
                files.append(f)
    return files

def test(filename = 'pdfs', **kwargs) -> None:
    files = getSubFiles(filename)
    print('found:')
    print(files)
    process_docs(files, **kwargs)

# open, convert, close and save list of filenames
# returns list of new filenames
def process_docs(filenames, prefix = prefix, **kwargs) -> list:
    if not type(filenames) == list:
        filenames = [filenames]
    new_files = []
    for file in filenames:
        doc = fitz.open(file)
        alt = duplicateAndScale(doc, **kwargs)
        new_filename = prefix + os.path.basename(file)
        alt.save(new_filename, deflate = True, 
                deflate_images = True, garbage = 4, clean = True)
        doc.close()
        alt.close()
        new_files.append(new_filename)
    return new_files

# convert a4 size paper to two a5 sized documents
def duplicateAndScale(src, **kwargs) -> fitz.Document:
    doc = fitz.open()  # create new empty doc
    # get kwargs value or set default
    print(kwargs)
    top_mg, left_mg, right_mg, bottom_mg = (kwargs['margins'] if
        'margins' in kwargs.keys() else [30, 0, 0, 430])
    full_size = (kwargs['full_size'] 
        if 'full_size' in kwargs.keys() else True)
    expand = (kwargs['expand'] 
        if 'expand' in kwargs.keys() else False)
    two_in_one = (kwargs['two_in_one'] 
        if 'two_in_one' in kwargs.keys() else False)
    rotate = (kwargs['rotate'] 
        if 'rotate' in kwargs.keys() else 0)
        
    for page in src:  # loop over each page
        page.set_rotation(0)  # ensure page is rotated correctly
        new_page = doc.new_page()  # create new empty page
        r = page.mediabox
        if full_size: # only use one
            croprect = fitz.Rect(left_mg, top_mg, r.x1-right_mg, r.y1-bottom_mg)
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
        else:
            page.set_cropbox(fitz.Rect(croprect))
            src_pix = page.get_pixmap(dpi = 300)
            print(page.get_pixmap(dpi =300).tobytes())
            ins_image(new_page, src_pix, expand, rotate)
    return doc 

def ins_image(page, src_pix, expand = False, rotate = 0) -> None:
    r = page.bound()
    if expand:
        page.set_rotation(90)
        page.insert_image(r, pixmap= src_pix, rotate = 90)
    else:
        page.insert_image(fitz.Rect(10, 0, r.x1 * .85, r.y1 / 2 - 20),
            pixmap= src_pix, rotate = rotate, keep_proportion = True)
        page.insert_image(fitz.Rect(10, r.y1 / 2, r.x1 * 0.85, r.y1 - 20), 
            pixmap= src_pix, rotate = rotate, keep_proportion = True)

# open given list of filenames into document objects 
def openDocuments(filenames: list[str]) -> dict:
    if not type(filenames) == list:
        print('creating list')
        filenames = [filenames]    
    return {filename: fitz.open(filename) for filename in filenames}

# close all documents in list/dict
def closeDocuments(docs: list[fitz.Document]) -> None:
    for doc in docs.values(): doc.close()

if __name__ == "__main__":
    print('going')
    parser = argparse.ArgumentParser(sys.argv[0])
    parser.add_argument('filename', type=str)
    parser.add_argument('margins', nargs=4, help="Top, left, right, and bottom margins", type= int)
    parser.add_argument('full_size', type=str)
    parser.add_argument('two_in_one', type=str)
    parser.add_argument('expand', type=str)
    parser.add_argument('rotate', type=int)
    if (len(sys.argv) > 1):
        # test(sys.argv[1], parser.parse_args())
        test(sys.argv[1])
    else:
        test()
    

