import tkinter as tk

def drag_widget(event):
    if (w:=root.dragged_widget): #walrus assignment
        cx,cy = w.winfo_x(), w.winfo_y() #current x and y
        #deltaX and deltaY to mouse position stored
        dx = root.marked_pointx - root.winfo_pointerx()
        dy = root.marked_pointy - root.winfo_pointery()
        #adjust widget by deltaX and deltaY
        w.place(x=cx-dx, y=cy-dy)
        #update the marked for next iteration
        root.marked_pointx = root.winfo_pointerx()
        root.marked_pointy = root.winfo_pointery()

def drag_init(event):
    if event.widget is not root:
        #store the widget that is clicked
        root.dragged_widget = event.widget
        #ensure dragged widget is ontop
        event.widget.lift()
        #store the currently mouse position
        root.marked_pointx = root.winfo_pointerx()
        root.marked_pointy = root.winfo_pointery()

def finalize_dragging(event):
    #default setup
    root.dragged_widget = None
    
root = tk.Tk()
#name and register some events to some sequences
root.event_add('<<Drag>>', '<B1-Motion>')
root.event_add('<<DragInit>>', '<ButtonPress-1>')
root.event_add('<<DragFinal>>', '<ButtonRelease-1>')
#bind named events to the functions that shall be executed
root.bind('<<DragInit>>', drag_init)
root.bind('<<Drag>>', drag_widget)
root.bind('<<DragFinal>>',finalize_dragging)
#fire the finalizer of dragging for setup
root.event_generate('<<DragFinal>>')
#populate the window
for color in ['yellow','red','green','orange']:
    tk.Label(root, text="test",bg=color).pack()

root.mainloop()
