import time
import collections
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

## Plotting Settings
annotateOffsetX = 3
annotateOffsetZ = -2

## SETUP FIGURE
fig = plt.figure()
plt.style.use('seaborn-whitegrid')
plt.grid(which='both')
# Title - could use stage name later?
fig.canvas.manager.set_window_title('Stage Pacenotes Trace')


## PLOT REDRAWING STUFF
def plotRedraw( plotData ):
	(trace, notesData) = plotData
	plt.gca().clear()
	# Map Trace
	plt.plot( trace[0] , trace[1] , zorder=10)
	# Pacenote Points
	( notesXZ, noteCalls ) = notesData
	plt.scatter( notesXZ[0] , notesXZ[1], color='r', zorder=20)
	# Pacenote Annotate
	for i,call in enumerate(noteCalls):
		plt.annotate( call, (notesXZ[0][i]+annotateOffsetX, notesXZ[1][i]+annotateOffsetZ) )		
	plt.xlim([-100,+100])
	plt.ylim([-100,+100])
	fig.canvas.draw_idle()


##### Threading Stuff #####
q = collections.deque(maxlen=1)
plotShown = False

# Called at end of main program such that main thread is the figure window
# Another thread called to do the main loop & curses window etc
def plotShow():
	global plotShown
	fig.canvas.draw_idle()
	plotShown = True
	plt.show()

def updatePlot( plotData ):
	q.append(plotData)		# Add to queue; will drop any older frames
	return

def plotRedrawQueueLoop():
	while plotShown == False:
		# wait till plot is shown to redraw first time
		time.sleep(0.001)
	while True:
		try:
			plotRedraw( q.popleft() )
		except IndexError:
			# No data in queue; wait for data.
			# Must include some sleep time or matplotlib window seems to hang
			# Not sure why as it should be in a separate thread, but whatever
			time.sleep(0.001)
			continue
# End