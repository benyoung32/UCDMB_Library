from turtle import right
import fitz
import argparse
import sys
import os
import glob

prefix = 'fp_'

CW = 0.85 # cropped width

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
                # print("folder found")
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
        else:
            print('invalid path')
    return folders

def test(filename = 'pdfs', **kwargs) -> None:
    files = getSubFiles(filename)
    print('found:')
    print(files)
    processDocs(files, **kwargs)

# open, convert, close and save list of filenames
# returns list of new filenames
def processDocs(filenames, prefix = prefix, **kwargs) -> list:
    print(kwargs)
    if not type(filenames) == list:
        filenames = [filenames]
    new_files = []
    docs = openDocuments(filenames)
    for file,doc in docs.items():
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
                      margins = [0, 0, 0, 0], rotate = 0, right_align = False, **kwargs) -> fitz.Document:
    doc = fitz.open()  # create new empty doc
    top_mg, left_mg, right_mg, bottom_mg = margins
    # if right_align:
    #     src = rightAlign(src)
    for page in src:  # process each page
        page.set_rotation(0)  # ensure page is rotated correctly
        new_page = doc.new_page()  # create new empty output page
        r = page.mediabox
        if full_size: # only use one
            croprect = fitz.Rect(left_mg, top_mg, r.x1-right_mg, r.y1-bottom_mg)
        elif rotate == 0: 
            croprect = fitz.Rect(left_mg, top_mg, r.x1 - right_mg, r.y1 / 2 - bottom_mg)
        else:
            croprect = fitz.Rect(r.x1 / 2 - top_mg, bottom_mg, r.x1 - right_mg, r.y1 - left_mg)
        if two_in_one: # for duplicating ones that are already half size and two pages
            page.set_cropbox(croprect)
            src_pix = page.get_pixmap(dpi = 300)
            insertImage(new_page, src_pix, expand, rotate,right_align)
            if expand: 
                page.set_cropbox(fitz.Rect(left_mg, (r.y1 / 2) - top_mg, r.x1 - right_mg, r.y1-bottom_mg))
                src_pix2 = page.get_pixmap(dpi = 300)
                new_page2 = doc.new_page()
                insertImage(new_page2, src_pix2, expand,rotate,right_align)
        else:
            page.set_cropbox(fitz.Rect(croprect))
            src_pix = page.get_pixmap(dpi = 300)
            insertImage(new_page, src_pix, expand, rotate,right_align)
    return doc 

def rightAlign(doc: fitz.Document):
    out_doc = fitz.Document()
    for page in doc:
        r = page.mediabox
        croprect = fitz.Rect(0, 0, r.x1 * CW, r.y1)
        page.set_cropbox(croprect)
        page_pixmap = page.get_pixmap(dpi = 300)
        out_page = out_doc.new_page()
        out_page.insert_image(fitz.Rect(r.x1 * (1 - CW), 0, r.x1, r.y1),
                              pixmap=page_pixmap)
    return out_doc

def resizeDocument(src: fitz.Document, format:str = 'a4') -> fitz.Document:
    doc = fitz.open()
    for ipage in src:
        if ipage.rect.width > ipage.rect.height:
            fmt = fitz.paper_rect("a4-l")  # landscape if input suggests
        else:
            fmt = fitz.paper_rect("a4")
        page = doc.new_page(width = fmt.width, height = fmt.height)
        page.show_pdf_page(page.rect, src, ipage.number)
    return doc

def insertImage(page, src_pix, expand = False, 
                rotate = 0, right_align = True, keep_proportion = True) -> None:
    r = page.bound()
    if expand:
        page.set_rotation(90)
        page.insert_image(r, pixmap= src_pix, rotate = 90)
    else:
        if not right_align:
            page.insert_image(fitz.Rect(10, 0, r.x1 * CW, r.y1 / 2 - 20),
                pixmap= src_pix, rotate = rotate, keep_proportion = keep_proportion)
            page.insert_image(fitz.Rect(10, r.y1 / 2, r.x1 * CW, r.y1 - 20), 
                pixmap= src_pix, rotate = rotate, keep_proportion = keep_proportion)
        else:
            page.insert_image(fitz.Rect(r.x1 * (1 - CW), 0, r.x1, r.y1 / 2),
                pixmap= src_pix, rotate = rotate, keep_proportion = True)
            page.insert_image(fitz.Rect(r.x1 * (1 - CW), r.y1 / 2, r.x1, r.y1), 
                pixmap= src_pix, rotate = rotate, keep_proportion = True)

# open given list of filenames into document objects 
def openDocuments(filenames: list[str], right_align:bool = False, size:str = "a4") -> dict[str, fitz.Document]:
    if not type(filenames) == list:
        filenames = [filenames]
    filenames = [file for file in filenames if os.path.exists(file)]    
    out = {}
    for filename in filenames:
        doc = fitz.open(filename)
        if size:
            doc = resizeDocument(doc, size)
        if right_align:
            doc = rightAlign(doc)
        out[filename] = doc
    return out
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
    parser.add_argument('rotate',nargs = '?',
                        help = 'How much to rotate the output ',
                        type=int, default = 0)
    parser.add_argument('-f','-full_size',
                        help='When the input takes up the full page size',
                        dest='full_size', action='store_true')
    parser.add_argument('-t','-two_in_one',
                        help='When the top and bottom of a pdf are two distinct separate parts',
                        dest='two_in_one', action='store_true')
    parser.add_argument('-e','-expand',
                        help='Expand cropped pdf to full page size',
                        dest='expand', action='store_true')
    parser.add_argument('-r','-right_align',
                        help='Align cropped pdfs to right edge of the page',
                        dest='right_align', action='store_true')
    if (len(sys.argv) > 1):
        test(**vars(parser.parse_args()))
        # test(sys.argv[1])
    else:
        test()
    resizeDocument(fitz.open(parser.parse_args().filename))

