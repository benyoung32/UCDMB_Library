import os
import tkinter as tk
import tkinter.filedialog
from turtle import color
import fitz
import pdf_reader as reader
from PIL import Image,ImageTk
PADDING = 10
RATIO = 8.5/11
SCALE = 1
SHIFT_HELD = 262145
IMAGE_PATH = "temp.png"
CROPBOX_ID = None
# ROTATE = 0

cv_width, cv_height = None, None
root = tk.Tk()
# temp init 
main_frame = tk.Frame(master=root)
pdf_canvas = tk.Canvas(root)
preview_canvas= tk.Canvas(root)
page:fitz.Page = None

tl = fitz.Point(5,5)
br = fitz.Point(100,100)
page_br = fitz.Point()

# get filepath from dialog
def openFile() -> str: 
        # get file info
        answer = tkinter.filedialog.askopenfile(parent=root,
                                 initialdir=os.getcwd(),
                                 title="Please select a file:",filetypes=[('Pdf File', '*.pdf')])
        # return filepath
        return answer.name

# get page sized tk.PhotoImage from a fitz.Page 
def getPageScaledImage(page) -> tk.PhotoImage:
    width, height = page.bound().br
    pixmap= page.get_pixmap(dpi=300)
    pixmap.save(IMAGE_PATH)
    img = Image.open(IMAGE_PATH)
    img = img.resize(size=(int(width), int(height)))
    return ImageTk.PhotoImage(img)

# draw current cropbox onto pdf_canvas, replacing previous
def drawCropBox() -> None:
    # clear previous box, if any
    global CROPBOX_ID
    if (CROPBOX_ID):
        pdf_canvas.delete(CROPBOX_ID)
    CROPBOX_ID = pdf_canvas.create_rectangle(tl.x, tl.y, br.x, br.y,outline='dodger blue',width=1)
    # pdf_canvas.create_rectangle(10,10,100,100)

def onKeyPress(event):
    global tl, br
    # print('You pressed %s\n' % (event.char))
    sym = event.keysym
    negative = False
    if event.state == SHIFT_HELD:
         negative = True
         print("shift")
    # print(event.state)
    if sym == 'Left':
        if negative:
            tl.x = tl.x - 1
        else:
            br.x = br.x - 1
    elif sym == 'Up':
        if negative:
            tl.y = tl.y - 1
        else:
            br.y = br.y - 1
    elif sym == 'Right':
        if negative:
            tl.x = tl.x  + 1
        else:
            br.x = br.x + 1
    elif sym == 'Down':
        if negative:
            tl.y = tl.y + 1
        else:
            br.y = br.y + 1
    else:
        return
    drawCropBox()

def init():
    global pdf_canvas, main_frame, root, tl, br
    print('creating window...')
    root.title("Crop pdf")
    root.geometry("1000x1000")
    # pdf_canvas.pack(pady=20)
    # path = openFile()
    path = 'C:\\Users\\benyo\\Code\\UCDMB_Library\\pdfs\\Everybody Talks-Tenor_Saxophone.pdf'
    doc = reader.openDocuments(path)[path]
    page = doc[0]
    
    # set up canvases 
    page_br = page.bound().br
    cv_width,cv_height = (page_br.x * SCALE,page_br.y * SCALE)
    main_frame = tk.Frame(master=root,width=cv_width * 2 + PADDING * 4, height = cv_height + PADDING * 4,bg='red')
    pdf_canvas = tk.Canvas(master=main_frame, width = cv_width, height=cv_height, bg='yellow')
    # preview_canvas= tk.Canvas(master=main_frame, width = cv_width, height = cv_height, bg = 'blue')
    
    pdf_canvas.grid(row=0,column=0,sticky='ew',padx=PADDING,pady=PADDING)
    # preview_canvas.grid(row=0,column=1,sticky='ew',padx=PADDING,pady=PADDING)   
    main_frame.pack(padx=PADDING,pady=PADDING)
    pdf_canvas.pack(padx=PADDING,pady=PADDING)

    # draw page to the canvas
    img = getPageScaledImage(page)
    pdf_canvas.create_image(2,2,image=img,anchor='nw')
    # pdf_canvas.create_rectangle(10,10,100,100)
    drawCropBox()
    tl = fitz.Point(2,2)
    br = page_br
    drawCropBox()
    root.bind('<KeyPress>', onKeyPress)
    root.mainloop()

if __name__ == "__main__":
    init()    
# translate points between canvas pixels and pdf points      
# show preview