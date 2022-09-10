### Map Trace Class & Data Processing
# EJC 220903

import csv
import math
#import time
import numpy as np
import _pacenotes

class classTrace:
	TRACE_RESOLUTION = 5	# resolution of the displayed road trace
	NOTE_RESOLUTION = None 	# resolution of note coordinate data (angle etc)
	CULL_AHEAD = 100		# plot size ahead/behind
	CULL_BEHIND = 20		# plot size ahead/behind

	def __init__(self, newFilename, noteResolution ):
		self.filename = newFilename
		self.NOTE_RESOLUTION = noteResolution
		# Setup Lists
		self.rawD = []
		self.rawX = []
		self.rawY = []
		self.rawZ = []
		self.rawT = []
		self.traceX = []
		self.traceZ = []
		self.traceDistCoords = {}
		self.Log = []
		#
		# Load raw file data
		self.loadRawTrace()
		# Generate simplified trace data for plotting purposes
		self.loadTrace()
		# Generate interpolated data (coords, angle, time) at each NoteResolution distance
		self.loadTraceNoteResolutionData()
		# END

	def getMaxDist(self):
		return( max(self.traceDistCoords.keys()) )

	def getDistFromTime(self, time):
		for d, v in sorted(self.traceDistCoords.items()):
			( X, Z, angle, T ) = v
			if T >= time:
				return d
		# if nothing found, just return last entry in list
		return max(self.traceDistCoords.keys())

	def getTimeFromDist(self, dist):
		( X, Z, angle, T ) = self.traceDistCoords[self.roundDist(dist, self.NOTE_RESOLUTION )]
		return T

	def roundDist(self, strdistRaw, resolution = None ):
		if resolution is None:
			resolution = self.TRACE_RESOLUTION
		return int(round(float(strdistRaw)/resolution,0)*resolution)

	def floorDist(self, strdistRaw, resolution = None ):
		if resolution is None:
			resolution = self.TRACE_RESOLUTION
		return int(math.floor(float(strdistRaw)/resolution)*resolution)

	def loadRawTrace(self):
		# Load raw data from file
		self.rawT.clear()
		self.rawD.clear()
		self.rawX.clear()
		self.rawY.clear()
		self.rawZ.clear()
		with open(self.filename) as csvfile:
			reader = csv.reader(csvfile)
			for line in reader:
				if line[2] == 'Distance(m)':
					continue 	# Ignore header row
				# otherwise add data to raw lists
				self.rawT.append(float(line[1]))
				self.rawD.append(float(line[2]))
				self.rawX.append(float(line[4]))
				self.rawY.append(float(line[5]))
				self.rawZ.append(float(line[6]))

	def loadTrace(self):
		# Loop through and extract cut down interpolated trace data based on TRACE_RESOLUTION
		self.traceX.clear()
		self.traceZ.clear()
		for dist in range(0, self.floorDist(max(self.rawD)), self.TRACE_RESOLUTION):
			interpX = np.interp(dist, self.rawD, self.rawX)
			interpZ = np.interp(dist, self.rawD, self.rawZ)
			self.traceX.append( interpX )
			self.traceZ.append( interpZ )

	def loadTraceNoteResolutionData(self):
		# Loop throught and extract coordinates and angle at required noteResolution
		self.traceDistCoords.clear()
		for dist in range(0, self.floorDist(max(self.rawD)), self.NOTE_RESOLUTION):
			interpT = np.interp(dist, self.rawD, self.rawT)
			interpX = np.interp(dist, self.rawD, self.rawX)
			#interpY = np.interp(dist, self.rawD, self.rawY)
			interpZ = np.interp(dist, self.rawD, self.rawZ)
			angle = 0
			if dist > 0:
				( prevX, prevZ, angle, prevT ) = self.traceDistCoords[dist-self.NOTE_RESOLUTION]
				angle = 0.5*math.pi - 1*math.atan2(interpZ - prevZ, interpX - prevX)
				if dist == self.NOTE_RESOLUTION:
					# If this is the 2nd point, then updated first point (at zero dist) to the same angle
					self.traceDistCoords[0] = ( prevX, prevZ, angle, prevT )
			#
			self.traceDistCoords[dist] = ( interpX, interpZ, angle, interpT )

	def plotData(self, curr_distance, Notes ):
		dataTrace = self.plotDataTrace( curr_distance )
		dataNotes = self.plotDataNotes( curr_distance, Notes )
		return( (dataTrace,dataNotes) )

	def plotDataTrace(self, curr_distance ):
		# Get current coordinate based on distance
		( X, Z, angle, T ) = self.traceDistCoords[curr_distance]
		#
		# Cull trace data infront and behind current distance
		distStart = max(min( self.traceDistCoords.keys() ), curr_distance-self.CULL_BEHIND )
		distEnd = min( max( self.traceDistCoords.keys() ), curr_distance+self.CULL_AHEAD )
		indexStart = round(distStart/self.TRACE_RESOLUTION)
		indexEnd = round(distEnd/self.TRACE_RESOLUTION)
		#get Culled X/Z
		#indexStart = 5
		#indexEnd = 10
		culledX = self.traceX[indexStart:indexEnd]
		culledZ = self.traceZ[indexStart:indexEnd]
		#
		# Shift the trace to align with current location
		centredTracePoints = [[val - X for val in culledX], [val - Z for val in culledZ] ]
		# Rotation Matrix
		R = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle),  np.cos(angle)]])
		# Rotate the trace so forwards is up
		rotatedTracePoints = R @ centredTracePoints
		#
		return rotatedTracePoints

	def plotDataNotes(self, curr_distance, Notes ):
		# Get current coordinate based on distance
		( X, Z, angle, T ) = self.traceDistCoords[curr_distance]
		#
		notePointsX = []
		notePointsZ = []
		noteCalls = []
		# Cull Distances
		distStart = round(curr_distance-self.CULL_BEHIND)
		distEnd = round(curr_distance+self.CULL_AHEAD)
		for dist,note in Notes.items():
			if distStart <= dist <= distEnd:
				( nX, nZ, nA, nT ) = self.traceDistCoords[dist]
				notePointsX.append( nX - X )
				notePointsZ.append( nZ - Z )
				noteCalls.append( note[_pacenotes.classPacenotes.CALLS] )
		# Shift the trace to align with current location
		centredNotePoints = [ notePointsX, notePointsZ ]
		# Rotation Matrix
		R = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle),  np.cos(angle)]])
		# Rotate the trace so forwards is up
		rotatedNotePoints = R @ centredNotePoints
		#
		return (rotatedNotePoints, noteCalls)
#
# def rotate(p, origin=(0, 0), angle=0):
# 	##angle = np.deg2rad(degrees)
# 	R = np.array([[np.cos(angle), -np.sin(angle)],[np.sin(angle),  np.cos(angle)]])
# 	o = np.atleast_2d(origin)
# 	p = np.atleast_2d(p)
# 	return np.squeeze((R @ (p.T-o.T) + o.T).T)
#