### Pacenote Map Editor 220906 by EJC
#
# Copyright [2022] [Edward Clarke]
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
## Notes
# All written from scratch
# I've done some limited software engineering training, but mostly learnt python via simple scripting
# This is probably my largest python undertaking to date, so apologies if it's a mess
#
# As far as I'm aware I've not used any licensable materials
# Released as Open Source; I've very little clue of the legality requirements, but above I understand is open source, and is same as Dirty Pacenotes

## Organisation:
# All plotting functionality is built into _plots.py file
#	Hence should be feasible to change the plotting functions entirely to use something else if needed.
# All pacenote data structure and handling is in _pacenotes.py class
# All map trace data structure / loading / data processing in _trace.py class

import os
#import sys
#import time
import curses
import _thread

#custom imports stuff
import _plots		# all plotting stuff wrapped up in here
import _pacenotes	# pacenote data structure, loading/saving, moving etc
import _trace		# RDA map trace plot and coordinates / getting pacenote coords, rotating etc

## GLOBAL SETTINGS
NoteResolution = 10
# This sets how finely you can position pacenotes.
# Must be an integer; distances are rounded to int when imported
# Could go down to 1m increments, but probably overkill.
# Leaving this largeish should make for quicker moving stuff and less scrolling through blank areas
# 10 seems fair and probably easier to read / quicker to scan through


## SETUP CURSES
screen = curses.initscr()
curses.noecho()
curses.cbreak()
curses.start_color()
screen.keypad( 1 )
# Text Styles
curses.init_pair(1,curses.COLOR_WHITE, curses.COLOR_BLUE)
curses.init_pair(2,curses.COLOR_WHITE, curses.COLOR_RED)
highlightText = curses.color_pair( 1 )
editText = curses.color_pair( 2 )
normalText = curses.A_NORMAL
# Size Setup
linesHeader = 3	# top to be filled later with other stuff?=
linesBottom = 1	# bottom blank border
colsLeft = 2	# left border, includes markers to show movement
colsDist = 6	# distance column width
colsRight = 2	# right blank border

cwd = os.getcwd()

## PROGRAM OUTER INTERFACE
def MainLoop():
	dirPacenotes = 'pacenotes'
	FilePicker( os.path.join(cwd, dirPacenotes ), topLevel = True )
	# END OF EVERYTHING
	return

def FilePicker( path , topLevel = False ):
	dirs = [d for d in next(os.walk(path))[1]]
	files = [f for f in next(os.walk(path))[2]]
	#(rootdir, dirs, files) = os.walk(path)
	pacenoteFiles = [f for f in files if (('.txt' in f) and ('.bak.' not in f))]
	dirFileList = {v: k for v, k in enumerate( dirs + pacenoteFiles )}
	## EDIT LOOP
	selected = 0
	while True:
		## UPDATE CURSES SCREEN
		screen.erase()
		# Resize every time; as I'm flushing input buffer before getch, can't rely on catching screen resize key.
		curses.resize_term(*screen.getmaxyx())
		curses.curs_set( 0 )
		# Get current size & calculate lines for notes
		#colsMax = curses.COLS
		linesMax = curses.LINES
		linesNotes = linesMax-linesHeader-linesBottom
		## HEADER
		strHeader1 = path.replace(cwd,'')
		screen.addstr( 0, colsLeft, strHeader1, normalText )
		#
		## REDRAW FILE LIST
		for i in range( 0, linesNotes ):
			if i in dirFileList:
				if i == selected:
					lineFormat = highlightText
				else:
					lineFormat = normalText
				screen.addstr( i+linesHeader, colsLeft, dirFileList[i], lineFormat )
		screen.refresh()
		#
		# GET KEYPRESS
		curses.flushinp()	# flush input buffer to ignore keypresses while busy (so we don't keep scrolling after releasing keys)
		keyIn = screen.getch()
		#
		### PROCESS KEYPRESS ###
		## Navigation
		if keyIn == 27 or curses.keyname(keyIn).decode() == '^H':	# ESC or Backspace
			# go back up a level, but not if at top level.
			if not topLevel:
				return
		elif keyIn == curses.KEY_DOWN:
			selected = min( selected + 1, len(dirFileList)-1 )	
		elif keyIn == curses.KEY_UP:
			selected = max( selected - 1, 0 )
		elif curses.keyname(keyIn).decode() == '^J':	# enter key
			selName = dirFileList[selected]
			fullPath = os.path.join( path, selName )
			if os.path.isfile(fullPath):
				fullPathTrace = fullPath.replace('.txt','.csv')
				EditorLoop( fullPath, fullPathTrace )
			elif os.path.isdir(fullPath):
				FilePicker( fullPath )
