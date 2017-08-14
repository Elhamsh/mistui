from Tkinter import *
import ttk
import Tkinter as tk
import webbrowser
import os
import pandas as pd
import numpy as np
import MILP
import DrawMap as dm
import os
from Tkinter import PhotoImage
import image
#from PIL import ImageTk

class simpleGUI_tk(tk.Tk):
    path = ''
    def __init__(self,parent):
        self.path = path
        tk.Tk.__init__(self,parent)
        self.cases=pd.read_csv(self.path+'Data/FinalCases_V16.csv', encoding='latin1',dtype={'Found lat':str})
        self.reports=pd.read_csv(self.path+'Data/Checked_FinalReports.csv', encoding='latin1')
        self.parent = parent
        self.menu()
        self.value_of_combo = ''
        self.selectedCaseNum=''
        self.list()
        self.button = tk.Button(self.parent, text = "Output Map")

    def PreprocessEvent(self, event):
        self.Preprocess()

    def Preprocess(self):
        obj.AtomRepDistDRT()

    def runFinderProgramEvent(self, event):
        self.runFinderProgram()

    def runFinderProgram(self):
        print("")
        # cases= [21.0, 24.0, 42.0, 53.0, 68.0, 85.0, 107.0, 110.0, 112.0, 166.0, 177.0, 211.0, 218.0, 219.0, 231.0, 234.0, 239.0, 240.0,
        # 241.0, 248.0, 251.0, 253.0, 256.0, 258.0, 265.0, 274.0, 276.0,279.0,280.0,283.0,286.0,287.0]
        train_cases=list(set(self.cases.dropna(subset=['Found lat', 'Found lng'])['Case Num'])&set(self.reports.dropna(subset=['Loc N/lat', 'Loc W/lng'])['Case Num']))
        if self.selectedCaseNum in self.reports.dropna(subset=['Loc N/lat', 'Loc W/lng'])['Case Num'].values:
            if self.selectedCaseNum in train_cases:
                train_cases.remove(self.selectedCaseNum)
            obj.Test(eps=0.03, wcc='W', TrainSet=train_cases, Test=self.selectedCaseNum)
        else:
            print 'no reported location'

    def drawInputEvent(self, event):
        self.drawInput()

    def drawInput(self):
        dm.createInput(self.path, self.selectedCaseNum)
        filename = "file://"+os.getcwd()+"/"+self.path+'Output/Inp_'+str(self.selectedCaseNum)+'.html'
        webbrowser.open_new_tab(filename)

    def drawOutputEvent(self,event):
        self.drawOutput()

    def drawOutput(self):
        try:
            dm.createTest(self.path, self.selectedCaseNum)
        except:
            print 'Error in draw output::createTest'

        filename = "file://"+os.getcwd()+"/"+self.path+'Output/'+str(self.selectedCaseNum)+'.html'
        #C:\Users\eshaaban\PycharmProjects\MISTUI\Output\292.html
        webbrowser.open_new_tab(filename)

    def aboutFinder(self):
        window = tk.Toplevel(root)
        window.maxsize(400,500)
        window.title("About")
        window.configure(background='black')
        aboutMessage = "\n MIST 1.0 \n\n Powered by CySIS Lab \n\n School of Computing, Informatics, and Decision Systems Engineering (CIDSE)\n Ira A. Fulton School of Engineering\n Arizona State University \n" \
                       " \n\nThe CySIS Lab is primarily focused on conducting basic research relating to challenging problems in cyber security, " \
                       "social network mining, security informatics, and artificial intelligence with the goal of creating intelligent systems that have a significant impact on real-world problems."

        image = path+"MISTUI/cysis_sign2.gif"
        #image=open(image)
        img = PhotoImage(file=image)
        img = img.subsample(8, 8)
        panel = tk.Label(window, image = img)
        panel2= tk.Label(window, text=aboutMessage, justify=LEFT, wraplength=370)
        panel.pack(side = "top",expand = "yes")
        panel2.pack( side = "bottom", fill = "both", expand=True)
        window.mainloop()
        # pic = PhotoImage(file='cysis_sign2.jpg')
        # msg = Message(window, text=aboutMessage,image=pic)
        # msg.pack()

    def aboutFinderEvent(self,event):
        self.aboutFinder()

    def helpFinderEvent(self,event):
        self.helpFinder()

    def helpFinder(self):
        window = tk.Toplevel(root)
        window.minsize(400,300)
        window.title("Help")
        helpMessage = "Instructions to run Finder: \n1. Select the case name to be analyzed\n" + "2. Press the 'Preprocess' button under the File tab." +\
                      "\n3. Press the 'Run' button under the 'Preprocess' tab\n" + \
                      "4. Under 'Draw', press 'Visualize Input' in order to see the inputs (reported locations) displayed on a map\n" +\
                      "5. Otherwise, press 'Search Area' to display the output onto the map after the input has been processed.\n"+\
                      "6. Lastly, 'Exit'quits out of the program\n\n" + "Shortcuts: \nPreprocess: CTRL + P\nRun: CTRL + R\nExit: CTRL + " \
                                                                        "E\nVisualize Input: CTRL + I\nSearch Area: CTRL + S\nHelp: CTRL + H\nAbout: CTRL + A"
        msg = Message(window, text=helpMessage)
        msg.pack()




    def menu(self):
        menubar = tk.Menu()

        # create a pulldown menu, and add it to the menu bar
        filemenu = tk.Menu(menubar, tearoff=0)
        # filemenu.add_command(label="Open Test Case", command=self.openFile)
        filemenu.add_command(label='Preprocess', command=self.Preprocess, accelerator="ctrl+P")
        self.bind("<Control-p>", self.PreprocessEvent)

        filemenu.add_command(label="Run", command=self.runFinderProgram, accelerator="Ctrl+R")
        self.bind("<Control-r>", self.runFinderProgramEvent)

        drawMenu = Menu(filemenu)
        drawMenu.add_command(label='Visualize Input', command=self.drawInput,accelerator="Ctrl+I")
        self.bind("<Control-i>", self.drawInputEvent)

        drawMenu.add_command(label='Search Area', command=self.drawOutput, accelerator="Ctrl+S")
        self.bind("<Control-s>", self.drawOutputEvent)

        filemenu.add_cascade(label="Draw", menu=drawMenu)
        filemenu.add_separator()

        filemenu.add_command(label="Exit", command=self.quit, accelerator="Ctrl+E")
        self.bind("<Control-e>", self.quit)

        menubar.add_cascade(label="File", menu=filemenu)
        helpmenu = tk.Menu(menubar, tearoff=0)

        helpmenu.add_command(label="Help", command=self.helpFinder, accelerator="Ctrl+H")
        self.bind("<Control-h>", self.helpFinderEvent)

        helpmenu.add_command(label="About", command=self.aboutFinder, accelerator="Ctrl+A")
        self.bind("<Control-a>", self.aboutFinderEvent)

        menubar.add_cascade(label="Help", menu=helpmenu)
        self.config(menu=menubar)
        self.grid_columnconfigure(0,weight=1)

    def newselection(self, event):
        self.value_of_combo = self.box.get()
        print(self.value_of_combo)
        self.selectedCaseNum=self.cases[self.cases['name']==self.value_of_combo]['Case Num'].values[0]
        print self.selectedCaseNum
    def list(self):

        # nameList=list(self.cases['name'][np.logical_or(self.cases['Found lat'].isnull(),self.cases['Found lng'].isnull())].values)
        nameList=list(self.cases['name'][self.cases['Case Num'].isin(list(self.reports['Case Num'].values))])

        self.box_value = StringVar()
        self.box = ttk.Combobox(self.parent, textvariable=self.box_value, state='readonly')
        self.box.bind("<<ComboboxSelected>>", self.newselection)
        self.box['values'] = nameList
        self.box.set('Case Name')
        # self.box.current(0)
        self.box.grid(column=0, row=0)


if __name__ == "__main__":
    path = ""
    root = simpleGUI_tk(None)
    root.geometry('450x250')

    root.title('Missing Person Intelligence Synthesis Toolkit')

    obj = MILP.MILP(path=path, gridDim=1, theta=0.5)
    root.mainloop()



#Allow for input, run algorithm, if successful show message, output the result