## ffpyplayer player class
from ffpyplayer.player import MediaPlayer
import collections
import numpy as np
import time
import cv2
#import _thread
import re

## THREAD MESSAGING
q = collections.deque()
# Flags
TOGGLE_PLAY_PAUSE = 1
TOGGLE_MUTE = 2
SEEK_TO = 3
CHANGE_VOLUME = 4
EXIT = 5
START_PLAYBACK = 6

currTime = 0.0
startTime = 0.0

def togglePlayPause():
	q.append( ( TOGGLE_PLAY_PAUSE, None ) )

def seekToTime( seconds ):
	q.append( ( SEEK_TO, seconds+startTime ) )

def toggleMute():
	q.append( ( TOGGLE_MUTE, None ) )

def changeVolume( delta ):
	q.append( ( CHANGE_VOLUME, delta ) )

def exitPlayback():
	q.append( ( EXIT, None ) )

def startPlayback( filename, tstart ):
	q.append( ( START_PLAYBACK, filename ) )
	setStartTime( tstart )

def setStartTime( tstart ):
	global startTime
	startTime = float(re.sub("[^0-9.\-]","",tstart))

def updateCurrTime( time ):
	global currTime
	currTime = time - startTime

def getCurrTime():
	return currTime

## Player Settings
videoWindowTitle = 'Recce Video'
seek_tolerance = 0.15


def videoLoop():
	# wait for message to start 
	while True:
		if q:
			(action, data) = q.popleft()
			if action == START_PLAYBACK:
				togglePlayPause()	# start paused - this'll only get processed once ffplayer() starts
				ffplayer( data )
		time.sleep(0.1)


def ffplayer(filename):
	player = MediaPlayer(filename)
	prevVolume = 1
	val = ''
	while val != 'eof':
		frame, val = player.get_frame()
		#
		## Control Message Received
		if q:
			(action, data) = q.popleft()
			if action == TOGGLE_PLAY_PAUSE:
				player.toggle_pause()
			elif action == CHANGE_VOLUME:
				newVol = player.get_volume() + data
				newVolNormalised = max(0.0,min(newVol,1.0))
				player.set_volume(newVolNormalised)
			elif action == TOGGLE_MUTE:
				if player.get_volume() > 0:
					prevVolume = player.get_volume()
					player.set_volume(0)
				else:
					player.set_volume(prevVolume)
			elif action == SEEK_TO:	## SEEK TO FRAME; do this if not playing and skipping distance.
				player.seek(data,relative=False)
				# Update Frame; must recall get_frame multiple times until it updates, seems clunky but this seems to work
				for dummy in range(0,100):
					frame, val = player.get_frame(force_refresh=True)
					if frame is not None:
						if abs(frame[1] - data) < seek_tolerance:
							cvRefresh( frame, val )
							break
					time.sleep(0.005)	# must wait otherwise we'll get through the 100 calls before it updates
			elif action == EXIT:
				cv2.destroyAllWindows()
				del player
				return
		# Refresh the screen with the current video frame
		cvRefresh( frame, val )


def cvRefresh( frame, val ):
	# Snippet below found online, no clue if there's a more efficient way to do this
	if val != 'eof' and frame is not None:
		img, t = frame
		updateCurrTime(t)
		w = img.get_size()[0]
		h = img.get_size()[1]
		arr = np.uint8(np.asarray(list(img.to_bytearray()[0])).reshape(h,w,3)) # h - height of frame, w - width of frame, 3 - number of channels in frame
		cv2.imshow(videoWindowTitle, arr)
		# Below is required to show the image in window; not sure if there's a command which does the same without bothering to wait for a keypress or 
		# not sure if this'll hijack keys in my other window, seems not to?
		cv2.waitKey(1)

