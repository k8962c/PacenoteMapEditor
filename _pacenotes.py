# Pacenotes Class
import os
import csv
#import math
#import time
import datetime
import shutil
import string

class classPacenotes:
	CALLAT = 1
	PLAYED = 2
	CALLS = 3
	
	DISTANCE_CALL = '@'
	NOTE_RESOLUTION = 5
	permittedChars = string.ascii_letters + string.digits + '-_ ' # Permitted Chars in Call Strings (for EditLoop)
	
	def __init__(self, newFilename, newNoteRes ):
		self.filename = newFilename
		self.NOTE_RESOLUTION = int(newNoteRes)
		self.Notes = {}
		#
		# Setup
		self.loadNotes()
		self.updateDistanceCalls()
	
	def setNoteResolution(self, newNoteRes ):
		self.NOTE_RESOLUTION = int(newNoteRes)

	def getNoteResolution(self):
		return( self.NOTE_RESOLUTION )

# Get data
	def getNote(self,dist):
		if( dist in self.Notes ):
			return( self.Notes[dist].copy() )
		else:
			return None

	def getNotes(self):
		return self.Notes.copy()

	def getNoteCalls(self,dist):
		if( dist in self.Notes ):
			return( self.Notes[dist][self.CALLS] )
		else:
			return None

	def getNextNoteDist(self,currDist):
		for d in sorted(self.Notes.keys()):
			if d > currDist:
				return d
		return max(self.Notes.keys())

	def getPrevNoteDist(self,currDist):
		for d in sorted(self.Notes.keys(), reverse=True):
			if d < currDist:
				return d
		return min(self.Notes.keys())
	
	def getLastNoteDist(self):
		if len(self.Notes) > 0:
			return max(self.Notes.keys())
		else:
			return 0

# Note Manipulation
	def addNote(self, dist, strCalls):
		if self.noteExists(dist):
			return False
		else:
			newNote = {}
			newNote[self.CALLAT] = None 	# Integer distance when to call this note
			newNote[self.PLAYED] = False 	# Boolean Played Flag
			newNote[self.CALLS] = strCalls	# String of calls, space-separated
			# Add dictionary entry to notes dict
			self.Notes[dist]=newNote
			return True

	def addDistanceNote(self, dist):
		if self.noteExists(dist):
			return False
		else:
			self.addNote(dist, self.DISTANCE_CALL)
			return True

	def deleteNote(self, dist):
		del self.Notes[dist]

	def changeDist(self, dist, delta):
		newDist = dist + delta
		if dist not in self.Notes:
			return dist
		if newDist in self.Notes:
			return dist
		if newDist < 0:
			return dist
		# otherwise, change
		self.Notes[newDist] = self.Notes.pop(dist)
		return newDist

	def changeDistAllAfter(self, dist, delta):
		# if not on a note, ignore
		if dist not in self.Notes:
			return dist
		# if moving earlier, check if there's already one there which would clash
		if delta < 0 and (dist + delta) in self.Notes:
			return dist
		if delta < 0:
			sortOrderReverse = False
		else:
			sortOrderReverse = True
		#
		keyList = sorted(self.Notes.keys(), reverse=sortOrderReverse)
		for d in keyList:
			if d >= dist:
				self.changeDist(d,delta)
		return( dist+delta )

	def changeCalls(self, dist, strCallsNew):
		self.Notes[dist][self.CALLS] = strCallsNew

	def mergeNotes(self, currentDist, mergeDist):
		if not self.noteExists(currentDist) or not self.noteExists(mergeDist):
			return currentDist
		if self.isDistanceNote(currentDist) or self.isDistanceNote(mergeDist):
			return currentDist
		if currentDist == mergeDist:
			return currentDist
		#
		currentCalls = self.Notes[currentDist][self.CALLS]
		mergeCalls = self.Notes[mergeDist][self.CALLS]
		if currentDist > mergeDist:
			newCalls = mergeCalls + ' ' + currentCalls
		else:
			newCalls = currentCalls + ' ' + mergeCalls
		self.Notes[mergeDist][self.CALLS] = newCalls
		# delete the previous note; now merged
		self.deleteNote(currentDist)
		return mergeDist

# Queries
	def isNote(self,dist):
		return self.noteExists(dist)

	def noteExists(self, dist):
		if dist in self.Notes:
			return True
		else:
			return False

	def isDistanceNote(self, dist):
		if dist in self.Notes:
			if self.DISTANCE_CALL in self.Notes[dist][self.CALLS]:
				return True
		# otherwise, isn't a distance call.
		# must ensure we don't allow @ symbol in editor
		return False

