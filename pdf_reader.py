import fitz
import os

def openFolder():
    for filename in os.listdir(os.getcwd()):
        if filename.endswith(".pdf") and (not 'alt' in filename):
            doc = fitz.open(filename)
            alt = duplicateAndScale(doc)
            doc.close()
            alt.save("alt_" + filename, deflate = True, deflate_images = True, garbage = 4, clean = True)

def clearAlt():
    for filename in os.listdir(os.getcwd()):
        if filename.endswith('.pdf') and ('alt' in filename):
            os.remove(filename)
            
def test():
    # clearAlt()
    # openFolder()
    filename = 'example.pdf'
    src = fitz.open(filename)
    # docs = openDocuments(['example.pdf', 'newfile.pdf', 'newfile2.pdf'])
    # print(docs)
    # closeDocuments(docs)
    new_doc = duplicateAndScale(src)
    new_doc.save('newfile2.pdf')
    new_doc.close()
    src.close()

# open, convert, close and save list of filenames
def process_docs(filenames, prefix = "alt_"):
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
def duplicateAndScale(src):
    doc = fitz.open() # create new empty doc
    # loop over each page
    for page in src:
        # ensure page is not rotated
        new_page = doc.new_page() # create new empty page
        r = new_page.bound()
        # crop page in half if necessary
        mg = 10
        # only use one
        #page.set_cropbox(fitz.Rect(0, 0, r.x1, 0))
        #page.set_cropbox(fitz.Rect(mg, mg/2, r.x1-mg, (r.y1 / 2) -mg + (mg / 8)))
        #page.set_cropbox(fitz.Rect(mg, 20, r.x1-mg, -mg + 5))
        page.set_rotation(0)
        src_pix = page.get_pixmap(dpi = 300)
        new_page.insert_image(fitz.Rect(0, 0, r.x1 * .85, r.y1 / 2), pixmap= src_pix)
        new_page.insert_image(fitz.Rect(0, r.y1 / 2, r.x1 * 0.85, r.y1), pixmap= src_pix)
    return doc

def rotateDoc(src):
    for page in src:
       page.set_rotation(90)

# open given list of filenames into document objects 
def openDocuments(filenames):
    return {filename: fitz.open(filename) for filename in filenames}

# close all documents in list/dict
def closeDocuments(docs):
    for doc in docs.values(): doc.close()

if __name__ == "__main__":
    print('going')
    test()


