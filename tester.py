import unittest
import sys
import os
import fitz # type: ignore

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import pdf_grouper as grouper

sys.path.append("C:\\Users\\benyo\\Code\\UCDMB_Library\\test_files\\**")
import pdf_grouper as grouper
import pdf_reader as reader
import pdf_splitter as splitter 

TEST_FOLDER = "test_files\\"
PASS = ''
def are_pdfs_equal(pdf1: fitz.Document, pdf2: fitz.Document) -> str:
    desc = str(pdf1) + " and " + str(pdf2)
    if not pdf1.page_count == pdf2.page_count: return desc + " have different page count"
    for p1, p2 in zip(pdf1, pdf2):
        # check they are the same size
        r1 = p1.bound()
        r2 = p2.bound()
        if not r1.width == r2.width: return desc + " are not the same width"
        if not r1.height == r2.height: return desc + " are not the same height"
        
        # check every pixel is the same
        pix1 = p1.get_pixmap()
        pix2 = p2.get_pixmap()
        mismatch = 0 
        for x in range(int(pix1.width)):
            for y in range(int(pix1.height)): 
                if not pix1.pixel(x, y) == pix2.pixel(x,y ): 
                    mismatch += 1
                    return desc + " differ at pixel " + str(x) + ", " + str (y)
    return PASS # return good message

class doc_tests(unittest.TestCase):
    def test_pdf_reader(self) -> None:
        tests = [("left_align", reader.leftAlign), 
                 ("right_align", reader.rightAlign),
                 ("splitTopBottom", reader.splitTopBottom),
                 ("")]
        for test in tests:
            doc = fitz.open(TEST_FOLDER + test[0] + "\\input.pdf")
            truth = fitz.open(TEST_FOLDER + test[0] + "\\truth.pdf")
            doc = test[1](doc)
            msg = are_pdfs_equal(doc, truth)
            self.assertTrue(msg == PASS, msg)

if __name__ == '__main__':
    unittest.main()