# END


### MAIN EDITOR CURSES EXECUTION LOOP FUNCTIONS
def EditCall( pacenotes, editDist, lineCurr, colsMax ):
	editLine = lineCurr+linesHeader
	lineStartCol = colsLeft+colsDist+1
	strCalls = pacenotes.getNoteCalls( editDist )
	cursor = len(strCalls)	# start at end of text, seems more typical place to start editing text
	maxLen = colsMax-colsLeft-colsDist-colsRight-1
	while True:
		# Update line
		screen.move(editLine,lineStartCol)
		screen.clrtoeol()
		screen.addstr( editLine, lineStartCol, strCalls[:maxLen], editText)
		
		screen.move(editLine,lineStartCol+cursor)
		curses.curs_set( 1 )
		
		keyIn = screen.getch()
		if keyIn == 27:	# ESCAPE; go back without saving changes
			return
		# Cursor Left/Right
		elif keyIn == curses.KEY_LEFT:
			cursor = max(cursor-1,0)
		elif keyIn == curses.KEY_RIGHT:
			cursor = min(cursor+1,len(strCalls))
		# Skip to next/prev work; this is pretty basic; based on spaces, could be updated
		elif keyIn == curses.CTL_RIGHT:
			index = strCalls[cursor:].find(' ')
			if index > -1:
				cursor = min(cursor+index+1,len(strCalls))
		elif keyIn == curses.CTL_LEFT:
			index = strCalls[:cursor-1].rfind(' ')
			if index > -1:
				cursor = index+1
		elif keyIn == curses.KEY_HOME:
			cursor = 0
		elif keyIn == curses.KEY_END:
			cursor = len(strCalls)
		# Delete Stuff
		elif curses.keyname(keyIn).decode() == '^H':	#backspace
			if cursor > 0:
				cursor -= 1
				strCalls = strCalls[:cursor] + strCalls[cursor + 1:]
		elif keyIn == curses.KEY_DC:	#del
			strCalls = strCalls[:cursor] + strCalls[cursor + 1:]
		# Return & Save
		elif curses.keyname(keyIn).decode() == '^J':	# enter key
			pacenotes.changeCalls( editDist, strCalls )
			return
		# Text Entry
		elif curses.keyname(keyIn).decode() in pacenotes.permittedChars:
			letter = curses.keyname(keyIn).decode().lower()
			strCalls = strCalls[:cursor] + letter + strCalls[cursor:]
			cursor += 1

