import sys
import zmq
import h5py
import time
import log
from epics import PV

from H5Writer import H5Writer
from SEDSS.CLIMessage import CLIMessage
GfullH5Path = None # Global(G) full h5 path

class ZMQWriter (H5Writer):
    def __init__(self, fName, fPath, configFile, wMode = "w"):
        super().__init__(fName, fPath, configFile, wMode)
        global GfullH5Path

        self.startTime = time.time()
        self.ZMQRType = zmq.SUB

        GfullH5Path = self.fPath+"/"+self.fName
        self.prefix = "XAFS:"
        self.PVs = self.configFile["writerPVs"]
        """
        Get ZMQ Sender settings from Beamline configration file
        Notes:
                1. ZMQSXXX: ZMQ Sender
                2. ZMQRXXX: ZMQ Reciever
        """
        try:
            self.ZMQSettings = self.configFile["ZMQSettings"]
            self.ZMQSType = self.ZMQSettings["ZMQSenderSettings"]["ZMQType"]
            self.ZMQSender = self.ZMQSettings["ZMQSenderSettings"]["ZMQSender"]
            self.ZMQSPort = self.ZMQSettings["ZMQSenderSettings"]["ZMQPort"]
            self.ZMQSProtocol = self.ZMQSettings["ZMQSenderSettings"]["ZMQProtocol"]
            # put saender in its format i.e. "tcp://127.0.0.1:1559"
            self.ZMQSender = self.ZMQSProtocol + "://" + self.ZMQSender + ":" + self.ZMQSPort

        except:
            CLIMessage ("Problem reading the beamline configration file", "E")
            raise AttributeError
            sys.exit()

        CLIMessage("ZMQ type is PUB (Publisher)", "I")
        log.info("Creating ZMQ context and socket")
        self.context = zmq.Context() #Create a zmq Context
        self.sock = self.context.socket(self.ZMQRType) # Create a socket
        self.sock.setsockopt_string(zmq.SUBSCRIBE, "")
        self.sock.bind(self.ZMQSender) # connect the created socket on the reciver to the sender
        log.info("Create ZMQ subscriber")

    def createDefaultDatasets(self, numPointsX, numPointsY):
        """
        This method is used to create datasets that are associated with the indexes and positions of points to
        be collected.
        i.e. IndexX, PositionY, ..
        """
        CLIMessage("Default datasets creation", "I")
        log.info("Start creating default datasets")
        defaultDatasets = self.configFile["defaultDatasets"]

        for dataset in defaultDatasets:

            # create datasets
            datasetOnH5 = self.h5File.create_dataset(defaultDatasets[dataset]["dataset"],
            dtype=defaultDatasets[dataset]["dtype"], shape=len(numPointsX) * len(numPointsY), chunks=True)      # create a 1 dimension dataset based on total scanning points

            # add attributes to the created dataset
            for att in defaultDatasets[dataset]["attributes"]:
                datasetOnH5.attrs[att]=defaultDatasets[dataset]["attributes"][att]

        log.info("Default datasets creation is done")

    def createRawDatasets(self, numPointsX, numPointsY):
        """
        This method is used to create datasets that are associated with the detector of points to
        be collected.
        i.e. Pixel, ..
        """
        CLIMessage("Raw datasets creation", "I")
        log.info("Start creating raw datasets")
        rawDatasets = self.configFile["rawDatasets"]

        dt = h5py.string_dtype(encoding='ascii')
        _dtype = dt # default if no dtype found

        for dataset in rawDatasets:
            if rawDatasets[dataset]["valueType"] == "EPICSPV":

                _data, _dataType = self.getPVValueType(rawDatasets[dataset]["value"])

                if _dataType in {"int","time_int", "ctrl_int", "short",
                "time_short","ctrl_short", "enum","time_enum", "ctrl_enum",
                 "long","time_long", "ctrl_long"}: # _AN: These data types need to be validated
                     _dtype = h5py.h5t.NATIVE_INT32
                elif _dataType in {"double", "time_double", "ctrl_double", "float",
                "time_float", "ctrl_float"}:
                    _dtype = "double"
                elif _dataType in {"char", "time_char", "ctrl_char", "time_string"}:
                    _dtype = dt

                # create datasets
                datasetOnH5 = self.h5File.create_dataset(rawDatasets[dataset]["dataset"],
                dtype=_dtype, shape=(len(numPointsY), len(numPointsX)), chunks=True)        # create a 2D dataset based on rows*cols >> y*x

                # add attributes to the created dataset
                for att in rawDatasets[dataset]["attributes"]:
                    datasetOnH5.attrs[att]=rawDatasets[dataset]["attributes"][att]

        log.info("Raw datasets creation is done")

    def receiveData(self, numPointsX, numPointsY, scanTopo = "seq", arrayIndexX = None, arrayIndexY=None):
        """
            Prepare the data sets to be ready to collect data points
        """
        self.numXPoints = len(numPointsX)
        self.numYPoints = len(numPointsY)
        self.arrayXPositions = numPointsX
        self.arrayYPositions = numPointsY
        self.arrayXIndex = arrayIndexX
        self.arrayYIndex = arrayIndexY
        self.scanTopo = scanTopo

        PV(self.prefix + self.PVs[self.PVs.index("TotalPoints")]).put(self.numXPoints * self.numYPoints, wait=True)
        CLIMessage(f"Ready to collect {self.numXPoints * self.numYPoints} points", "I")

        self.h5file = h5py.File(GfullH5Path, 'a')  # Reopen in append mode
        self.data 		= "/exchange/xmap/data"
        self.indexX 	= "/defaults/IndexX"
        self.indexY 	= "/defaults/IndexY"
        self.positionX 	= "/defaults/PositionX"
        self.positionY 	= "/defaults/PositionY"
        self.pixel      = "/exchange/xmap/pixel"

        self.h5file[self.data].resize(self.numXPoints, axis=1)      # resize X axis from 1 to X points
        self.h5file[self.data].resize(self.numYPoints, axis=0)      # resize Y axis from 1 to Y points

        self.missedPoints = []          # array to store missed points
        self.totalPoints = 0            # attr to store the points

        if self.scanTopo.lower()[0:3] == "seq":
            for y in range(0,self.numYPoints):
                for x in range(0,self.numXPoints):
                    self.writingData(x, y)
        else:
            for point in zip(self.arrayXIndex, self.arrayYIndex):
                x, y = point
                self.writingData(x, y)

        self.h5file.close()
        CLIMessage(f"total recieved points: {self.totalPoints - len(self.missedPoints)} out of {self.numXPoints * self.numYPoints} | "
                   f"missed points index: {'No missed points' if len(self.missedPoints) == 0 else self.missedPoints}", "I")
        log.info(f"total recieved points: {self.totalPoints - len(self.missedPoints)} out of {self.numXPoints * self.numYPoints} | "
                   f"missed points index: {'No missed points' if len(self.missedPoints) == 0 else self.missedPoints}")

    def writingData(self, x, y):
        """
            writing the recieved data in the datasets, if the data not recieved >> the value in the index dataset will be 0
        """
        self.totalPoints +=1            # increase the recieved points each time (for each point)
        data = self.sock.recv_pyobj()   # waiting until recieve any data (NO BLOCKING)
        if data == "timeout":
            self.h5file[self.data][y, x, :] = 0
            self.h5file[self.pixel][y,x] = 0
            self.missedPoints.append((x, y))
            PV(self.prefix + self.PVs[self.PVs.index("MissedPoints")]).put(len(self.missedPoints), wait=True)
            log.error(f"missed point index ({x, y})")
            CLIMessage(f"missed point index ({x, y})", "W")
        elif data == "scanAborted":
            CLIMessage(f"scan has been aborted >>> recieved points: {self.totalPoints - len(self.missedPoints)} out of {self.numXPoints * self.numYPoints}", "E")
            log.info(f"scan has been aborted >>> recieved points: {self.totalPoints - len(self.missedPoints)} out of {self.numXPoints * self.numYPoints}")
            self.h5File.close()
        else:
            PV(self.prefix + self.PVs[self.PVs.index("ReceivedPoints")]).put(self.totalPoints, wait=True)
            self.h5file[self.data][y, x, :] = data
            self.h5file[self.pixel][y,x] = PV(self.configFile["EPICSandIOCs"]["KETEKNetValue"]).get(timeout=self.PVTimeout, use_monitor=False)
            CLIMessage(f"Total Points: {self.numXPoints * self.numYPoints} | "
                        f"current point index: {x, y} | "
                        f"current point position: {self.arrayXPositions[x], self.arrayYPositions[y]} | "
                        f"collected points: {self.totalPoints} | "
                        f"missed points: {'0' if len(self.missedPoints) == 0 else self.missedPoints} | "
                        f"remaining points: {self.numXPoints * self.numYPoints - self.totalPoints}", "I")
            log.info(f"Total Points: {self.numXPoints * self.numYPoints} | "
                        f"current point index: {x, y} | "
                        f"current point position: {self.arrayXPositions[x], self.arrayYPositions[y]} | "
                        f"collected points: {self.totalPoints} | "
                        f"missed points: {'0' if len(self.missedPoints) == 0 else self.missedPoints} | "
                        f"remaining points: {self.numXPoints * self.numYPoints - self.totalPoints}")

        self.h5file[self.indexX][self.totalPoints-1] = x
        self.h5file[self.indexY][self.totalPoints-1] = y
        self.h5file[self.positionX][self.totalPoints-1] = self.arrayXPositions[x]
        self.h5file[self.positionY][self.totalPoints-1] = self.arrayYPositions[y]
