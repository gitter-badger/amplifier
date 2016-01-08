import os
import RPi.GPIO as GPIO
import pifacecad.ir
import signal
import subprocess
import sys
import time
import string
import datetime 
import threading

import shutil
import atexit
import traceback

from lcd_class import Lcd
from  LargeFont import classLargeFont
from  SmaleFont import classSmaleFont
from rotary_class import RotaryEncoder
from log_class import Log
from amplifier_class import Amplifier
from amplifier_daemon import Daemon
log = Log()
lcd = Lcd()
amplifier = Amplifier()
 
# Switch IO Pins 

# Volume rotary encoder rechts
5,6,13
RIGHT_A = 5
RIGHT_B = 6
RIGHT_BUTTON = 13 

# Input Channel rotary encoder links 
#17,27,22
LEFT_A = 17
LEFT_B = 27
LEFT_BUTTON = 22

def signalHandler(signal,frame):
	global lcd
	global log
	#radio.execCommand("umount /media > /dev/null 2>&1")
	#radio.execCommand("umount /share > /dev/null 2>&1")
	pid = os.getpid()
	log.message("Amp stopped, PID " + str(pid), log.INFO)
	lcd.Clear_Lcd(0x00)
	lcd.DrawString (0,5, "Amplifier Power Down")
	lcd.DrawString (0,25, ("PID:" +str(pid)))
	lcd.DrawString (0,45, ("GOOD BY !!!"))
	
	GPIO.cleanup()
	time.sleep(2.0)
	sys.exit(0)

# Daemon class
class MyDaemon(Daemon):
	def run(self):
		global CurrentFile
		global volumeknob,tunerknob, switch, channelrotaryposition, volumenrotaryposition
		
		channelrotaryposition = 0
		volumenrotaryposition = 0
		
		global Einschaltdelay
		Einschaltdelay = 1
				
		switch = 0
		global ActualVolume
		ActualVolume = 0
		global irevent, irchannelcounter, irvolumcounter
		irevent = 0
		irchannelcounter = 0
		irvolumcounter = 0
		log.init('amplifierwp')
		signal.signal(signal.SIGTERM,signalHandler)
		progcall = str(sys.argv)
		
		ipaddr = exec_cmd('hostname -I')
		myos = exec_cmd('uname -a')
		hostname = exec_cmd('hostname -s')
		log.message(myos, log.INFO)
		
		log.message("GPIO version " + str(GPIO.VERSION), log.INFO)
		
		time.sleep(0.5)
		lcd.init(2)
		time.sleep(0.5)
		lcd.init(2)
		time.sleep(0.5)
		
		log.message("LCD_OLED version " + str(lcd.VERSION), log.INFO)
		
		lcd.Lcd_On()
		time.sleep(0.1)
		lcd.Lcd_Off()
		time.sleep(0.1)
		lcd.Clear_Lcd(0x00)
		
		
		lcd.ShowMute()    
		
		#amplifier.storeVolume(30)
		#amplifier.storeChannel(2)
		
		listener = pifacecad.ir.IREventListener(prog="amplifier4")
		listener.register('KEY_UP',print_ir_code)
		listener.register('KEY_DOWN',print_ir_code)	
		listener.register('KEY_LEFT',print_ir_code)
		listener.register('KEY_RIGHT',print_ir_code)
		listener.register('KEY_MENU',print_ir_code)
		listener.register('KEY_PLAY',print_ir_code)
		listener.activate()
		
		#lcd.DrawString (0,10, ("GPIO-V:" + str(GPIO.VERSION)))
		lcd.DrawString (0,10, ("Paltauf Amplifier: " + str(amplifier.VERSION)))
		
		lcd.DrawString (0,30, ("IP:" +str(ipaddr)))
		
		
		lcd.DrawString (0,50, ("Ready in " + str(Einschaltdelay) + " Seconds" ))
		
		time.sleep(Einschaltdelay)
		
		
		
		lcd.Clear_Lcd(0x00)
		lcd.DrawString (0,0, "Eingang ")
		lcd.DrawString (44,0,"Volumen ")
		
		amplifier.start()
		
		
		volumeknob = RotaryEncoder(RIGHT_A,RIGHT_B,RIGHT_BUTTON,volume_event,2)
		tunerknob = RotaryEncoder(LEFT_A,LEFT_B,LEFT_BUTTON,channel_event,2)
		log.message("Running" , log.INFO)
		
		lcd.Clear_Lcd(0x00)
		lcd.DrawString (0,0, "Eingang ")
		lcd.DrawString (44,0,"Volumen ")
		
		
		volumenrotaryposition = amplifier.getStoredVolume()
		channelrotaryposition = amplifier.getStoredChannel()
		
		lcd.ShowVolume(volumenrotaryposition,0)
		lcd.ShowInputChannel(channelrotaryposition)
		
		while True:
			#if switch > 0 and switch < 5:
			#	lcd.ShowVolume(volumenrotaryposition,0)
			
			#elif switch > 10 and switch < 20:
				#lcd.ShowInputChannel(channelrotaryposition)
			
			switch =0
			time.sleep(0.5)
	
	
	def status(self):
		# Get the pid from the pidfile
		try:
			pf = file(self.pidfile,'r')
			pid = int(pf.read().strip())
			pf.close()
		except IOError:
			pid = None

		if not pid:
			message = "Amplifier status: not running"
	    		log.message(message, log.INFO)
			print message 
		else:
			message = "Ampifier4 running pid " + str(pid)
	    		log.message(message, log.INFO)
			print message 
		return
	
		
# endof class ovverides 
			

