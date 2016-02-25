import tkinter as tk
import webbrowser
import os

class simpleGUI_tk(tk.Tk):
    def __init__(self,parent):
        tk.Tk.__init__(self,parent)
        self.parent = parent
        self.menu()

    def openFile(self):
        print("bruh")
        #
    def saveLocation(self):
        print("bruh")
        #save what was run
    def runFinderProgram(self):
        print("")
    def output(self):
        print(os.getcwd())
        f = open('map_240.0.html','w')

        # message = """<html>
        # <head></head>
        # <body><p>Hello World!</p></body>
        # </html>"""
        #
        # f.write(message)
        f.close()

        webbrowser.open_new_tab('map_240.0.html')
        #call elham's code
    def aboutFinder(self):
        print("here is the explanation of what the finder does, add extra stuff")

    def menu(self):

        menubar = tk.Menu()

        # create a pulldown menu, and add it to the menu bar
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open Test Case", command=self.openFile)
        filemenu.add_command(label="Save", command=self.saveLocation)
        filemenu.add_command(label="Run", command=self.runFinderProgram)
        filemenu.add_command(label="Output Map", command=self.output)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=filemenu)



        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="About", command=self.aboutFinder)
        menubar.add_cascade(label="Help", menu=helpmenu)

        # display the menu
        self.config(menu=menubar)




        #label = tkinter.Label(self,anchor="w",fg="white",bg="blue")
        #label.grid(column=0,row=1,columnspan=2,sticky='EW')

        self.grid_columnconfigure(0,weight=1)


if __name__ == "__main__":
    app = simpleGUI_tk(None)
    app.title('Missing Persons Locater')
    app.mainloop()



