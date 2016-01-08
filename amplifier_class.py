import os
import sys
import string
import time,datetime
import re
import ConfigParser
from log_class import Log

# System files
ConfigFile = "/etc/amplifier4.conf"
AmplifierLibDir = "/var/lib/amplifier"
CurrentStationFile = AmplifierLibDir + "/current_station"
CurrentTrackFile = AmplifierLibDir + "/current_track"
VolumeFile = AmplifierLibDir + "/volume"
ChannelFile = AmplifierLibDir + "/channel"
TimerFile = AmplifierLibDir + "/timer" 
AlarmFile = AmplifierLibDir + "/alarm" 
StreamFile = AmplifierLibDir + "/streaming"
BoardRevisionFile = AmplifierLibDir + "/boardrevision"

log = Log()
config = ConfigParser.ConfigParser()


class Amplifier:

# Input source
	RADIO = 0
	CDPLAYER = 1
	MP3 = 2
		
	
# Display Modes
	MODE_TIME = 0
	MODE_SEARCH  = 1
	MODE_SOURCE  = 2
	MODE_OPTIONS  = 3
	MODE_RSS  = 4
	MODE_IP  = 5
	MODE_LAST = MODE_IP	# Last one a user can select
	MODE_SLEEP = 6		# Sleep after timer or waiting for alarm
	MODE_SHUTDOWN = -1

# Alarm definitions
	ALARM_OFF = 0
	ALARM_ON = 1
	ALARM_REPEAT = 2
	ALARM_WEEKDAYS = 3
	ALARM_LAST = ALARM_WEEKDAYS
	
	# Other definitions
	UP = 0
	DOWN = 1
	ONEDAYSECS = 86400	# Day in seconds
	ONEDAYMINS = 1440	# Day in minutes

	boardrevision = 2 # Raspberry board version type
	mpdport = 6600  # MPD port number
	volume = 20	# Volume level 0 - 100%
	pause = False   # Is radio state "pause"
	playlist = []	# Play list (tracks or radio stations)
	current_id = 1	# Currently playing track or station
	source = RADIO	# Source RADIO or Player
	reload = False	# Reload radio stations or player playlists
	option = ''     # Any option you wish
	artist = ""	# Artist (Search routines)
	error = False 	# Stream error handling
	errorStr = ""   # Error string
	switch = 0	# Switch just pressed
	updateLib = False    # Reload radio stations or player
	numevents = 0	     # Number of events recieved for a rotary switch
	volumeChange = False	# Volume change flag (external clients)

	display_mode = MODE_TIME	# Display mode
	display_artist = False		# Display artist (or tracck) flag
	current_file = ""  		# Currently playing track or station
	option_changed = False		# Option changed
	channelChanged = True		# Used to display title
	configOK = False		# Do we have a configuration file
	
	
	# Clock and timer options
	timer = False	  # Timer on
	timerValue = 30   # Timer value in minutes
	timeTimer = 0  	  # The time when the Timer was activated in seconds 
	volumetime = 0	  # Last volume check time
	channeltime = 0	  # Last channel check time
	dateFormat = "%H:%M %d/%m/%Y"   # Date format

	alarmType = ALARM_OFF	# Alarm on
	alarmTime = "0:07:00"    # Alarm time default type,hours,minutes
	alarmTriggered = False	# Alarm fired

	stationName = ''		# Radio station name
	stationTitle = ''		# Radio station title

	VERSION	= "1.1"		# Version number
	VERSIONDATE = "06.01.2015"
	