def print_ir_code(event):
	global volumenrotaryposition,channelrotaryposition
	global irevent
	global irvolumcounter, irchannelcounter
	volumechangepos = 0
	volumechangeneg = 0
	
	channelchangepos = 0
	channelchangeneg = 0
	
	key = event.ir_code
	if key == 'KEY_UP': 
		irevent = 30
		volumenrotaryposition +=1
		volumechangepos = 1
		irvolumcounter +=1
		
	if key == 'KEY_DOWN': 
		irevent = 31
		volumenrotaryposition -=1
		volumechangepos = 1
		irvolumcounter +=1
		
				
	if key == 'KEY_LEFT': 
		irevent = 32
		channelrotaryposition -=1
		channelchangeneg = 1
		irchannelcounter +=1
	if key == 'KEY_RIGHT': 
		irevent = 33
		channelrotaryposition +=1
		channelchangepos = 1
		irchannelcounter +=1		
	
	if volumechangepos == 1 and irvolumcounter == 5:
		volumenrotaryposition = volumenrotaryposition -4
		if volumenrotaryposition > 100:
			volumenrotaryposition = 100
		if volumenrotaryposition <= 0:
			volumenrotaryposition = 0
		
		amplifier.setVolume(volumenrotaryposition)
		lcd.ShowVolume(volumenrotaryposition,0)
		volumechangepos = 0
		irvolumcounter = 0
	
	if volumechangeneg == 1 and irvolumcounter == 5:
		volumenrotaryposition = volumenrotaryposition +4
		if volumenrotaryposition > 100:
			volumenrotaryposition = 100
		if volumenrotaryposition <= 0:
			volumenrotaryposition = 0
		
		amplifier.setVolume(volumenrotaryposition)
		lcd.ShowVolume(volumenrotaryposition,0)
		volumechangeneg = 0
		irvolumcounter = 0
		
	if channelchangepos == 1 and irchannelcounter == 5:
		channelrotaryposition = channelrotaryposition -4
		if channelrotaryposition >= 5:
			channelrotaryposition = 5
		
		if channelrotaryposition <= 1:
			channelrotaryposition = 1
		amplifier.storeChannel(channelrotaryposition)
		lcd.ShowInputChannel(channelrotaryposition)	
		channelchangepos = 0
		irchannelcounter = 0
	
	if channelchangeneg == 1 and irchannelcounter == 5:
		channelrotaryposition = channelrotaryposition + 4
		if channelrotaryposition >= 5:
			channelrotaryposition = 5
		
		if channelrotaryposition <= 1:
			channelrotaryposition = 1
		amplifier.storeChannel(channelrotaryposition)
		lcd.ShowInputChannel(channelrotaryposition)	
		channelchangeneg = 0
		irchannelcounter = 0
	
	
	return


	# Execute system command
def exec_cmd(cmd):
	p = os.popen(cmd)
	result = p.readline().rstrip('\n')
	return result

def volume_event(event):
	global volumeknob
	global switch
	global volumenrotaryposition
	switch = 0
	ButtonNotPressed = volumeknob.getSwitchState(RIGHT_BUTTON)

	# Suppress events if volume button pressed
	if ButtonNotPressed:
		#radio.incrementEvent()
		if event == RotaryEncoder.CLOCKWISE:
			switch = 1
			volumenrotaryposition +=1
			 
		elif event == RotaryEncoder.ANTICLOCKWISE:
			switch = 2
			volumenrotaryposition -=1
		if event ==  RotaryEncoder.BUTTONDOWN:
			switch = 3
		
		if event ==  RotaryEncoder.BUTTONUP:
			switch = 4
		if volumenrotaryposition > 100:
			volumenrotaryposition = 100
		if volumenrotaryposition <= 0:
			volumenrotaryposition = 0
		amplifier.setVolume(volumenrotaryposition)
		lcd.ShowVolume(volumenrotaryposition,0)
	
	return

# Call back routine for the tuner control knob
def channel_event(event):
	global channelrotaryposition
	global tunerknob
	global switch
	switch = 0
	timepressed  = 0 
	ButtonNotPressed = tunerknob.getSwitchState(LEFT_BUTTON)

	# Suppress events if volume button pressed
	if ButtonNotPressed:
		#radio.incrementEvent()
		if event == RotaryEncoder.CLOCKWISE:
			channelrotaryposition += 1
			switch = 14
			
		elif event == RotaryEncoder.ANTICLOCKWISE:
			channelrotaryposition -= 1
			switch = 15
			
		if event ==  RotaryEncoder.BUTTONDOWN:
			switch = 16
			timepressed = time.time()
		
		if event ==  RotaryEncoder.BUTTONUP:
			timepressed =  time.time() - timepressed 
		
		if channelrotaryposition >= 5:
			channelrotaryposition = 5
		
		if channelrotaryposition <= 1:
			channelrotaryposition = 1
		amplifier.storeChannel(channelrotaryposition)
		lcd.ShowInputChannel(channelrotaryposition)	
		
	return

### Main routine ###
if __name__ == "__main__":
	daemon = MyDaemon('/var/run/amplifier4.pid')
	if len(sys.argv) == 2:
		if 'start' == sys.argv[1]:
			daemon.start()
		elif 'stop' == sys.argv[1]:
			os.system("service mpd stop")
			daemon.stop()
		elif 'restart' == sys.argv[1]:
			daemon.restart()
		elif 'status' == sys.argv[1]:
			daemon.status()
		elif 'version' == sys.argv[1]:
			print "Version " + amplifier.getVersion()
		else:
			print "Unknown command: " + sys.argv[1]
			sys.exit(2)
		sys.exit(0)
	else:
		print "usage: %s start|stop|restart|status|version" % sys.argv[0]
		sys.exit(2)

# End of script 

    
