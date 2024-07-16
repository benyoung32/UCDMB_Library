import pdf_grouper as grouper  
import my_file_utils as utils 
import part as part
import fitz
import fitz.fitz
import argparse
import sys
import os
import glob

prefix = 'p_'
FORMAT = fitz.paper_rect('letter')

CW = 0.85 # cropped width

def main(filename:str = 'pdfs', **kwargs) -> None:
    '''
    Main function. Opens filenames, passes kwargs to processing functoins
    '''
    files = getSubFiles([filename])
    print('found:', files)
    openCropSaveDocs(files, **kwargs)

def openCropSaveDocs(filepaths: list[str], 
                auto_expand:bool = True, **kwargs) -> list:
    '''
    Primarily wrapper for :func:`pdf_reader.duplicateAndScale`
    See that function for more info about kwargs.
    For each file in filenames, open as document, apply crop using
    :func:`pdf_reader.createCroppedDocument` and args in kwargs. 
    Save altered file with 'prefix' inside new folder. 
    :param filenames: List of paths to pdfs that will be processed
    :param auto_expand: If true, check if processed doc is in grouper.DRUMS
                        and should be expanded.
    :param kwargs: Kwargs to be passed along to :func:`pdf_reader.createCroppedDocument`
    :return: Returns list of paths for the newly created pdf files
    '''
    new_files = []
    docs = openDocuments(filepaths, size='letter')
    new_folder = os.path.dirname(filepaths[0]) + '\\Printable Parts'
    try:
        os.mkdir(new_folder)
    except:
        print('new folder already exists')
    for file, doc in zip(filepaths, docs):
        Part = part.getPartFromFilepath(file)
        print(file)
        if auto_expand:
            print(Part)
            if Part in grouper.DRUMS:
                print('expanding', Part)    
                kwargs['expand'] = True
            else: kwargs['expand'] = False
        cropped_doc = createCroppedDocument(doc, **kwargs)
        new_filename = new_folder + '\\' + os.path.basename(file)
        saveDocument(cropped_doc, new_filename, prefix = prefix)
        doc.close()
        new_files.append(new_filename)
    return new_files

def splitTopBottom(doc: fitz.Document) -> fitz.Document:
    out = fitz.Document(rect=FORMAT)
    for page in doc:
        r = page.bound()
        doc.new_page(width = FORMAT.width, height = FORMAT.height) # type: ignore
    return out

def createCroppedDocument(src:fitz.Document, full_size:bool=False, 
                      expand:bool=False, two_in_one:bool=False,
                      margins:list[int] = [0, 0, 0, 0], rotate = 0, **kwargs) -> fitz.Document:
    '''
    From source document 'src', crop the page according to 'margins' 
    and insert cropped page as image into output document. 
    Functions significantly differently if 'expand' is True:
    If expand, crop document then insert image into full pdf, landscape
    Else, insert cropped page twice on top and bottom into output pdf
    :param src: Source document to alter
    :param full_size: Is the input full size, 
                      or should the cropping begin from half of the page
    :param;
    '''
    doc = fitz.Document(rect=FORMAT)  # create new empty doc
    top_mg, left_mg, right_mg, bottom_mg = margins     # unpack margin array
    for page in src:
        page.set_rotation(0)  # make sure page has no rotation
        r = page.mediabox
        new_page = doc.new_page(width = FORMAT.width, height = FORMAT.height) # type: ignore
        if full_size: croprect = fitz.Rect(left_mg, top_mg, r.x1-right_mg, r.y1-bottom_mg)
        else: croprect = fitz.Rect(r.x1 / 2 - top_mg, bottom_mg, r.x1 - right_mg, r.y1 - left_mg)
        page.set_cropbox(fitz.Rect(croprect))
        src_pix = page.get_pixmap(dpi = 300,colorspace='GRAY')  # type: ignore
        if expand:
            insertFullPageImage(new_page, src_pix)
        else:
            insertImage(new_page, src_pix, rotate=rotate)
    return doc 

def insertFullPageImage(page, src_pix) -> None:
    r = page.bound()
    page.set_rotation(90)
    page.insert_image(r, pixmap= src_pix, rotate = 90)

def insertImage(page, src_pix, **kwargs) -> None:
    r = page.bound()
    page.insert_image(fitz.Rect(0, 5, r.x1 * CW, r.y1 / 2 - 5),
        pixmap= src_pix, **kwargs)
    page.insert_image(fitz.Rect(0, r.y1 / 2 + 5, r.x1 * CW, r.y1 - 5), 
        pixmap= src_pix, **kwargs)    