def EditorLoop( filePathNotes, filePathTrace ):
	## LOADING
	screen.erase()
	curses.resize_term(*screen.getmaxyx())
	curses.curs_set( 0 )
	# Load Pacenotes
	screen.addstr( 0, 1, 'Loading Pacenotes...', normalText)
	screen.refresh()
	pacenotes = _pacenotes.classPacenotes( filePathNotes, NoteResolution )
	# Load Map Trace
	screen.addstr( 1, 1, 'Loading Trace...', normalText)
	screen.refresh()
	trace = _trace.classTrace( filePathTrace, pacenotes.getNoteResolution() )
	# Load editor
	screen.addstr( 3, 1, 'Initialising plots and main editor...', normalText)
	screen.refresh()
	
	## EDIT LOOP
	statusText = 'LOADED'
	dist = 0	# start at zero distance
	while True:
		## UPDATE CURSES SCREEN
		screen.erase()
		# Resize every time; as I'm flushing input buffer before getch, can't rely on catching screen resize key.
		curses.resize_term(*screen.getmaxyx())
		curses.curs_set( 0 )
		# Get current size & calculate lines for notes
		colsMax = curses.COLS
		linesMax = curses.LINES
		linesNotes = linesMax-linesHeader-linesBottom
		lineCurr = int(0.75*linesNotes)
		#
		## HEADER
		strHeader1 = pacenotes.filename.replace(cwd,'')	
		screen.addstr( 0, colsLeft, strHeader1, normalText )
		screen.addstr( 1, colsLeft, statusText, editText )
		statusText = ''
		
		## REDRAW NOTES
		for i in range( linesHeader, linesHeader+linesNotes ):
			d = (dist + lineCurr*NoteResolution)-(i-linesHeader)*NoteResolution
			# blank lines before start / after finish
			if d < 0:
				continue
			if d > trace.getMaxDist():
				continue
			# line format highlight current distance
			if d == dist:
				lineFormat = highlightText
			else:
				lineFormat = normalText
			# Distance
			strLine = str(d).ljust(colsDist)
			# Append Note calls if note exists here
			iNote = pacenotes.getNote(d)
			if iNote is not None:
				maxLen = colsMax-colsLeft-colsDist-colsRight
				strLine += ('•'+str(iNote[pacenotes.CALLS]).ljust(maxLen))[:maxLen]
			#
			screen.addstr( i, colsLeft, strLine, lineFormat)
			# Add marker at start of line to help show scrolling
			if d%100 == 0:
				screen.addstr( i, 1, '|', normalText)
		screen.refresh()
		#
		## UPDATE PLOT
		_plots.updatePlot(  trace.plotData( dist, pacenotes.getNotes() )  )
		#
		# GET KEYPRESS
		# Flush input, other than if it's a key-resize, in which case process this
		# TODO maybe move this to a separate function, then I can detect any KEY_RESIZE during flushing, flush input and return this.
		# Otherwise flush input to nothing, then wait for another key then return this.
		# Manual key flushing; doesn't seem overly robust; leave as a problem for future
		#while True:
		#	screen.nodelay(1)
		#	keyIn = screen.getch()
		#	if keyIn == curses.KEY_RESIZE:
		#		curses.resize_term(*screen.getmaxyx())
		#		screen.clear()
		#		screen.refresh()
		#	elif keyIn == -1:
		#		break
		#screen.nodelay(0)
		curses.flushinp()	# flush input buffer to ignore keypresses while busy (so we don't keep scrolling after releasing keys)
		keyIn = screen.getch()
		#
		### PROCESS KEYPRESS ###
		## Navigation
		if keyIn == 27:
			statusText = 'Use F12 to exit, make sure to save first!'
		elif keyIn == curses.KEY_RESIZE or curses.keyname(keyIn).decode() == 'KEY_F(5)':
			pass
			# do nothing; just refresh screen
		elif keyIn == curses.KEY_DOWN:
			dist = max( dist - NoteResolution, 0 )
		elif keyIn == curses.KEY_UP:
			dist = min( dist + NoteResolution, trace.getMaxDist() )
		elif keyIn == curses.KEY_PPAGE:
			dist = pacenotes.getNextNoteDist(dist)
		elif keyIn == curses.KEY_NPAGE:
			dist = pacenotes.getPrevNoteDist(dist)
		elif keyIn == curses.KEY_HOME:
			dist = 0
		elif keyIn == curses.KEY_END:
			dist = trace.getMaxDist()
		#
		## Note Moving
		elif keyIn == curses.CTL_DOWN:
			dist = pacenotes.changeDist( dist, -NoteResolution )
			pacenotes.updateDistanceCalls()
		elif keyIn == curses.CTL_UP:
			if dist+NoteResolution <= trace.getMaxDist():
				dist = pacenotes.changeDist( dist, +NoteResolution )
				pacenotes.updateDistanceCalls()
		elif keyIn == curses.ALT_DOWN:
			dist = pacenotes.changeDistAllAfter( dist, -NoteResolution )
			pacenotes.updateDistanceCalls()
		elif keyIn == curses.ALT_UP:
			if pacenotes.getLastNoteDist()+NoteResolution <= trace.getMaxDist():
				dist = pacenotes.changeDistAllAfter( dist, +NoteResolution )
				pacenotes.updateDistanceCalls()
		#
		## Note Merging
		elif keyIn == curses.CTL_PGUP:
			# Merge note with next
			if pacenotes.noteExists(dist):
				dist = pacenotes.mergeNotes( dist, pacenotes.getNextNoteDist(dist) )
				pacenotes.updateDistanceCalls()
		elif keyIn == curses.CTL_PGDN:
			# Merge note with previous
			if pacenotes.noteExists(dist):
				dist = pacenotes.mergeNotes( dist, pacenotes.getPrevNoteDist(dist) )
		#
		## Note Insert/Delete
		elif keyIn == curses.KEY_IC:
			if not pacenotes.noteExists(dist):
				pacenotes.addNote(dist,'')
				pacenotes.updateDistanceCalls()
		elif keyIn == curses.KEY_DC:
			if pacenotes.noteExists(dist):
				pacenotes.deleteNote(dist)
				pacenotes.updateDistanceCalls()
		elif curses.keyname(keyIn).decode() in 'dD':	# d to add distance call
			if not pacenotes.noteExists(dist):
				pacenotes.addDistanceNote(dist)
				pacenotes.updateDistanceCalls()
		#
		## Add Distance Call; one key on 'd' or 'D'	
		# Enter or F2 = edit note
		elif (curses.keyname(keyIn).decode() == 'KEY_F(2)') or (curses.keyname(keyIn).decode() == '^J'): # ^J = enter key
			if pacenotes.isNote(dist):
				if not pacenotes.isDistanceNote(dist):
					EditCall( pacenotes, dist, lineCurr, colsMax )
			else:
				# Not currently a pacenote; add one here then edit it
				pacenotes.addNote(dist,'')
				EditCall( pacenotes, dist, lineCurr, colsMax )
		## FILE IO
		# F6 = save
		elif curses.keyname(keyIn).decode() == 'KEY_F(6)':
			if pacenotes.saveNotes():
				statusText = 'SAVED'
			else:
				statusText = 'NOT SAVED - UNKNOWN EXCEPTION - CHECK FILE PATH?'
		# F9 = load / restore
		elif curses.keyname(keyIn).decode() == 'KEY_F(9)':
			if pacenotes.loadNotes():
				statusText = 'LOADED'
			else:
				statusText = 'NOT LOADED - UNKNOWN EXCEPTION - CHECK FILE PATH?'
		# F12 = exit (no autosaving) (Don't use ESC, as ESC is used to abort editing call text)
		elif curses.keyname(keyIn).decode() == 'KEY_F(12)':
			return
#


### THREADING & EXECUTION STUFF
# Start another thread to handle curses window
_thread.start_new_thread(MainLoop,())	# need to include empty tuple for arguments

# Start another threat to process plot queue
_thread.start_new_thread(_plots.plotRedrawQueueLoop,())	# need to include empty tuple for arguments

# The original main thread used for the matplotlib GUI so it doesn't hang etc
# found this method here: https://stackoverflow.com/questions/34764535/why-cant-matplotlib-plot-in-a-different-thread
_plots.plotShow()

# TBC do these other threads get bundled up and nicely closed when I just close the main curses window?

#END
