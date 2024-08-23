from ast import Pass
from pyclbr import Function
from typing import Callable
import unittest
import sys
import os
import fitz # type: ignore

import pdf_grouper as grouper
import pdf_reader as reader
import pdf_splitter as splitter 
import my_file_utils as utils
from part import *

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append("C:\\Users\\benyo\\Code\\UCDMB_Library\\test_files\\**")

TEST_FOLDER = "test_files\\"
PASS = ''

class FunctionTest:
    def __init__(self, test_name: str, input: Any, functions: list[Callable]) -> None:
        self.test_name = test_name
        self.functions = functions
        self.input = input
        self.result = None

    def run(self) -> Any:
        result = self.input
        for func in self.functions:
            result = func(result)
        self.result = result
        return result

# returns PASS msg if two pdfs are equal, else returns error msg describing the first difference found 
def are_pdfs_equal(pdf1: fitz.Document, pdf2: fitz.Document) -> str:
    desc = str(pdf1) + " and " + str(pdf2)
    if not pdf1.page_count == pdf2.page_count: return desc + " have different page count"
    for p1, p2 in zip(pdf1, pdf2):
        # check they are the same size
        r1 = p1.bound()
        r2 = p2.bound()
        if not r1.width == r2.width: return desc + " are not the same width"
        if not r1.height == r2.height: return desc + " are not the same height"
        
        pix1 = p1.get_pixmap()
        pix2 = p2.get_pixmap()
        mismatch = 0 
        ''' how many pixels to check? Significantly effects runtime. eg:
            PRECISION = 1 -> check every pixel
            PRECISION = 10 -> check every 10th pixel
        '''
        PRECISION = 4 
        for x in range(0, int(pix1.width), PRECISION):
            for y in range(0, int(pix1.height), PRECISION): 
                if not pix1.pixel(x, y) == pix2.pixel(x,y ): 
                    mismatch += 1
                    return desc + " differ at pixel " + str(x) + ", " + str (y)
    return PASS

def create_json_truth(tests: list[FunctionTest], output_path: str) -> dict[str, str]:
    json_out = {}
    for test in tests:
        json_out[test.test_name] = test.run()
    with open(output_path, "+w") as out_file:
        json.dump(json_out, out_file, indent = 4)
    return json_out

def add_to_json(json_filepath: str, add: dict[str, str]) -> dict[str, str]:
    with open(json_filepath, "+a") as json_file:
        json_out = json.load(json_file)
        for k, v in add.items():
            json_out[k] = v
        json.dump(json_out, json_file)
    return json_out

class doc_tests(unittest.TestCase):
    def test_pdf_reader(self) -> None:
        tests = [("left_align", [reader.leftAlign]), 
                 ("right_align", [reader.rightAlign]),
                 ("splitTopBottom", [reader.leftAlign, reader.splitTopBottom])
                 ]
        for test in tests:
            doc = fitz.open(TEST_FOLDER + "\\doc_tests\\" + test[0] + "\\input.pdf") # type: ignore
            truth = fitz.open(TEST_FOLDER + "\\doc_tests\\" + test[0] + "\\truth.pdf") # type: ignore
            for func in test[1]:
                doc = func(doc)
            msg = are_pdfs_equal(doc, truth)
            reader.saveDocument(doc, TEST_FOLDER + "\\doc_tests\\" + test[0] + "\\result.pdf",prefix='')
            self.assertTrue(msg == PASS, msg)

class part_tests(unittest.TestCase):
    def test_part_creation(self) -> None:
        for part_name, aliases in JSON_ALIAS.items():
            part_truth = Part(part_name)
            for alias in aliases:
                part_test = Part(alias)
                with self.subTest(msg=f'checking {part_name}'): 
                    self.assertTrue(part_truth == part_test, f"{alias} does not match to {part_name}")
    
    def test_drum_case(self) -> None:
        tests = [
            ("snare", "Drum - Snare"),
            ("bass", "Drum - Bass"),
            ("glock", "Drum - Glock"),
            ("glock", "Drums - Glocks"),
            ("quads", "Drum - Quads"),
        ]
        for test in tests:
            part_name = test[0]
            part_truth = Part(part_name)
            part_test = Part(test[1])
            with self.subTest(msg=f'checking {part_name}'): 
                self.assertTrue(part_truth == part_test, f"{test[1]} does not match to {part_name}")

class grouper_tests(unittest.TestCase):
    def test_part_from_filepath(self) -> None:

        truth_file = f"{TEST_FOLDER}grouper_tests\\truths.json"
        test = FunctionTest("getPartFromFilepath", [f"{TEST_FOLDER}example_subfolder"], 
                         [utils.getSubFiles, 
                          lambda a : list(map(str, map(getPartFromFilepath, a)))]),
        with open(truth_file) as f:
            truth = json.load(f)
            self.assertEqual(test[0].run(), truth[test[0].test_name]) 

    def test_part_dict(self) -> None:
        pass
        parts = utils.readFile(f"{TEST_FOLDER}parts.txt")
        parts = [Part(s) for s in parts if s != ERROR_PART]
        truth_file = f"{TEST_FOLDER}grouper_tests\\file_dict.json"
        result = grouper.findPartFiles([f"{TEST_FOLDER}example_subfolder\\dir1"], parts)
        with open(truth_file) as f:
            json_out = {}
            truth = json.load(f)
            for k, v in result.items():
                json_out[str(k)] = v
            self.assertEqual(json_out[str(k)], truth[str(k)], 
                f"{json_out[str(k)]} does not match {truth[str(k)]} for part: {str(k)}")
            truth["test result"] = json_out
        with open(truth_file, "w") as f:
            json.dump(truth, f, indent = 4)

class utils_tests(unittest.TestCase):
    def test_good_inputs(self) -> None:
        truth_file = f"{TEST_FOLDER}util_tests\\truths.json"
        tests = [
            FunctionTest("getSubFiles", [f"{TEST_FOLDER}example_subfolder"], [utils.getSubFiles]),
            FunctionTest("getSubFolders", [f"{TEST_FOLDER}example_subfolder"], [utils.getSubFolders]),
            FunctionTest("readFile1", f"{TEST_FOLDER}util_tests\\test_file1.txt", [utils.readFile]),
            FunctionTest("readFile2", f"{TEST_FOLDER}util_tests\\test_file2.txt", [utils.readFile]),
        ]
        # create_json_truth(tests, truth_file)
        with open(truth_file) as f:
            truth = json.load(f)
            # self.maxDiff = None
            for test in tests:
                self.assertEqual(test.run(), truth[test.test_name], f"{test.test_name} did not have the expected output")
    
    def test_bad_inputs(self) -> None:
        tests = [
            FunctionTest("getSubFiles bad filename", "hi :)", [utils.getSubFiles]),
            FunctionTest("getSubFolder bad filename", "hi :)", [utils.getSubFolders]),
            FunctionTest("getSubFiles non-existing file", ["no file"], [utils.getSubFiles]),
            FunctionTest("getSubFolders non-existing file", ["no file"], [utils.getSubFolders])
        ]
        for test in tests:
            test.run()

unittest.main()