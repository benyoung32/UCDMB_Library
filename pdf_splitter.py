import argparse
import sys
from turtle import back
import pdf_reader as reader
import crop_tool as crop
import tkinter as tk
from matplotlib import pyplot as plt
import numpy as np
import cv2 as cv

# root = tk.Tk()
# root.title("Split pdf")
# root.withdraw()
# root.geometry("1000x1000")
# main_frame = tk.Frame(master=root, background = 'grey')
# pdf_canvas = tk.Canvas(main_frame, background = 'light blue',width = 400, height = 400)
# pdf_canvas.grid(row = 0, column = 0, sticky = 'nwes')
# button_frame = tk.Frame(main_frame,  background = 'yellow', width = 400, height = 100)
# button_frame.grid(row = 1, column= 0, sticky = 'nwes')


def main(filename:str):
    docs = reader.openDocuments(filename).values()
    template = cv.imread('.\\template.png.', cv.IMREAD_GRAYSCALE)
    width, height = template.shape[::-1]
    method = eval('cv.TM_CCOEFF_NORMED')
    for doc in docs:
        for page in doc:
            page.set_rotation(0)
            crop.savePageImage(page, 'temp2.png')
            img = cv.imread('temp2.png', cv.IMREAD_GRAYSCALE)
            res = cv.matchTemplate(img, template, method)
            min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)
            top_left = max_loc
            bottom_right = (top_left[0] + width, top_left[1] + height)
            print(top_left, bottom_right)
            cv.rectangle(img,top_left,bottom_right, 150, 10)
            plt.subplot(121),plt.imshow(res,cmap = 'gray')
            plt.title('Matching Result'), plt.xticks([]), plt.yticks([])
            plt.subplot(122),plt.imshow(img,cmap = 'gray')
            plt.title('Detected Point'), plt.xticks([]), plt.yticks([])
            plt.suptitle('result')
    plt.show()

    # main_frame.pack()
    # root.mainloop()

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(sys.argv[0])
    parser.add_argument('filename',type=str, nargs = '?',
                    default=".\pdfs\Baritone 2.pdf")
    main(parser.parse_args().filename)
