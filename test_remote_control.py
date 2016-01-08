#!/usr/bin/env python
#       
# $Id: test_remote_control.py,v 1.1 2015/03/08 11:47:41 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
# IR remote control test
#

import pifacecad.ir
import signal
from signal import SIGUSR1
import time
import sys
import os
import RPi.GPIO as GPIO

global irevent

irevent = 0

def print_ir_code(event):
	print  (event.ir_code)
	key = event.ir_code
	if key == 'KEY_UP': 
		irevent = 30
		#exec_cmd('mpc volume +5')		
	if key == 'KEY_DOWN': 
		irevent = 31
		#exec_cmd('mpc volume -5')		
	if key == 'KEY_LEFT': 
		irevent = 32
		#exec_cmd('mpc next')		
	if key == 'KEY_RIGHT': 
		irevent = 33
		#exec_cmd('mpc prev')		
	return

# Execute system command
def exec_cmd(cmd):
        p = os.popen(cmd)
        result = p.readline().rstrip('\n')
        return result


listener = pifacecad.ir.IREventListener(prog="amplifier4")
listener.register('KEY_UP',print_ir_code)
listener.register('KEY_DOWN',print_ir_code)
listener.register('KEY_LEFT',print_ir_code)
listener.register('KEY_RIGHT',print_ir_code)
listener.register('KEY_MENU',print_ir_code)
listener.register('KEY_PLAY',print_ir_code)

print "Activating"
listener.activate()

