import fitz

def test():
    filename = 'example.pdf'
    src = fitz.open(filename)
    docs = openDocuments(['example.pdf', 'newfile.pdf', 'newfile2.pdf'])
    print(docs)
    closeDocuments(docs)
    new_doc = duplicateAndScale(src)
    new_doc.save('newfile.pdf')
    new_doc.close()

# open given list of filenames into document objects 
def openDocuments(filenames):
    return {filename: fitz.open(filename) for filename in filenames}

# close all documents in list/dict
def closeDocuments(docs):
    for doc in docs.values():
        doc.close()

# convert a4 size paper to two a5 sized documents
def duplicateAndScale(src):
    doc = fitz.open() # create new empty doc
    # loop over each page
    for page in src:
        # ensure page is not rotated
        page.set_rotation(0)
        new_page = doc.new_page() # create new empty page
        src_pix = page.get_pixmap(dpi = 300)
        r = new_page.bound()
        new_page.insert_image(fitz.Rect(0, 0, r.x1, r.y1 / 2), pixmap= src_pix, rotate = 90)
        new_page.insert_image(fitz.Rect(0, r.y1 / 2, r.x1, r.y1), pixmap= src_pix, rotate = 90)
        src_pix.save("page-%i.png" % page.number)
    return doc

def rotateDoc(src):
    for page in src:
       page.set_rotation(90)

test()


