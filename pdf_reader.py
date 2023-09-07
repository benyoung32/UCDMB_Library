import fitz
import argparse
import sys
import os
import glob

prefix = 'fp_'

def clearAlt() -> None:
    for filename in os.listdir(os.getcwd()):
        if filename.endswith('.pdf') and (prefix in filename):
            os.remove(filename)

def getSubFiles(filenames, files = [], ignore_altered = True, recursive = True) -> list[str]:
    if not type(filenames) == list:
        filenames = [filenames]
    for f in filenames:
        if os.path.exists(f):
            if os.path.isdir(f):
                print("folder found")
                if recursive:
                    getSubFiles(glob.glob(f + "/*"), files, ignore_altered)
                else:
                    getSubFiles(glob.glob(f + '/*.pdf'),files, ignore_altered)
            if '.pdf' in f and (not ignore_altered or prefix not in f):
                files.append(f)
    return files

def getSubFolders(filenames, folders = [], ignore_altered = True) -> list[str]:
    if not type(filenames) == list:
        filenames = [filenames]
    for f in filenames:
        if os.path.exists(f):
            if os.path.isdir(f):
                folders.append(f)
                getSubFolders(glob.glob(f + "/*"), folders, ignore_altered)
    return folders

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
        new_filename = os.path.dirname(file) + "\\" +prefix + os.path.basename(file)
        print(new_filename)
        alt.save(new_filename, deflate = True, 
                deflate_images = True, garbage = 4, clean = True)
        doc.close()
        alt.close()
        new_files.append(new_filename)
    return new_files

# convert a4 size paper to two a5 sized documents
def duplicateAndScale(src, full_size=False, expand=False, two_in_one=False,
                      margins = [0, 0, 0, 0], rotate = 0, **kwargs) -> fitz.Document:
    doc = fitz.open()  # create new empty doc
    resized_doc = fitz.open()
    # get kwargs value or set default
    top_mg, left_mg, right_mg, bottom_mg = margins
    fmt = fitz.paper_rect("a4")
    for page in src:  # process each page
        # resize incoming document to a4 size
        # page = resized_doc.new_page(width = fmt.width, height = fmt.height)
        # page.show_pdf_page(page.rect,src,ipage.number)
        # page.set_rotation(0)  # ensure page is rotated correctly
        new_page = doc.new_page()  # create new empty output page
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
            # print(page.get_pixmap(dpi =300).tobytes())
            ins_image(new_page, src_pix, expand, rotate)
    return doc 

def ins_image(page, src_pix, expand = False, rotate = 0) -> None:
    r = page.bound()
    if expand:
        page.set_rotation(90)
        page.insert_image(r, pixmap= src_pix, rotate = 90)
    else:
        # page.insert_image(fitz.Rect(10, 0, r.x1 * .85, r.y1 / 2 - 20),
        #     pixmap= src_pix, rotate = rotate, keep_proportion = True)
        # page.insert_image(fitz.Rect(10, r.y1 / 2, r.x1 * 0.85, r.y1 - 20), 
        #     pixmap= src_pix, rotate = rotate, keep_proportion = True)
        page.insert_image(fitz.Rect(r.x1 * .15, 0, r.x1, r.y1 / 2),
            pixmap= src_pix, rotate = rotate, keep_proportion = True)
        page.insert_image(fitz.Rect(r.x1 * .15, r.y1 / 2, r.x1, r.y1), 
            pixmap= src_pix, rotate = rotate, keep_proportion = True)

# open given list of filenames into document objects 
def openDocuments(filenames: list[str]) -> dict[str, fitz.Document]:
    if not type(filenames) == list:
        print('creating list')
        filenames = [filenames]    
    return {filename: fitz.open(filename) for filename in filenames}

# close all documents in list/dict
def closeDocuments(docs: list[fitz.Document]) -> None:
    for doc in docs.values(): doc.close()

# given list of documents, return one large document
def combineDocuments(docs: list[fitz.Document]) -> fitz.Document:
    out_doc = fitz.Document()
    for doc in docs:
        out_doc.insert_pdf(doc)
    return out_doc

def strtobool (val):
    """Convert a string representation of truth to true (1) or false (0).
    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return 1
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return 0
    else:
        raise ValueError("invalid truth value %r" % (val,))

if __name__ == "__main__":
    # print('going')
    parser = argparse.ArgumentParser(sys.argv[0])
    parser.add_argument('filename', type=str)
    parser.add_argument('margins', nargs=4, help="Top, left, right, and bottom margins", type= int)
    parser.add_argument('full_size', type=strtobool)
    parser.add_argument('two_in_one', type=strtobool)
    parser.add_argument('expand', type=strtobool)
    parser.add_argument('rotate', type=int)
    if (len(sys.argv) > 1):
        test(**vars(parser.parse_args()))
        # test(sys.argv[1])
    else:
        test()
    

