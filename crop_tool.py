from copy import copy
import os
import tkinter as tk
from tkinter import font
import tkinter.filedialog
import fitz
import pdf_reader as reader
from PIL import Image,ImageTk
MYFONT = ('Arial',16)
PADDING = 10
RATIO = 8.5/11
SCALE = 1
SHIFT_HELD1 = 262145
SHIFT_HELD2 = 262185
IMAGE_PATH = "temp.png"

def savePageImage(page: fitz.Page, filepath:str)-> None:
    pixmap= page.get_pixmap(dpi=300,colorspace='GRAY')
    pixmap.save(filepath)

def getPagePILImage(parent, page:fitz.Page, dpi = 300, resize:fitz.Point = None) -> Image:
    pix = page.get_pixmap(dpi=dpi,colorspace='GRAY')
    parent.page_image = Image.frombytes('L', [pix.width, pix.height], pix.samples)
    if resize:
        width, height = resize
        parent.page_image = parent.page_image.resize(size=(int(width), int(height)))
    return parent.page_image

def createPageScaledImage(parent, page: fitz.Page, dpi = 300, resize:fitz.Point = None) -> tk.PhotoImage:
    my_image = img = ImageTk.PhotoImage(getPagePILImage(parent, page,dpi, resize),master=parent)
    return my_image

