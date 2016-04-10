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
class simpleGUI_tk(tk.Tk):

    def __init__(self,parent):

        tk.Tk.__init__(self,parent)

        self.parent = parent
        self.menu()
        self.value_of_combo = ''
        self.list()
        self.button = tk.Button(self.parent, text = "Output Map")


    def openFile(self):
        print("")
        #
    def Preprocess(self):
        obj.AtomRepDistDRT()

    def runFinderProgram(self):
        print("")
        cases= [21.0, 24.0, 42.0, 53.0, 68.0, 85.0, 107.0, 110.0, 112.0, 166.0, 177.0, 211.0, 218.0, 219.0, 231.0, 234.0, 239.0, 240.0,
        241.0, 248.0, 251.0, 253.0, 256.0, 258.0, 265.0, 274.0, 276.0,279.0,280.0,283.0,286.0,287.0]
        obj.Test(theta=.5,eps=0, wcc='WO', TrainSet=cases, Test=292.0)

    # def button(self):
        # print(os.getcwd())
        # f = open('map_240.0.html')
        # f.close()
        # webbrowser.open_new_tab('map_240.0.html')
        #call elham's code


    def drawOutput(self):
        try:
            dm.createTest(292)
        except:
            print 'Error in draw output::createTest'

        filename = os.getcwd()+'\\..\Output\\'+str(292)+'.html'
        #C:\Users\eshaaban\PycharmProjects\MISTUI\Output\292.html
        webbrowser.open_new_tab(filename)

    def aboutFinder(self):
        print("here is the explanation of what the finder does, add extra stuff")


    def helpFinder(self):
        window = tk.Toplevel(root)
        window.minsize(400,300);
        window.title("Help")
        helpMessage = "Instructions to run Finder: \n1. Select the case name to be analyzed\n" + "2. Press the 'Preprocess' button under the File tab." +\
                      "\n3. Press the 'Run' button under the 'Preprocess' tab\n" + \
                      "4. Under 'Draw', press 'Visualize Input' in order to see the inputs (reported locations) displayed on a map\n" +\
                      "5. Otherwise, press 'Search Area' to display the output onto the map after the input has been processed.\n"+\
                      "6. Lastly, 'Exit'quits out of the program\n\n" + "Shortcuts: \nPreprocess: CTRL + P\nRun: CTRL + R\nExit: CTRL + E\nVisualize Input: CTRL + I\nSearch Area: CTRL + A\n"
        msg = Message(window, text=helpMessage)
        msg.pack()




    def menu(self):
        menubar = tk.Menu()

        # create a pulldown menu, and add it to the menu bar
        filemenu = tk.Menu(menubar, tearoff=0)
        # filemenu.add_command(label="Open Test Case", command=self.openFile)
        filemenu.add_command(label='Preporcess', command=self.Preprocess)
        filemenu.add_command(label="Run", command=self.runFinderProgram)

        drawMenu = Menu(filemenu)
        drawMenu.add_command(label='Visualize Input')
        drawMenu.add_command(label='Search Area', command=self.drawOutput)
        filemenu.add_cascade(label="Draw", menu=drawMenu)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.quit)

        menubar.add_cascade(label="File", menu=filemenu)
        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Help", command=self.helpFinder)
        helpmenu.add_command(label="About", command=self.aboutFinder)
        menubar.add_cascade(label="Help", menu=helpmenu)

        # modelMenu = tk.Menu(menubar, tearoff = 0)
        # modelMenu.add_command(label="Create Model", command=self.createModel())
        # menubar.add_cascade(label="Create Model", menu=modelMenu)
        # analysisMenu = tk.Menu(menubar, tearoff = 0)
        # analysisMenu.add_command(label="Analyze Result", command=self.analyze())
        # menubar.add_cascade(label="Analyze Result", menu=analysisMenu)
        # display the menu
        self.config(menu=menubar)


        #label = tkinter.Label(self,anchor="w",fg="white",bg="blue")
        #label.grid(column=0,row=1,columnspan=2,sticky='EW')

        self.grid_columnconfigure(0,weight=1)

    def newselection(self, event):
        self.value_of_combo = self.box.get()
        print(self.value_of_combo)
    def list(self):
        # input=pd.read_csv('FinalCases_V13.csv', encoding='latin1',dtype={'Found lat':str})

        self.cases=pd.read_csv('../Data/FinalCases_V14.csv', encoding='latin1',dtype={'Found lat':str})
        nameList=list(self.cases['name'][np.logical_or(self.cases['Found lat'].isnull(),self.cases['Found lng'].isnull())].values)

        self.box_value = StringVar()
        self.box = ttk.Combobox(self.parent, textvariable=self.box_value, state='readonly')
        self.box.bind("<<ComboboxSelected>>", self.newselection)
        self.box['values'] = nameList
        self.box.set('Case Name')
        # self.box.current(0)
        self.box.grid(column=0, row=0)


if __name__ == "__main__":

    root = simpleGUI_tk(None)
    root.geometry('450x250')

    root.title('Missing Person Intelligence Synthesis Toolkit')
    obj = MILP.MILP('../Data/Beta.csv', '', gridDim=1)
    root.mainloop()



#Allow for input, run algorithm, if successful show message, output the result