def rightAlign(doc: fitz.Document) -> fitz.Document:
    out_doc = fitz.Document(rect=FORMAT)
    for page in doc:
        r = page.mediabox
        croprect = fitz.Rect(0, 0, r.x1 * CW, r.y1)
        page.set_cropbox(croprect)
        page_pixmap = page.get_pixmap(dpi = 300) # type: ignore
        out_page = out_doc.new_page(width=FORMAT.width, height=FORMAT.height)  # type: ignore
        out_page.insert_image(fitz.Rect(r.x1 * (1 - CW), 0, r.x1, r.y1),
                              pixmap=page_pixmap)
    return out_doc

def leftAlign(doc:fitz.Document) -> fitz.Document:
    out_doc = fitz.Document(rect=FORMAT)
    for page in doc:
        r = page.mediabox
        croprect = fitz.Rect(r.x1 * (1 - CW), 0, r.x1, r.y1)
        page.set_cropbox(croprect)
        page_pixmap = page.get_pixmap(dpi = 300)
        out_page = out_doc.new_page(width=FORMAT.width, height=FORMAT.height)
        out_page.insert_image(fitz.Rect(0, 0, r.x1 * CW, r.y1),
                              pixmap=page_pixmap)
    return out_doc

def resizeDocument(src: fitz.Document, format:str = 'letter') -> fitz.Document:
    doc = fitz.Document(rect=FORMAT)
    for ipage in src:
        if ipage.rect.width > ipage.rect.height:
            fmt = fitz.paper_rect(format)  # landscape if input suggests
            # print(fmt)
            # temp = fmt.width
            fmt = fitz.Rect(0,0,fmt.height, fmt.width)
            # print(fmt)
            # fmt.height = temp
        else:
            fmt = fitz.paper_rect(format)
        page = doc.new_page(width = fmt.width, height = fmt.height)
        page.show_pdf_page(page.rect, src, ipage.number)
    return doc

def openDocuments(filenames: list[str], right_align:bool = False, size:str = None) -> list[fitz.Document]:
    if not type(filenames) == list:
        filenames = [filenames]
    filenames = [file for file in filenames if os.path.exists(file)]    
    out = []
    for filename in filenames:
        try:
            doc = fitz.open(filename)
        except:
            print("unable to open file: ", filename)
            print(fitz.TOOLS.mupdf_warnings())
            sys.exit(":(")
            doc = None
        # if size:
        #     doc = resizeDocument(doc, size)
        # if right_align:
        #     doc = rightAlign(doc)
        out.append(doc)
    return out

def saveDocument(doc: fitz.Document, filename:str, prefix = prefix, close = True) -> None: 
    new_filename = os.path.dirname(filename) + "\\" + prefix + os.path.basename(filename)
    doc.save(new_filename, deflate = True, 
            deflate_images = True, garbage = 4, clean = True)
    if close:
        doc.close()

def combineDocuments(docs: list[fitz.Document]) -> fitz.Document:
    out_doc = fitz.Document()
    for doc in docs:
        out_doc.insert_pdf(doc)
    return out_doc

def addPageNumbers(doc: fitz.Document, split = False, start = 0) -> None:
    i = 0
    page_size = doc[0].bound()
    top_rect = fitz.Rect(page_size.x1 - 40, 15, page_size.x1 - 20, 50)
    bot_rect = fitz.Rect(page_size.x1 - 40, 15 + page_size.y1 / 2, 
                         page_size.x1 - 20, 50 + page_size.y1 / 2)
    font = "TiRo"
    for page in doc:
        i += 1
        if (i <= start): continue
        pg = i - start
        page.insert_textbox(top_rect, str(pg), fontname= font) # type: ignore
        if split:
            page.add_freetext_annot(bot_rect, str(pg + doc.page_count), fontname= font) # type: ignore
        else:
            page.add_freetext_annot(bot_rect, str(pg), fontname= font) # type: ignore

def strtobool (val) -> bool:
    '''
    Convert a string representation of truth to true (1) or false (0).
    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    '''
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return True
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return False
    else:
        raise ValueError("invalid truth value %r" % (val,))

if __name__ == "__main__":
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
    parser.add_argument('-ro', '-right_align_only',
                        help='Align pdfs to right edge of the page, don\'t do any cropping',
                        dest='right_align_only', action='store_true')
    parser.add_argument('-lo', '-left_align_only',
                        help='Align pdfs to right edge of the page, don\'t do any cropping',
                        dest='left_align_only', action='store_true')
    args = parser.parse_args()
    files = utils.getSubFiles([args.filename], ignore_prefix=None)
    print(files)
    docs = openDocuments(files)
    if args.right_align_only:
        for path, doc in zip(files, docs):
            print(f"right align {path}")
            saveDocument(rightAlign(doc), path, prefix = 'fp_')
    elif args.left_align_only:
        for path, doc in zip(files, docs):
            saveDocument(leftAlign(doc), path)
    elif (len(sys.argv) > 1):
        main(**vars(args))
    else:
        main()
    
    # resizeDocument(fitz.open(parser.parse_args().filename))