# Set up Amplifier configuration 
	def start(self):
		if not os.path.isfile(ConfigFile) or os.path.getsize(ConfigFile) == 0:
			log.message("Missing configuration file " + ConfigFile, log.ERROR)
		else:
			self.configOK = True	# Must be set before calling getConfig()
			self.getConfig()

		self.boardrevision = self.getBoardRevision()
		#self.current_id = self.getStoredID(self.current_file)
		self.volume = self.getStoredVolume()
		self.setVolume(self.volume)
		self.timeTimer = int(time.time())
		self.timerValue = self.getStoredTimer()
		self.alarmTime = self.getStoredAlarm()
		#sType,sHours,sMinutes = self.alarmTime.split(':')
		#self.alarmType = int(sType)
		self.alarmType = 0
		return
	
		# Get configuration options

	def getConfig(self):
		section = 'RADIOD'

		if not self.configOK:
			return

		# Get options
		config.read(ConfigFile)
		try:
			options =  config.options(section)
			for option in options:
				parameter = config.get(section,option)
				msg = "Config option: " + option + " = " + parameter 
				log.message(msg,log.DEBUG)

				if option == 'loglevel':
					next

				elif option == 'mpdport':
					self.mpdport = parameter

				elif option == 'dateformat':
					self.dateFormat = parameter
				else:
					msg = "Invalid option " + option + ' in section ' \
						+ section + ' in ' + ConfigFile
					log.message(msg,log.ERROR)

		except ConfigParser.NoSectionError:
			msg = ConfigParser.NoSectionError(section),'in',ConfigFile
			log.message(msg,log.ERROR)
		return

	# Get volume and check if it has been changed by any MPD external client
	# Slug MPD calls to no more than  per 0.5 second
	def getVolume(self):
		volume = 0
		try:
			now = time.time()	
			if now > self.volumetime + 0.5:
				stats = self.getStats()
				volume = int(stats.get("volume"))
				self.volumetime = time.time()
			else:
				volume = self.volume
		except:
			log.message("amplifier.getVolume failed", log.ERROR)
			volume = 0
		if volume == str("None"):
			volume = 0

		if volume != self.volume:
			log.message("amplifier.getVolume external client changed volume " + str(volume),log.DEBUG)
			self.setVolume(volume)
			self.volumeChange = True
		return self.volume

	# Check for volume change
	def volumeChanged(self):
		volumeChange = self.volumeChange
		self.volumeChange = False
		return volumeChange

	# Set volume (Called from the amplifier client or external mpd client via getVolume())
	def setVolume(self,volume):
		if self.muted(): 
			self.unmute()
		else:
			if volume > 100:
				 volume = 100
			elif volume < 0:
				 volume = 0

			log.message("amplifier.setVolume " + str(volume),log.DEBUG)
			self.volume = volume
			#self.execMpc(client.setvol(self.volume))

			# Don't change stored volume (Needed for unmute function)
			if not self.muted():
				self.storeVolume(self.volume)
		return self.volume


	# Increase volume 
	def increaseVolume(self):
		if self.muted(): 
			self.unmute()
		self.volume = self.volume + 1
		self.setVolume(self.volume)
		return  self.volume

	# Decrease volume 
	def decreaseVolume(self):
		if self.muted(): 
			self.unmute()
		self.volume = self.volume - 1
		self.setVolume(self.volume)
		return  self.volume

	# Mute sound functions (Also stops MPD if not streaming)
	def mute(self):
		log.message("amplifier.mute streaming=" + str(self.streaming),log.DEBUG)
		#self.execMpc(client.setvol(0))
		self.volume = 0
		#self.execMpc(client.pause(1))
		return

	# Unmute sound fuction, get stored volume
	def unmute(self):
		self.volume = self.getStoredVolume()
		log.message("amplifier.unmute volume=" + str(self.volume),log.DEBUG)
		#self.execMpc(client.pause(0))
		#self.execMpc(client.setvol(self.volume))
		return self.volume

	def muted(self):
		muted = True
		if self.volume > 0:
			muted = False
		return muted

	# Get the stored volume
	def getStoredVolume(self):
		volume = 10
		if os.path.isfile(VolumeFile):
			try:
				volume = int(self.execCommand("cat " + VolumeFile) )
			except ValueError:
				volume = 10
		else:
			log.message("Error reading " + VolumeFile, log.ERROR)

		return volume

	# Store volume in volume file
	def storeVolume(self,volume):
		self.execCommand ("echo " + str(volume) + " > " + VolumeFile)
		return

	def getStoredChannel(self):
		channel = 1
		if os.path.isfile(ChannelFile):
			try:
				channel = int(self.execCommand("cat " + ChannelFile) )
			except ValueError:
				channel = 1
		else:
			log.message("Error reading " + ChannelFile, log.ERROR)

		return channel
	
		
	
	# Store volume in volume file
	def storeChannel(self,channel):
		self.execCommand ("echo " + str(channel) + " > " + ChannelFile)
		return
	
	# Timer functions
	def getTimer(self):
		return self.timer

	def timerOn(self):
		self.timerValue = self.getStoredTimer()
		self.timeTimer = int(time.time())
		self.timer = True
		return self.timer

	def timerOff(self):
		self.timer = False
		self.timerValue = 0
		return self.timer

	def getTimerValue(self):
		return self.timerValue

	def fireTimer(self):
		fireTimer = False
		if self.timer and self.timerValue > 0:
			now = int(time.time())
			if now > self.timeTimer + self.timerValue * 60:
				fireTimer = True
				# Store fired value
				self.storeTimer(self.timerValue)
				self.timerOff()
		return fireTimer

	# Display the amount of time remaining
	def getTimerString(self):
		tstring = ''
		now = int(time.time())
		value = self.timeTimer + self.timerValue * 60  - now
		if value > 0:
			minutes,seconds = divmod(value,60)
			hours,minutes = divmod(minutes,60)
			if hours > 0:
				tstring = '%d:%02d:%02d' % (hours,minutes,seconds)
			else:
				tstring = '%d:%02d' % (minutes,seconds)
		return  tstring

	# Increment timer.   
	def incrementTimer(self,inc):
		if self.timerValue > 120:
			inc = 10
		self.timerValue += inc
		if self.timerValue > self.ONEDAYMINS:
			self.timerValue = self.ONEDAYMINS
		self.timeTimer = int(time.time())
		return self.timerValue

	def decrementTimer(self,dec):
		if self.timerValue > 120:
			dec = 10
		self.timerValue -= dec
		if self.timerValue < 0:
			self.timerValue = 0	
			self.timer = False
		self.timeTimer = int(time.time())
		return self.timerValue

	# Get the stored timer value
	def getStoredTimer(self):
		timerValue = 0
		if os.path.isfile(TimerFile):
			try:
				timerValue = int(self.execCommand("cat " + TimerFile) )
			except ValueError:
				timerValue = 30
		else:
			log.message("Error reading " + TimerFile, log.ERROR)
		return timerValue

	# Store timer time in timer file
        def storeTimer(self,timerValue):
		self.execCommand ("echo " + str(timerValue) + " > " + TimerFile)
		return

	# amplifier Alarm Functions
	def alarmActive(self):
		alarmActive = False
		if self.alarmType != self.ALARM_OFF:
			alarmActive = True
		return alarmActive

	def alarmCycle(self,direction):
		if direction == self.UP:
			self.alarmType += 1
		else:
			self.alarmType -= 1

		if self.alarmType > self.ALARM_LAST:
			self.alarmType = self.ALARM_OFF
		elif self.alarmType < self.ALARM_OFF:
			self.alarmType = self.ALARM_LAST

		if self.alarmType > self.ALARM_OFF:
			self.alarmTime = self.getStoredAlarm()
		
		sType,sHours,sMinutes = self.alarmTime.split(':')
		hours = int(sHours)
		minutes = int(sMinutes)
		self.alarmTime = '%d:%d:%02d' % (self.alarmType,hours,minutes)
		self.storeAlarm(self.alarmTime)

		return self.alarmType

	# Switch off the alarm unless repeat or days of the week
	def alarmOff(self):
		if self.alarmType == self.ALARM_ON:
			self.alarmType = self.ALARM_OFF
		return self.alarmType

	# Increment alarm time
	def incrementAlarm(self,inc):
		sType,sHours,sMinutes = self.alarmTime.split(':')
		hours = int(sHours)
		minutes = int(sMinutes) + inc
		if minutes >= 60:
			minutes = minutes - 60 
			hours += 1
		if hours >= 24:
			hours = 0
		self.alarmTime = '%d:%d:%02d' % (self.alarmType,hours,minutes)
		self.storeAlarm(self.alarmTime)
		return '%d:%02d' % (hours,minutes) 

	# Decrement alarm time
	def decrementAlarm(self,dec):
		sType,sHours,sMinutes = self.alarmTime.split(':')
		hours = int(sHours)
		minutes = int(sMinutes) - dec
		if minutes < 0:
			minutes = minutes + 60 
			hours -= 1
		if hours < 0:
			hours = 23
		self.alarmTime = '%d:%d:%02d' % (self.alarmType,hours,minutes)
		self.storeAlarm(self.alarmTime)
		return '%d:%02d' % (hours,minutes) 

	# Fire alarm if current hours/mins matches time now
	def alarmFired(self):

		fireAlarm = False
		if self.alarmType > self.ALARM_OFF:
			sType,sHours,sMinutes = self.alarmTime.split(':')
			type = int(sType)
			hours = int(sHours)
			minutes = int(sMinutes)
			t1 = datetime.datetime.now()
			t2 = datetime.time(hours, minutes)
			weekday =  t1.today().weekday()

			if t1.hour == t2.hour and t1.minute == t2.minute and not self.alarmTriggered:
				# Is this a weekday
				if type == self.ALARM_WEEKDAYS and weekday < 5: 
					fireAlarm = True
				elif type < self.ALARM_WEEKDAYS:	
					fireAlarm = True

				if fireAlarm:
					self.alarmTriggered = fireAlarm 
					if type == self.ALARM_ON:
						self.alarmOff()
					log.message("amplifier.larmFired type " + str(type), log.DEBUG)
			else:
				self.alarmTriggered = False 

		return  fireAlarm

	# Get the stored alarm value
	def getStoredAlarm(self):
		alarmValue = '' 
		if os.path.isfile(AlarmFile):
			try:
				alarmValue = self.execCommand("cat " + AlarmFile)
			except ValueError:
				alarmValue = "0:7:00"
		else:
			log.message("Error reading " + AlarmFile, log.ERROR)
		return alarmValue

	# Store alarm time in alarm file
        def storeAlarm(self,alarmString):
		self.execCommand ("echo " + alarmString + " > " + AlarmFile)
		return

	# Get the actual alarm time
	def getAlarmTime(self):
		sType,sHours,sMinutes = self.alarmTime.split(':')
		hours = int(sHours)
		minutes = int(sMinutes)
		return '%d:%02d' % (hours,minutes) 
		
	# Get the alarm type
	def getAlarmType(self):
		return  self.alarmType
	

	
	# Get the stored date format
	def getStoredDateFormat(self):
		return self.dateFormat

	# Get the date format
	def getDateFormat(self):
		return self.dateFormat

		
	# Option changed 
	def optionChanged(self):
		return self.option_changed

	def optionChangedTrue(self):
		self.option_changed = True
		return

	def optionChangedFalse(self):
		self.option_changed = False
		return

	# Set  and get Display mode
	def getDisplayMode(self):
		return self.display_mode

	# Mode string for debugging
	def getDisplayModeString(self):
		sMode = ["MODE_TIME", "MODE_SEARCH", "MODE_SOURCE",
			 "MODE_OPTIONS", "MODE_RSS", "MODE_IP", "MODE_SLEEP"] 
		return sMode[self.display_mode]

	def setDisplayMode(self,display_mode):
		self.display_mode = display_mode
		return
	
	# Set any option you like here 
	def getOption(self):
		return self.option

	def setOption(self,option):
		self.option = option
		return
	
	# Execute system command
	def execCommand(self,cmd):
		p = os.popen(cmd)
		return  p.readline().rstrip('\n')
	
	
	# Check to see if an error occured
	def gotError(self):
		return self.error

	# Get the error string if a bad channel
	def getErrorString(self):
		self.error = False
		return self.errorStr
	
	def getSwitch(self):
		return self.switch

	# Routines for storing rotary encoder events
	def incrementEvent(self):
		self.numevents += 1
		return self.numevents
	
	def decrementEvent(self):
		self.numevents -= 1
		if self.numevents < 0:
			self.numevents = 0
		return self.numevents
	
	def getEvents(self):
		return self.numevents
	
	def resetEvents(self):
		self.numevents = 0
		return self.numevents
	
	# Version number
	def getVersion(self):
		return self.VERSION

	
	# Get Board Revison	
	def getBoardRevision(self):
		revision = 1
		with open("/proc/cpuinfo") as f:
			cpuinfo = f.read()
		rev_hex = re.search(r"(?<=\nRevision)[ |:|\t]*(\w+)", cpuinfo).group(1)
		rev_int = int(rev_hex,16)
		if rev_int > 3:
			revision = 2
		self.boardrevision = revision
		log.message("Board revision " + str(self.boardrevision), log.INFO)
		return self.boardrevision
