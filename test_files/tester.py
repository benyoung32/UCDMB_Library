import unittest
import sys

import pdf_grouper as grouper

sys.path.append("C:\Users\benyo\Code\UCDMB_Library\pdfs")


import pdf_grouper as grouper
import pdf_reader as reader
import pdf_splitter as splitter 

import fitz
import fitz._fitz

def are_pdfs_equal(pdf1: fitz.Document, pdf2: fitz.Document) -> bool:
    if not pdf1.width == pdf2.width: return False
    if not pdf1.height == pdf2.height: return False

    if not pdf1.page_count == pdf2.page_count: return False
    pix1 = pdf1.get_pixmap()
    pix2 = pdf2.get_pixmap()


    for x in range(pdf1.width):
        for y in range(pdf1.height): 
            if not pix1.pixel(x, y) == pix2.pixel(x,y ): return False 
    return True

class TestStringMethods(unittest.TestCase):
        
    def test_left_align(self):
        doc = fitz.open("reference.pdf")
        doc = reader.leftAlign(doc)
        truth = fitz.open("left_align.pdf")
        self.assertTrue(are_pdfs_equal(doc, truth))

    def test_right_align(self):
        doc = fitz.open("reference.pdf")
        doc = reader.rightAlign(doc)
        truth = fitz.open("right_align.pdf")
        self.assertTrue(are_pdfs_equal(doc, truth))

if __name__ == '__main__':
    unittest.main()