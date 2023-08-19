from H5Writer import H5Writer
from SEDSS.CLIMessage import CLIMessage
import sys
import zmq
import h5py
import time
from epics import PV
import log
GfullH5Path = None # Global(G) full h5 path

class ZMQWriter (H5Writer):
	def __init__(self, fName, fPath, configFile, wMode = "w"):
		super().__init__(fName, fPath, configFile, wMode)
		global GfullH5Path

		self.startTime = time.time()
		self.ZMQRType = zmq.SUB

		GfullH5Path = self.fPath+"/"+self.fName

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
			self.WriterRecivingTime = self.configFile["EPICSandIOCs"]["writerRecivingTime"]
			self.WriterOverallTime = self.configFile["EPICSandIOCs"]["writerOverallTime"]

		except:
			CLIMessage ("Problem reading the beamline configration file", "E")
			raise AttributeError
			sys.exit()

		if self.ZMQSType.lower() in ("pub", "publisher", "publish"):
			CLIMessage("ZMQ type is PUB (Publisher)", "I")
			self.ZMQSType = "PUB"
		elif self.ZMQSType.lower() in ("push", "pus"):
			self.ZMQSType = "PUSH"
			self.ZMQRType = zmq.PULL
		else:
			CLIMessage ("The value of the ZMQType in the beamline configration"\
				" is not defined","E")
			log.error("ZMQ (sender) type is not defined in the writer/beamline"\
				"configration file")
			sys.exit()

		log.info("Creating ZMQ context and socket")
		self.context = zmq.Context() #Create a zmq Context
		self.sock = self.context.socket(self.ZMQRType) # Create a socket

		if self.ZMQRType == zmq.SUB:
			self.sock.setsockopt_string(zmq.SUBSCRIBE, "")
			self.sock.bind(self.ZMQSender) # connect the created socket on the reciver to the sender
			log.info("Create ZMQ subscriber")
		elif self.ZMQRType == zmq.PULL: # to support Pull if needed in the future
			self.sock.bind(self.ZMQSender)

	def reciveData(self, numPointsX, numPointsY, scanTopo = "seq", arrayIndexX = None, arrayIndexY=None):

		self.numXPoints = numPointsX
		self.numYPoints = numPointsY
		self.arrayXIndex = arrayIndexX
		self.arrayYIndex = arrayIndexY
		self.scanTopo = scanTopo

		h5file = h5py.File(GfullH5Path, 'a')  # Reopen in append mode

		missedPoints = []
		totalPoints = 0
		if self.scanTopo.lower()[0:3] == "seq":
			for i in range(0,self.numXPoints):
				h5file["/exchange/xmap/data"].resize(i+1, axis=0)
				for j in range(0,self.numYPoints):
					totalPoints +=1
					data = self.sock.recv_pyobj()
					if data == "timeout":
						h5file["/exchange/xmap/data"].resize(j+1, axis=1)
						h5file["/exchange/xmap/data"][:, j, :] = 0
						missedPoints.append((i, j))
						log.error(f"missed point ({i, j})")
						CLIMessage(f"missed point ({i, j})", "W")
					elif data == "scanAborted":
						CLIMessage(f"scan has been aborted", "E")
						break;
					else:
						h5file["/exchange/xmap/data"].resize(j+1, axis=1)
						h5file["/exchange/xmap/data"][:, j, :] = data
						CLIMessage(f"Total Points: {self.numXPoints * self.numYPoints} | current index point: {i, j} | remaining points: {self.numXPoints * self.numYPoints - totalPoints}", "I")
						log.info(f"Total Points: {self.numXPoints * self.numYPoints} | current index point: {i, j} | remaining points: {self.numXPoints * self.numYPoints - totalPoints}")
			h5file.close()
			CLIMessage(f"total recieved points: {(i+1) * (j+1) - len(missedPoints)} | missed points index: {'No missed points' if len(missedPoints) == 0 else missedPoints}", "I")
			log.info(f"total recieved points: {(i+1) * (j+1) - len(missedPoints)} | missed points index: {'No missed points' if len(missedPoints) == 0 else missedPoints}")
		else:
			for i,k in enumerate(self.arrayXIndex):
				h5file["/exchange/xmap/data"].resize(i+1, axis=0)
				for j,l in enumerate(self.arrayYIndex):
					totalPoints +=1
					data = self.sock.recv_pyobj()
					if data == "timeout":
						h5file["/exchange/xmap/data"].resize(j+1, axis=1)
						h5file["/exchange/xmap/data"][:, l, :] = 0
						missedPoints.append((k, l))
						log.error(f"missed point ({k, l})")
						CLIMessage(f"missed point ({k, l})", "W")
					elif data == "scanAborted":
						CLIMessage(f"scan has been aborted", "E")
						break;
					else:
						h5file["/exchange/xmap/data"].resize(j+1, axis=1)
						h5file["/exchange/xmap/data"][:, l, :] = data
						CLIMessage(f"Total Points: {self.numXPoints * self.numYPoints} | current index point: {k, l} | remaining points: {self.numXPoints * self.numYPoints - totalPoints}", "I")
						log.info(f"Total Points: {self.numXPoints * self.numYPoints} | current index point: {k, l} | remaining points: {self.numXPoints * self.numYPoints - totalPoints}")
			h5file.close()
			CLIMessage(f"total recieved points: {(i+1) * (j+1) - len(missedPoints)} | missed points index: {'No missed points' if len(missedPoints) == 0 else missedPoints}", "I")
			log.info(f"total recieved points: {(i+1) * (j+1) - len(missedPoints)} | missed points index: {'No missed points' if len(missedPoints) == 0 else missedPoints}")