class CropTool(tk.Toplevel):
    def __init__(self,parent,filepath=None) -> None:
        super().__init__(parent)
        self.title("Crop pdf")
        self.geometry("1000x1000")
        self.history = []
        self.keyvar = tk.StringVar()
        self.rotate_var = tk.IntVar(self)
        self.rightalign_var = tk.BooleanVar(self)
        self.fullsize_var = tk.BooleanVar(self)
        self.expand_var = tk.BooleanVar(self)
        self.twoinone_var = tk.BooleanVar(self)
        self.CROPBOX = None
        # print(self.focus_get())
        if not filepath:
            self.path = self.openFile()
        else:
            self.path = filepath
        # self.path = "hm.pdf"
        doc = reader.openDocuments(self.path)[self.path]
        page = doc[0]
        self.page_br = page.bound().br
        # set up canvases 
        self.cv_width, self.cv_height = (self.page_br.x * SCALE,self.page_br.y * SCALE)
        self.main_frame = tk.Frame(master=self,
                    width=self.cv_width * 2 + PADDING * 4, 
                    height = self.cv_height + PADDING * 4,bg='gray')
        self.button_frame = tk.Frame(master=self.main_frame,
                    bg='green',height=10,width =self.cv_width)
        self.pdf_canvas = tk.Canvas(master=self.main_frame, 
                    width = self.cv_width, height=self.cv_height, bg='yellow')
        # preview_canvas= tk.Canvas(master=main_frame, width = cv_width, height = cv_height, bg = 'blue')
        
        self.pdf_canvas.grid(row=0,column=0,sticky='ew',padx=PADDING,pady=PADDING)
        # preview_canvas.grid(row=0,column=1,sticky='ew',padx=PADDING,pady=PADDING)
        self.preview_button = tk.Button(self.button_frame, command=self.createPreviewWindow,
                                width = 10, height = 1,text='Create Preview')
        self.export_button = tk.Button(self.button_frame, command=self.printSettingsString,
                                width = 10, height = 1,text='Export Settings')
        self.crop_folder_button = tk.Button(self.button_frame, command=self.applyCropToFolder,
                                width = 20, height = 1, text = 'Apply to folder')
        self.crop_file_button = tk.Button(self.button_frame, command=self.applyCropToFile, width = 20, height = 1,
                                          text = 'Apply to file')
        self.rotate_entry = EntryWithLabel(self.button_frame,'Rotate?','')
        self.fullsize_box = CheckButtonWithLabel(self.button_frame, 
                                                'Full Size?',self.fullsize_var )
        self.expand_box = CheckButtonWithLabel(self.button_frame,
                                                'Expand?', self.expand_var)
        self.twoinone_box = CheckButtonWithLabel(self.button_frame,
                                                'Two in one?',self.twoinone_var)
        self.rightalign_box = CheckButtonWithLabel(self.button_frame, 
                                                'Right Align?', self.rightalign_var)
        self.button_frame.grid(row=0,column=1,sticky='nw',pady=PADDING,padx=PADDING)
        self.preview_button.grid(row=0,column=0,sticky='nwes')
        self.export_button.grid(row=0,column=1,sticky='nwes')
        self.crop_file_button.grid(row=6,column=0, sticky='nwes')
        self.crop_folder_button.grid(row=7,column=0,sticky='nwes')
        self.rotate_entry.grid(row=1,column=0,sticky='nwes',columnspan=2)
        self.fullsize_box.grid(row=2,column=0,sticky = 'nwes',columnspan=2)
        self.expand_box.grid(row=3,column=0,sticky = 'nwes',columnspan=2)
        self.twoinone_box.grid(row=4,column=0,sticky = 'nwes',columnspan=2)
        self.rightalign_box.grid(row=5,column=0,sticky = 'nwes',columnspan=2)
        self.main_frame.pack(padx=PADDING,pady=PADDING,fill='none')
        myimage = createPageScaledImage(self,page,resize=page.bound().br)
        self.pdf_canvas.create_image(2,2,image=myimage,anchor='nw')
        self.tl = fitz.Point(2,2)
        self.br = copy(self.page_br)

        self.pdf_canvas.bind('<KeyPress>', self.keydown)
        self.pdf_canvas.bind('<KeyRelease>', self.keyup)
        self.pdf_canvas.bind('<Button-1>', self.onClick)
        self.pdf_canvas.bind('<B1-Motion>', self.onDrag)
        self.pdf_canvas.focus_set()

        self.after(30,self.updateKeyboardInput)
        self.bind("<Destroy>", self.kill_root)
        self.mainloop()

    def updateKeyboardInput(self):
        key_string = self.keyvar.get()
        # print(key_string)
        if 'Shift' in key_string or 'Shift_L' in key_string: target = self.tl
        else: target = self.br
        
        if 'Control_L' in key_string: scale = 2
        else: scale = 1
        if  'Left' in key_string: target.x = target.x - scale
        if 'Up' in key_string: target.y = target.y - scale
        if 'Right' in key_string: target.x = target.x  + scale
        if 'Down' in key_string: target.y = target.y + scale
        self.drawCropBox()
        self.after(30,self.updateKeyboardInput)
    
    def onClick(self, event) -> None:
        if not 'Control_L' in self.keyvar.get(): return
        self.tl.x = event.x
        self.tl.y = event.y
        self.drawCropBox()

    def onDrag(self, event):
        if not 'Control_L' in self.keyvar.get(): return
        self.br.x = event.x
        self.br.y = event.y
        self.drawCropBox()

    def openFile(self) -> str:
        # get file info
        answer = tk.filedialog.askopenfile(parent=self.master,
                                initialdir=os.getcwd(),
                                title="Please select a file:",filetypes=[('Pdf File', '*.pdf')])
        # return filepath
        self.grab_set()
        self.focus_get()
        return answer.name

    # draw current cropbox onto pdf_canvas, replacing previous21FD
    def drawCropBox(self) -> None:
        if (self.CROPBOX):
            self.pdf_canvas.delete(self.CROPBOX)
        self.CROPBOX = self.pdf_canvas.create_rectangle(self.tl.x, 
                        self.tl.y, self.br.x, self.br.y,outline='dodger blue',width=1)

    def getSettingsDict(self) -> dict[str, any]:
        args = {}
        tl, br = self.tl, self.br
        print(tl, br)
        args['filename'] = self.path
        args['margins'] = (int(tl.y), int(tl.x) + 10, int(self.page_br.x - br.x) + 10, int(self.page_br.y - br.y))
        args['full_size'] = self.fullsize_var.get()
        args['two_in_one'] = self.twoinone_var.get()
        args['expand'] = self.expand_var.get()
        args['right_align'] = self.rightalign_var.get()
        args['rotate'] = self.getRotation()    
        # print(args)
        return args

    def getSettingsString(self) -> str:
        global page_br
        args = self.getSettingsDict()
        out = '\"' + self.path + '\"' 
        for v in ['full_size','two_in_one','expand','right_align']:
            if args[v]:
                out += ' -' + v
        for n in args['margins']:
            out += ' ' + str(n)
        out += ' ' + str(args['rotate'])
        return out

    def printSettingsString(self) -> None:
        print(self.getSettingsString())
    
    def applyCropToFolder(self) -> None:
        ''' apply current settings to the folder where the sample came from '''
        folder= os.path.dirname(self.path)
        files = reader.getSubFiles(folder)
        # print(files)
        reader.openCropSaveDocs(files, reader.prefix, **self.getSettingsDict())
    
    def applyCropToFile(self) -> None:
        reader.processDocs(self.path, reader.prefix, **self.getSettingsDict())
    
    # get rotation from entry box, sanitize input
    def getRotation(self) -> int:
        rotation = self.rotate_entry.get()
        try:
            rotation = int(rotation)
            if not (rotation in [0,90,270]): raise Exception('invalid rotation value')
        except:
            self.rotate_entry.delete(0)
            rotation = 0
        return rotation

    def createPreviewWindow(self) -> None:
        args = self.getSettingsDict()
        doc = reader.openDocuments(self.path,size='a4')[self.path]
        # alter document using settings 
        newdoc = reader.createCroppedDocument(doc,**args)
        # create new window to show altered document
        preview_window = PDFWindow(self,newdoc,'Crop Preview')

    def kill_root(self, event) -> None:
        if event.widget == self and self.master.winfo_exists():
            self.master.destroy()
    
    def keyup(self,event) -> None:
        if event.keysym in self.history:
            self.history.pop(self.history.index(event.keysym))
            self.keyvar.set(str(self.history))

    def keydown(self, event) -> None:
        if not event.keysym in self.history:
            self.history.append(event.keysym)
            self.keyvar.set(str(self.history))

