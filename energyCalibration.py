import math
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
from matplotlib.widgets import Button, TextBox
import epics
from SEDSS.SEDSupplements import CLIMessage, UIMessage

class energyCalibration:
    
    def __init__(self,xdiPath):

        ''' The main purpose of this class is to compute the new offset, by extracting the energy vs. imutrans for xdi file, then these data are processed '''
        self.offsetPV = "D08R1-MO-MC2:OH-DCM-STP-ROTX1.OFF"
        self.xdiPath = xdiPath
        self.energyReal = epics.PV("XAFS:ENGCAL:RealFoilEleEng").get() /1000   # Divide by 1000, keV >> eV.
        self.crystal = epics.PV("XAFS:DCMSetup:Crystal").get()
        self.oldOffset = epics.PV(self.offsetPV).get()
        self.PI = math.pi

        self.extractImutrans()

    def extractImutrans(self):
        # Extracting the data (energy vs. imutrans) 
        try:
            f=open(self.xdiPath,"r")
            lines=list(f.readlines())
            self.energy = []
            self.ImutransData = [] 

            for l in lines:
                if not l.startswith('#'):                                # exclude the lines start with (#)
                    self.energy.append(float(l.split('  ')[0]))          # extract the energy column by index 0, column 1
                    self.ImutransData.append(float(l.split('  ')[5]))    # extract the imutrans by index 4, column 5

            f.close()

        except:
            CLIMessage(f"Unable to open or handle xdi file >>> {self.xdiPath}", "E")
        
        self.plottingAnalysis()

    def plottingAnalysis(self):
        # this method to implement the main process functions, which are commented below

        # Normalization 
        self.normalization = (self.ImutransData - np.min(self.ImutransData)) / np.ptp(self.ImutransData)

        # Smoothing
        self.smoothing = savgol_filter(self.normalization, 5, 3)

        # 1st Derivative
        self.firstDerivative = np.gradient(self.normalization)

        # 2nd Derivative 
        self.secondDerivative = np.gradient(self.firstDerivative)
        
        self.plotting()
        self.findPeaks()

    def findPeaks(self):
        # Extracting the maximum peaks 

        self.peaksMax = []
        # self.peaksMin = []

        for max in range(1,len(self.firstDerivative)-1):    # exract the index of the peaks
            if (self.firstDerivative[max] > self.firstDerivative[max-1] and self.firstDerivative[max] > self.firstDerivative[max+1]):
                self.peaksMax.append(max)

        # for min in range(1,len(self.firstDerivative)-1):
        #     if (self.firstDerivative[min] < self.firstDerivative[min-1] and self.firstDerivative[min] < self.firstDerivative[min+1]):
        #         self.peaksMin.append(min)
        
        self.maxPeaksXaxis = [self.energy[index] for index in self.peaksMax]            # append the x-axis values of peaks by index (energy)
        self.maxPeaksYaxis = [self.firstDerivative[index] for index in self.peaksMax]   # append the y-axis values of peaks by index (imutrans)

        # self.minPeaksXaxis = [self.energy[index] for index in self.peaksMin]
        # self.minPeaksYaxis = [self.firstDerivative[index] for index in self.peaksMin]

        self.peaksPlotting()
    
    def plotting(self):
        # plot the functions from plottingAnalysis
        plt.close()
        plt.subplots_adjust(left=0.1,
                    bottom=0.1, 
                    right=0.9, 
                    top=0.9, 
                    wspace=0.4, 
                    hspace=0.4)
        
        # plt.subplot(2,2,1)
        # plt.plot(self.energy,self.ImutransData)
        # plt.title("Original Data", fontsize = 12)
        # plt.grid(color = 'green', linestyle = '--', linewidth = 0.5)

        plt.subplot(2,2,4)
        plt.plot(self.energy,self.normalization, color = 'blue',label = "Normlization")
        plt.plot(self.energy,self.smoothing, color = 'red',label = "Smoothing")
        plt.plot(self.energy,self.firstDerivative,color = 'black',linewidth = 2,label = "1st derivative")
        plt.plot(self.energy,self.secondDerivative,color = 'green',linewidth = 2,label = "2nd derivative")
        plt.legend(loc="upper right")
        plt.grid(color = 'green', linestyle = '--', linewidth = 0.5)

        plt.subplot(2,2,1)
        plt.plot(self.energy,self.normalization)
        plt.title("Normalized Data", fontsize = 12)
        plt.grid(color = 'green', linestyle = '--', linewidth = 0.5)

        plt.subplot(2,2,2)
        plt.plot(self.energy,self.smoothing)
        plt.title("Smoothed Data", fontsize = 12)
        plt.grid(color = 'green', linestyle = '--', linewidth = 0.5)

        plt.subplot(2,2,3)
        plt.plot(self.energy,self.firstDerivative)
        plt.title("1st Derivative", fontsize = 12)
        plt.grid(color = 'green', linestyle = '--', linewidth = 0.5)
        
        # plt.subplot(2,3,6)
        # plt.plot(self.energy,self.secondDerivative)
        # plt.title("2nd Derivative", fontsize = 12)
        # plt.grid(color = 'green', linestyle = '--', linewidth = 0.5)

    def peaksPlotting(self):
        
        self.fig, self.ax = plt.subplots()  # new subplot for peaks
        self.fig.subplots_adjust(bottom=0.2) # or whatever
    
        self.ax.plot(self.energy,self.firstDerivative,color = 'black', picker=True)          # plot the main data
        self.ax.plot(self.maxPeaksXaxis,self.maxPeaksYaxis, 'bo',picker=True, pickradius=5)  # plot the pickers points which are peaks (picker=True)
        
        plt.grid(color = 'black', linestyle = '--', linewidth = 0.75)

        for x,y in zip(self.maxPeaksXaxis,self.maxPeaksYaxis):      # annotate the points for each peak 

            self.label = "{:.4f}".format(x)
            plt.annotate(self.label,                 # this is the text
                        (x,y),                       # these are the coordinates to position the label
                        textcoords="offset points",  # how to position the text
                        xytext=(0,10),               # distance from text to points (x,y)
                        ha='center',                 # horizontal alignment can be left, right or center
                        rotation = 90)               # rotate the labels to be in vertical mode   

        plt.title("1st Derivative", fontsize = 20)
        plt.xlabel("Energy", fontsize = 13)
        plt.ylabel("Imutrans", fontsize = 13)

        # ax.plot(self.minPeaksXaxis,self.minPeaksYaxis, 'bo',picker=True, pickradius=5)
        
        WLgraphBox = self.fig.add_axes([0.25, 0.07, 0.1, 0.055])        # set the dimensions of the window length field
        windowLength = TextBox(WLgraphBox, "Window Length: ")           # set a name for the window length field
        windowLength.on_submit(self.getWindowLength)                    # callback function 

        POgraphBox = self.fig.add_axes([0.25, 0.01, 0.1, 0.055])        # set the dimensions of the poly order field  
        polyOrder = TextBox(POgraphBox, "Polynomial Order: ")           # set a name for the poly order field
        polyOrder.on_submit(self.getPolyOrder)                          # callback function

        self.axes = plt.axes([0.9, 0.005, 0.09, 0.075])     # set the dimensions of the button
        self.button = Button(self.axes, 'Confirm')          # set a name for the button
        self.button.on_clicked(self.buttonOnClick)          # callback function 

        self.energyPeak = None                              # peak value
        self.fig.canvas.mpl_connect('pick_event', self.getPeaks) # callback function
        
        plt.show()
   
    def getPeaks(self,event):

        self.thisline = event.artist                  # artist: generate the pick event  
        self.xdata = self.thisline.get_xdata()
        self.ind = event.ind                          
        self.energyPeak = float(self.xdata[self.ind])
        CLIMessage(f"Current chosen Peak: {self.energyPeak}", "I")

    def buttonOnClick(self,val):
        
        if self.energyPeak != None:
            plt.close("all")
        
            if str(self.crystal) == "Si 111":
                self.constantSI111 = 1.9770410767
                self.calcOffset(str(self.crystal),self.constantSI111)
            
            if str(self.crystal) == "Si 311":
                self.constantSI311 = 3.7860083059
                self.calcOffset(str(self.crystal),self.constantSI311)

        else:
            CLIMessage("No value chosen, please select a value to continue", "E")

    def calcOffset(self,crystal,SI):

        self.crystalType = crystal
        self.constantSI = SI

        self.thetaReal = math.asin(self.constantSI / self.energyReal) * (180 / self.PI)
        self.thetaExp  = math.asin(self.constantSI / self.energyPeak) * (180 / self.PI)

        self.newOffset = self.oldOffset + (self.thetaReal - self.thetaExp)
        
        CLIMessage(f"Crystal setup: {self.crystalType}", "I")
        CLIMessage(f"The old offset is: {self.oldOffset}", "W")
        CLIMessage(f"The new offset is: {self.newOffset}", "I")

        epics.PV(self.offsetPV).put(self.newOffset)       

    def getWindowLength(self, windowLength = "5"):
        # return the input value of window length

        self.windowLength = int(windowLength)
        self.visualizeGraph()

    def getPolyOrder(self, polyOrder = "3"):
        # return the input value of poly order

        self.polyOrder = int(polyOrder)
        self.visualizeGraph()

    def visualizeGraph(self):
        """ the purpose of this method is to re-plot the 1st derivative after changing the savgol filter parameters """
        try:
            """ the conditions below related to default plotting, by default >> the plotting will be without smoothing, 
                if there any value was entered, the plotting will be with smoothing, to return to 1st conditions >> the fileds must be zeros not NONE!!! """
                
            if (self.windowLength > self.polyOrder):                                                    
                self.smoothing = savgol_filter(self.normalization,self.windowLength, self.polyOrder)
                self.firstDerivative = np.gradient(self.smoothing)

            elif (self.windowLength == 0 and self.polyOrder == 0):
                self.firstDerivative = np.gradient(self.normalization)

            else:
                UIMessage("Invalid Values", "Check the values","window length must be greater than poly order!").showWarning()
            
            self.peaksMax = []

            for max in range(1,len(self.firstDerivative)-1):    # exract the index of the peaks
                if (self.firstDerivative[max] > self.firstDerivative[max-1] and self.firstDerivative[max] > self.firstDerivative[max+1]):
                    self.peaksMax.append(max)

            self.maxPeaksXaxis = [self.energy[index] for index in self.peaksMax]            # append the x-axis values of peaks by index (energy)
            self.maxPeaksYaxis = [self.firstDerivative[index] for index in self.peaksMax]   # append the y-axis values of peaks by index (imutrans)

        except:
            pass
        
        self.ax.cla()       # clear old graph
        
        self.ax.grid(color = 'black', linestyle = '--', linewidth = 0.75)

        for x,y in zip(self.maxPeaksXaxis,self.maxPeaksYaxis):      # annotate the points for each peak 

            self.label = "{:.4f}".format(x)
            self.ax.annotate(self.label,             # this is the text
                        (x,y),                       # these are the coordinates to position the label
                        textcoords="offset points",  # how to position the text
                        xytext=(0,10),               # distance from text to points (x,y)
                        ha='center',                 # horizontal alignment can be left, right or center
                        rotation = 90)               #
        
        self.ax.plot(self.energy,self.firstDerivative,color = 'black', picker=True)          # plot the main data
        self.ax.plot(self.maxPeaksXaxis,self.maxPeaksYaxis, 'bo',picker=True, pickradius=5)  # plot the pickers points which are peaks (picker=True)
        
        self.ax.set_title("1st Derivative", fontsize = 20)
        self.ax.set_xlabel("Energy", fontsize = 13)
        self.ax.set_ylabel("Imutrans", fontsize = 13)
        
        plt.draw()    # draw the new plot

# x= energyCalibration("test.txt")
