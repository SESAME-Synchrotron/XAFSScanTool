import pandas as pd
import numpy as np

from SEDSS.SEDFileManager import readFile
from scipy import stats
from SEDSS.CLIMessage import CLIMessage

class LINEARINTERVALS:
	def __init__(self, cfg):
		self.limits = readFile("configurations/limits.json").readJSON()
		self.cfg = cfg
		self.numIntervals = cfg["NIntervals"]

	def getIntervals(self):
		# ui: user interval
		# li: predefined linear interval
		self.intervals = []
		for ui in range(self.numIntervals):
			self.subInterval = {}
			uiStart = float(self.cfg['Intervals'][ui]['Startpoint'])
			uiEnd = float(self.cfg['Intervals'][ui]['Endpoint'])
			uiStepSize = float(self.cfg['Intervals'][ui]['Stepsize'])
			CLIMessage('Get linear segment(s) for interval number {} that covers the range ({},{}):'.format(ui, uiStart, uiEnd), 'I')
			self.linearSegmentsDF = self.findOptimalSegments(uiStart, uiEnd, uiStepSize)
			self.linearIntervalsIndex = []
			self.LinearIntervalValue = []
			self.linearIntervalsSpeed = []
			for i_index, i in self.linearSegmentsDF.iterrows():
				liStart = float(i['start'])
				liEnd = float(i['end'])
				if uiStart >= liStart and liEnd > uiStart:
					self.linearIntervalsIndex.append(i_index)
					speed = self.calcMonoThetaSpeed(ui, i_index)
					self.linearIntervalsSpeed.append(speed)
					self.LinearIntervalValue.append([uiStart, uiEnd if uiEnd <= liEnd else liEnd])
					if uiEnd <= liEnd:
						break
					else:
						for j_index, j in self.linearSegmentsDF.iloc[i_index+1:].iterrows():
							liEnd = j['end']
							if liEnd >= uiEnd:
								self.linearIntervalsIndex.append(j_index)
								speed = self.calcMonoThetaSpeed(ui, j_index)
								self.linearIntervalsSpeed.append(speed)
								self.LinearIntervalValue.append([j['start'], uiEnd])
								break
							else:
								self.linearIntervalsIndex.append(j_index)
								speed = self.calcMonoThetaSpeed(ui, j_index)
								self.linearIntervalsSpeed.append(speed)
								self.LinearIntervalValue.append([j['start'], j['end']])

			self.subInterval['userInterval(ui)'] = ui
			self.subInterval['uiStart'] = uiStart
			self.subInterval['uiEnd'] = uiEnd
			self.subInterval['linearIntervalsIndex'] = self.linearIntervalsIndex
			self.subInterval['linearIntervalValue'] = self.LinearIntervalValue
			self.subInterval['linearIntervalsSpeed'] = self.linearIntervalsSpeed
			self.intervals.append(self.subInterval)
		return self.intervals

	def calcMonoThetaSpeed(self, ui, li):
		engStepSize = float(self.cfg['Intervals'][ui]['Stepsize'])
		liStartPoint = float(self.linearSegmentsDF.iloc[li]['start'])
		thetaStepSize = abs(self.getThetaPosition(liStartPoint) - self.getThetaPosition(liStartPoint + engStepSize))
		stepMovementTime = self.getStepMovementTime(ui)
		speed = thetaStepSize/stepMovementTime
		return speed

	def getStepMovementTime(self, ui):
		detectors = self.cfg['detectors']
		IC_KETEK_ExpTime = float(self.cfg['Intervals'][ui]['IcsIntTime'])
		FICUS_ExpTime = float(self.cfg['Intervals'][ui]['DetIntTime'])
		ICDataFrameTime = KETEKDataFrameTime = FICUSDataFrameTime = 0
		FicusReadOutTime = float(self.limits['FicusReadOutTime'])
		KetekReadoutAvrageTime = float(self.limits['KetekReadoutAvrageTime'])
		ICsLatency = float(self.limits['ICsLatency'])
		KetekLatency = float(self.limits['KetekLatency'])
		FicusLatency = float(self.limits['FicusLatency'])
		MonoLatency = float(self.limits['MonoLatency'])
		ICsReadoutAvrageTime = float(self.limits['ICsReadoutAvrageTime'])
		ICDataFrameTime = IC_KETEK_ExpTime + ICsReadoutAvrageTime + MonoLatency + ICsLatency
		if 'KETEK' in detectors:
			KETEKDataFrameTime = IC_KETEK_ExpTime + KetekReadoutAvrageTime + MonoLatency + KetekLatency
		if 'FICUS' in detectors:
			FICUSDataFrameTime = FICUS_ExpTime + FicusReadOutTime + MonoLatency + FicusLatency
		return max(ICDataFrameTime, KETEKDataFrameTime, FICUSDataFrameTime)

	def getThetaPosition(self, energy):
		P = 1.9770410767
		theta = np.degrees(np.arcsin(P / energy))
		return theta

	def printIntervals(self):
		print("Intervals Summary:\n")
		print("{:<20} {:<15} {:<15} {:<25} {:<30} {:<15}".format(
			"UI", "UI Start", "UI End", "LI Index", "LI Values", "Speed"))
		print("="*120)
		for interval in self.intervals:
			ui = interval['userInterval(ui)']
			ui_start = interval['uiStart']
			ui_end = interval['uiEnd']
			linearIntervalsIndex = interval['linearIntervalsIndex']
			linear_interval_values = interval['linearIntervalValue']
			speed = interval['linearIntervalsSpeed']

			linear_intervals_str = ', '.join(map(str, linearIntervalsIndex))
			linear_values_str = ', '.join([f"[{v[0]}, {v[1]}]" for v in linear_interval_values])
			speed_str = ', '.join(map(str, speed))

			print("{:<20} {:<15} {:<15} {:<25} {:<30} {:<15}".format(
				ui, ui_start, ui_end, linear_intervals_str, linear_values_str, speed_str
			))

	def findOptimalSegments(self, engStart, engStop, engStepSize):
		points = np.arange(engStart, engStop, engStepSize)
		df = pd.DataFrame(points, columns=['Points'])
		df['Energy'] = pd.to_numeric(df['Points'])
		# J = 20
		P = 1.977041077
		df["Theta"] = np.degrees(np.arcsin(P / df['Energy']))

		max_error = self.limits['linearFittingMaxErrorMargin']
		segments = []
		start_idx = 0
		while start_idx < len(df):
			end_idx = start_idx + 1
			while end_idx < len(df):
				segment_df = df.iloc[start_idx:end_idx+1]
				slope, intercept, _, _, _ = stats.linregress(segment_df['Energy'], segment_df['Theta'])
				predicted_theta = slope * segment_df['Energy'] + intercept
				max_deviation = np.abs(predicted_theta - segment_df['Theta']).max()
				if max_deviation > max_error:
					end_idx -= 1
					break
				end_idx += 1
			segment_df = df.iloc[start_idx:end_idx+1]
			slope, intercept, _, _, _ = stats.linregress(segment_df['Energy'], segment_df['Theta'])
			segments.append((slope, intercept, segment_df['Energy'].iloc[0], segment_df['Energy'].iloc[-1]))
			start_idx = end_idx

		for i, (_,_,start, end) in enumerate(segments):
			print(f"Segment {i+1:>2}: Start = {start:>8.4f}, End = {end:>8.4f}")
		segmentsDF = pd.DataFrame(segments, columns=['slope', 'intercept', 'start', 'end'])

		return segmentsDF

# optimal_segments = find_optimal_segments(df, max_error=limits['linearFittingMaxErrorMargin'])