class EntryWithLabel(tk.Frame):
    '''
    Custom widget that combines a tk.Label and a tk.Entry side by side
    '''
    def __init__(self, parent:tk.Widget, label:str, default:str="") -> None:
        tk.Frame.__init__(self, parent)
        self.label = tk.Label(self, text=label, anchor="w")
        self.entry = tk.Entry(self)
        self.entry.insert(0, default)
        self.label.pack(side="left", fill="both")
        self.entry.pack(side="right", fill="both", padx=4)
   
    def get(self) -> str:
        return self.entry.get()
    
    def delete(self,index) -> None:
        self.entry.delete(index)

class CheckButtonWithLabel(tk.Frame):
    '''
    Custom widget that combines a tk.Label and a tk.Checkbutton side by side
    '''
    def __init__(self, parent:tk.Widget, label:str, var:tk.Variable) -> None:
        tk.Frame.__init__(self, parent)
        self.label = tk.Label(self, text=label, anchor="w")
        self.checkbutton = tk.Checkbutton(self,variable=var)
        self.label.pack(side="left", fill="both")
        self.checkbutton.pack(side="right", fill="both", padx=4)

class PDFWindow(tk.Toplevel):
    def __init__(self,parent:tk.Widget,doc:fitz.Document,title:str) -> None:
        tk.Toplevel.__init__(self, parent)
        br = doc[0].bound().br
        self.image_id = -1
        self.title(title)
        self.geometry('{0}x{1}'.format(int(br.x), int(br.y)))
        self.image_canvas = PDFCanvas(self,doc)
        self.image_canvas.pack()

class PDFCanvas(tk.Frame):
    def __init__(self, parent:tk.Widget,doc:fitz.Document,label_var:tk.StringVar = None) -> None:
        tk.Frame.__init__(self, parent)
        self.doc = doc
        self.page_images = [None] * doc.page_count
        self.pagenum = 0
        page = doc[0]
        br = page.bound().br
        self.configure(relief='groove',borderwidth=4,width=int(br.x),
                       height=int(br.y),padx=5,pady=5,bg='snow2')
        self.image_id = -1
        if label_var != '':
            self.label_var = label_var
            self.label = tk.Label(self,textvariable=self.label_var,
                                  font=MYFONT)
            self.label.grid(row=0,column=0,pady=5)
        else:
            self.label = None
        self.image_canvas = tk.Canvas(self,bg='white',width=br.x, height=br.y)
        self.image_canvas.grid(row=1,column=0)
        # self.bind('<Configure>', self.updateImageSize)
        self.updatePage(0)
    
    def updateImageSize(self, event) -> None:
        self.updateImage(self.page_images[self.pagenum]) 

    def updatePage(self, page_number:int) -> None:
        if not self.page_images[page_number]:
            page = self.doc[page_number]
            self.page_images[page_number] = createPageScaledImage(self, page,dpi=100,resize=page.bound().br)
        img = self.page_images[page_number]
        self.pagenum = page_number
        self.updateImage(img)

    def updateImage(self, img:Image) -> None:
        self.img = img
        self.clear()
        self.image_id = self.image_canvas.create_image(0,0,image=self.img,anchor='nw')

    def preloadImages(self) -> None:
        for i, page in enumerate(self.doc):
            self.page_images[i] = createPageScaledImage(self, page,dpi=100,resize=page.bound().br)
    

    def clear(self) -> None:
        if self.image_id != -1:
            self.image_canvas.delete(self.image_id)
            self.image_id = -1
    
        # self.geometry('{0}x{1}'.format(int(br.x), int(br.y)))
if __name__ == "__main__":
    root = tk.Tk()
    root.grab_set()
    root.withdraw()
    CropTool(root)    
# show preview