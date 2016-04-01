from tkinter import *
from tkinter import ttk
from demopanels import MsgPanel, SeeDismissPanel
import tkinter as tk
import webbrowser
import os
import pandas as pd
import numpy as np

class simpleGUI_tk(tk.Tk):

    def __init__(self,parent):

        tk.Tk.__init__(self,parent)

        self.parent = parent
        self.menu()
        self.list()

    def openFile(self):
        print("")
        #

    def runFinderProgram(self):
        print("")
    # def button(self):
        # print(os.getcwd())
        # f = open('map_240.0.html')
        # f.close()
        # webbrowser.open_new_tab('map_240.0.html')
        #call elham's code



    def aboutFinder(self):
        print("here is the explanation of what the finder does, add extra stuff")

    def analyze(self):
        print("")
    def createModel(self):
        print("")
    def menu(self):

        menubar = tk.Menu()

        # create a pulldown menu, and add it to the menu bar
        filemenu = tk.Menu(menubar, tearoff=0)
        # filemenu.add_command(label="Open Test Case", command=self.openFile)

        filemenu.add_command(label="Run", command=self.runFinderProgram)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=filemenu)



        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="About", command=self.aboutFinder)
        menubar.add_cascade(label="Help", menu=helpmenu)

        modelMenu = tk.Menu(menubar, tearoff = 0)
        modelMenu.add_command(label="Create Model", command=self.createModel())
        menubar.add_cascade(label="Create Model", menu=modelMenu)
        analysisMenu = tk.Menu(menubar, tearoff = 0)
        analysisMenu.add_command(label="Analyze Result", command=self.analyze())
        menubar.add_cascade(label="Analyze Result", menu=analysisMenu)
        # display the menu
        self.config(menu=menubar)


        #label = tkinter.Label(self,anchor="w",fg="white",bg="blue")
        #label.grid(column=0,row=1,columnspan=2,sticky='EW')

        self.grid_columnconfigure(0,weight=1)

    def list(self):
        input=pd.read_csv('FinalCases_V13.csv', encoding='latin1',dtype={'Found lat':str})
         # dtype={'Found lat':str}
        nameList=list(input['name'][np.logical_or(input['Found lat'].isnull(),input['Found lng'].isnull())].values)
        demoPanel = Frame(self)
        demoPanel.pack(side=TOP, fill=BOTH, expand=Y)

        # create comboboxes

        showNames = ttk.Labelframe(demoPanel, text='Name List')
        ttk.Combobox(showNames,values=nameList, state='readonly').pack(pady=5, padx=10)
        showNames.pack(in_=demoPanel, side=TOP, pady=5, padx=10)

        button = tk.Button(self,text = "Output Map")
        button.pack(in_ = demoPanel, side = BOTTOM, pady = 80, padx = 10)


if __name__ == "__main__":

    root = simpleGUI_tk(None)
    root.geometry('450x250')

    root.title('Missing Persons Locater')


    root.mainloop()



#Allow for input, run algorithm, if successful show message, output the result