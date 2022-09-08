# -*- coding: utf-8 -*-
import os
import glob
import pathlib
import my_prompt
from tkinterdnd2 import *
from tkinter import *
from tkinter.scrolledtext import ScrolledText
from tkinter import filedialog

# dict linking filenames with their filepaths 
filedict = {}

root = TkinterDnD.Tk()
root.withdraw()
root.title('TkinterDnD demo')
root.minsize(width = 600, height = 400)
root.geometry("600x400")
root.grid_rowconfigure(1, weight=1, minsize=250)
root.grid_columnconfigure(0, weight=1, minsize=300)
root.grid_columnconfigure(1, weight=1, minsize=300)



Label(root, text='Drag and drop files here:').grid(
                    row=0, column=0, padx=10, pady=5)
buttonbox = Frame(root)
buttonbox.grid(row=2, column=0, columnspan=2, pady=5)

def add_files(filepaths):
    for filepath in filepaths:
        path = pathlib.PurePath(filepath)
        filedict.append(path.name, path)

def delete_files(first, last):

    paths = listbox.get(first, last)
    for path in paths:
        filedict.pop(path)
    #listbox.

def open_selection():
    if len((sel := listbox.curselection())) > 0:
        pass

def open_folder():
    # get folder using file explorer
    answer = filedialog.askdirectory(parent=root,
                                 initialdir=os.getcwd(),
                                 title="Please select a folder:")
    filenames = []
    if answer: # check if not empty 
        print(answer)
        for file in glob.glob(answer + "/*.pdf"):
            filenames.append(file)
    prompt = my_prompt.MyPrompt(root, 'how many', filenames)
    return filenames

listbox = Listbox(root, name='dnd_demo_listbox',
                    selectmode='extended', width=1, height=1)
listbox.grid(row=1, column=0, padx=5, pady=5, sticky='news')

Button(buttonbox, text='Quit', command=root.quit).pack(
                    side=LEFT, padx=5)
Button(buttonbox, text='Delete Selected', command = (lambda : delete_files(listbox.curselection))).pack(
                    side=LEFT, padx=5)
Button(buttonbox, text='Open Folder', command=open_folder).pack(
                    side=LEFT, padx=10)



def drop_enter(event):
    event.widget.focus_force()
    # print('Entering widget: %s' % event.widget)
    #print_event_info(event)
    return event.action
    # pass

def drop_position(event):
    # print('Position: x %d, y %d' %(event.x_root, event.y_root))
    #print_event_info(event)
    return event.action
    # pass

def drop_leave(event):
    #print('Leaving %s' % event.widget)
    #print_event_info(event)
    return event.action

def drop(event):
    if event.data:
        # print('Dropped data:\n', event.data)
        #print_event_info(event)
        if event.widget == listbox:
            # event.data is a list of filenames as one string;
            # if one of these filenames contains whitespace characters
            # it is rather difficult to reliably tell where one filename
            # ends and the next begins; the best bet appears to be
            # to count on tkdnd's and tkinter's internal magic to handle
            # such cases correctly; the following seems to work well
            # at least with Windows and Gtk/X11
            files = listbox.tk.splitlist(event.data)
            for f in files:
                if os.path.exists(f):
                    # print('Dropped file: "%s"' % f)
                    listbox.insert('end', f)
                else:
                    print('Not dropping file "%s": file does not exist.' % f)

        else:
            print('Error: reported event.widget not known')
    return event.action

# now make the Listbox and Text drop targets
listbox.drop_target_register(DND_FILES)

listbox.dnd_bind('<<DropEnter>>', drop_enter)
listbox.dnd_bind('<<DropPosition>>', drop_position)
listbox.dnd_bind('<<DropLeave>>', drop_leave)
listbox.dnd_bind('<<Drop>>', drop)
    #widget.dnd_bind('<<Drop:DND_Files>>', drop)
    #widget.dnd_bind('<<Drop:DND_Text>>', drop)

# define drag callbacks

def drag_init_listbox(event):
    # print_event_info(event)
    # use a tuple as file list, this should hopefully be handled gracefully
    # by tkdnd and the drop targets like file managers or text editors
    data = ()
    if listbox.curselection():
        data = tuple([listbox.get(i) for i in listbox.curselection()])
        #print('Dragging :', data)
    # tuples can also be used to specify possible alternatives for
    # action type and DnD type:
    return ((ASK, COPY), (DND_FILES, DND_TEXT), data)

def drag_end(event):
    #print_event_info(event)
    # this callback is not really necessary if it doesn't do anything useful
    #print('Drag ended for widget:', event.widget)
    pass

# finally make the widgets a drag source

def print_event_info(event):
    print('\nAction:', event.action)
    print('Supported actions:', event.actions)
    print('Mouse button:', event.button)
    print('Type codes:', event.codes)
    print('Current type code:', event.code)
    print('Common source types:', event.commonsourcetypes)
    print('Common target types:', event.commontargettypes)
    print('Data:', event.data)
    print('Event name:', event.name)
    print('Supported types:', event.types)
    print('Modifier keys:', event.modifiers)
    print('Supported source types:', event.supportedsourcetypes)
    print('Operation type:', event.type)
    print('Source types:', event.sourcetypes)
    print('Supported target types:', event.supportedtargettypes)
    print('Widget:', event.widget, '(type: %s)' % type(event.widget))
    print('X:', event.x_root)
    print('Y:', event.y_root, '\n')

listbox.drag_source_register(1, DND_TEXT, DND_FILES)

listbox.dnd_bind('<<DragInitCmd>>', drag_init_listbox)
listbox.dnd_bind('<<DragEndCmd>>', drag_end)

# skip the useless drag_end() binding for the text widget

root.update_idletasks()
root.deiconify()
root.mainloop()