
### SETUP:
For a given stage pacenote file (.txt)
Make another file with identical name but with (.inf) extension
In the inf file, enter:
- Filenames for the RDA trace csv
- Corresponding recce screen recording video file
- 'starttime', which is the time in the video when the stage starts (at "Go!")
Sorry this is a bit manual, but seemed the easiest way to make it more robust and you can keep track of different recce runs.

example files:
El Rodeo.txt
El Rodeo.inf
El Rodeo 2022-08-30.csv		RDA trace
El Rodeo 2022-08-30.mkv		Screen Recording of the recce

Example contents of El Rodeo.inf:
trace=El Rodeo 2022-08-30.csv
video=El Rodeo 2022-08-30.mkv
videostart=38


### Features:
	Use Racetrack Data Aquisition mod to record a .csv map trace of a stage.

	The .EXE is VERY SLOW to open up.
		(This if the first .exe I've made from python, so no clue why this is so slow)
		If you want speed, just use the raw python, there aren't too many non-standard libraries required.
		Note I'm using "windows-curses" package for a windows curses implementation (https://github.com/zephyrproject-rtos/windows-curses)
			Should be installable using pip install windows-curses

	When loading a pacenote file:
		It rounds off distance to 10m.
		If there are 2 closely spaced notes, it will push the 2nd note 10m after the first. Generally shouldn't be an issue.
		If there are notes out of sequence it'll assume this is an error, and will shift the next note 10m after the last one loaded.
		Currently NO WARNINGS printed about any of the above auto-changes. (on the to do list)

	When saving, it will first copy the old file to a backup file with modified date string in filename.

### Known Bugs:
	It will Crash/Hang if you :
		Open a stage where the pacenotes file has a call after the end of the stage.
		Open a stage without a corresponding .csv map trace (from Racetrack Data Aquisition mod).
	TBC what happens if you open a stage without a corresponding video file recording, probably will crash, but this makes it so much better to use.

### Thanks to:
	Palo Samo for creating DiRTy Pacenotes and giving inspiration for doing this
	strawhatboy & ZTMZClub Pacenote Tool contributors for pacenote files of the original game to work with
	bn880 for RaceTrack Data Acquisition (RDA) which this is intended to work with



##### PLAYBACK KEYS #####
SPACE				Play/Pause Video
m					Mute
+/-					Volume up/down


##### EDITOR KEYS #####
Up/Down Cursors		Move forward backwards through stage, 10m at a time.
PageUp/Down			Jump to the next/previous pacenote
Home/End			Jump to start/end of stage

F2 or ENTER			Edit the calls for a note. If no note existing, it'll add one and then edit.
INS					Insert blank note
DEL					Delete note


CTRL + Up/Down		Shift a pacenote forward/backwards, 10m at a time.
ALT + Up/Down		Shift this pacenote and ALL FOLLOWING pacenotes in the stage foward/back, 10m at a time.

CTRL + PageUp/Down	Merge the current note into the next/previous.
					i.e. deletes the currently selected note and shifts the calls into the next/previous.

d					Add a distance call: this will automatically calcuate the distance from this note to the next note.
					i.e. if you add this at the end of a corner, it'll calculate the distance to the next note
					Saved in the pacenote file as e.g. @50.
					I'll need to hack Dirty Pacenotes to strip off any @ symbols before calling, or you can just remove in a text editor when finished.
					My intent though is to in future hack Dirty Pacenotes such that when it loads the notes, it'll:
						Merge the distance call either on the end of the previous note, or at start of next note, based on user preference.

					The auto-calculation will use 'into' if close (less than 20m), or 'and' if up to 40m.
					Rounds off distance call to reduce number of sounds which'll be required:
						Rounding: 10m below 100m, 20m below 300m, then 50m up to 500m, then to 100m above 500m.

F5					Redraw screen in case of curses messup
F6					SAVE
F9					LOAD (will wipe any changes made)
F12					QUIT (won't save before quitting)