# Data Processing
	def roundDist(self, strdistRaw, resolution = None ):
		if resolution is None:
			resolution = self.NOTE_RESOLUTION
		return int(round(float(strdistRaw)/resolution,0)*resolution)

	def updateDistanceCalls(self):
		# Loop through notes in order
		# When a distance call is found (@), get the distance to next note.
		# Pick a call based on strDistCall()
		# Update the note call, preserving the @ so it will auto-update if notes are shifted
		# Reader to strip the @ when playing; I expect I can just use this same class to process & export the sound file names
		keysList = sorted(self.Notes.keys())
		for index, dist in enumerate(keysList):
			if self.isDistanceNote(dist):
				if index+1 < len(keysList):	# if there is another note after this (i.e. this isn't last note in the list)
					nextDist = keysList[index+1]
					self.changeCalls( dist, self.DISTANCE_CALL + self.strDistCall( nextDist - dist ) )

	def strDistCall(self, rawDistance ):
		# Round call distances into something logical to avoid excessive sound files required
		# For distance shorter than 40, more usual to call 'into' or 'and', although I think some systems reverse these...
		tolerance = 10
		if rawDistance < 20:
			return 'into'
		elif rawDistance < 40:
			return 'and'
		elif rawDistance < 100:
			tolerance = 10
		elif rawDistance < 300:
			tolerance = 20
		elif rawDistance < 1000:
			tolerance = 50
		else:
			tolerance = 100
		return str(int(round(rawDistance/tolerance,0)*tolerance))

	def updateCallDistances(self):
		# Loop through all notes, calculating at what distance they should be called out.
		# copy from realtime notes function
		# TBC how to handle distance calls; with #300? then in the reader strip off the #?
		# or some other denoterl preferred to use # as comment; i.e. ignore any calls starting with #, ignore any line starting with #, ignore anything after ##
		# prefix distance calls with @, such that they auto-calculate; DirtyNotes update
		#
		# when updating notes, can auto-populate /replace @ with auto-distance.
		# Can still then manually write distance calls as 30
		#
		# Make these as separate calls; i.e. at the start of straight
		# can Mod DirtyPacenotes to optionally: add to end of previous call, or add to start of next call, or leave separate
		pass


# File I/O
	def loadNotes(self):
		try:
			self.Notes.clear()
			# Open file
			with open(self.filename) as csvfile:
				reader = csv.reader(csvfile)
				for line in reader:
					strShift = ''
					strOutOfOrder = ''
					strDist = line[0]
					strCalls = line[1].strip()
					noteDist = self.roundDist( strDist, self.NOTE_RESOLUTION )
					# if this distance value is less than previously added, shift to after
					if len(self.Notes) > 0:
						if noteDist < max(self.Notes.keys()):
							strOutOfOrder = '\t<!out of order, shifted after ' + str(max(self.Notes.keys())) + '>'
							noteDist = max(self.Notes.keys()) + self.NOTE_RESOLUTION
					# if 2 notes round to the same 5m increment, shift the 2nd note further down the road
					while noteDist in self.Notes:
						noteDist += self.NOTE_RESOLUTION
						strShift = '\t<!shifted later>'
					# Add the new note
					self.addNote( noteDist, strCalls )
					# Print note with warnings if relevant
					#print( strDist, str(noteDist), strCalls, strOutOfOrder, strShift )
					# TODO - Add better handling of import warnings; maybe list all warnings for review before going to editor view
			return True
		except:
			return False

	def saveNotes(self):
		try:
			# Backup existing notes file with timestamp before saving
			self.backupNotes()
			# Update automatic distance call calculations before saving
			self.updateDistanceCalls()
			## Write current data to file
			# Note the below line fails in python 2.7, but works in version3x.
			# Might have to tweak the newline thing also; this is done to avoid extra newlines being added.
			with open(self.filename, 'w', newline='') as csvfile:
				writer = csv.writer(csvfile)
				for dist in sorted(self.Notes.keys()):
					strCalls = self.Notes[dist][self.CALLS].strip()
					writer.writerow( [dist,strCalls] )
			return True
		except:
			return False

	def backupNotes(self):
		existingFile = self.filename
		modifiedTime = os.path.getmtime(existingFile)
		strSuffix = '.'+datetime.datetime.fromtimestamp(modifiedTime).strftime('%Y%m%d-%H%M')+'.bak.txt'
		backupFile = existingFile.replace('.txt',strSuffix)
		shutil.copy(existingFile, backupFile)
		#os.copy(existingFile, backupFile)
		#print(existingFile, backupFile) 
