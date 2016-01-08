import time
import RPi.GPIO as GPIO
from lcd_class import Lcd
from  LargeFont import classLargeFont
from  SmaleFont import classSmaleFont

lcd = Lcd()
LargeFontArray = classLargeFont.bytes
SmaleFontArray = classSmaleFont.bytes

GPIO.setmode(GPIO.BCM) # Use BCM GPIO numbers
GPIO.setwarnings(False)      # Ignore warnings

res = 25 
cs = 23
dc = 24 

#ssd1322 Command
cmd_EnableGrayScale = 0x00 
SetColumnAddress = 0x15
WriteRamCmd = 0x5C
cmd_ReadRam	= 0x5D
SetRowAddress = 0x75
SetRemap = 0xA0
SetDisplayStartLine = 0xA1
SetDispOffset = 0xA2
cmd_SetNormalDisp = 0xA4
cmd_SetDispOn = 0xA5
cmd_SetDispOff = 0xA6
cmd_SetDispInverse = 0xA7
SetDisplayON = 0xAE
SetContrastCurrent = 0xC1
SetCommandLock = 0xFD

GPIO.setup(res,GPIO.OUT) # 25 RESET (low to reset)
GPIO.output(res,True)    #    Release the RESET

GPIO.setup(cs,GPIO.OUT) #  Chip select
GPIO.output(cs,False)    # Chip Select

GPIO.setup(dc,GPIO.OUT)   # 24 D/C


def resetOLED():
	time.sleep(0.3) 
	GPIO.output(res,True) 
	GPIO.output(dc,True)
	GPIO.output(cs,True)
	time.sleep(0.3)
	GPIO.output(cs, False)
	time.sleep(0.3)
	GPIO.output(res,False) # Activate reset
	time.sleep(0.6 )      # Hold it low for half a second
	GPIO.output(res,True)  # Release reset
	time.sleep(0.5)       # Give the chip a second to come up
	GPIO.output(cs,False)    # Chip Select
 

Contrast_level=0xf0

import spidev
spi = spidev.SpiDev()
spi.open(0,0)
spi.cshigh = False   # CS active low
spi.lsbfirst = False # Send MSB first
spi.mode = 3         # Clock idle high, data on 2nd edge (end of pulse)
spi.max_speed_hz = 5000000  

def SSD1322_Command(dataByte):
	GPIO.output(dc,False) # Select command register
	spi.writebytes([dataByte])

def SSD1322_Data(dataByte):
	GPIO.output(dc,True) # Select data register
    	spi.writebytes([dataByte])    

def writeDataBytes(dataBytes):
	GPIO.output(dc,True) # Select data register	
	spi.writebytes(dataBytes)
    

pic1 = []
pic1Processed =[]

pic2Processed = []
pic2 = []
    
def Initial():    
    SSD1322_Command(SetCommandLock) # Set Command Lock
    
    SSD1322_Command(SetCommandLock) # SET COMMAND LOCK 
    SSD1322_Data(0x12) # UNLOCK 
    SSD1322_Command(SetDisplayON)# DISPLAY OFF 
    SSD1322_Command(0xB3) # DISPLAYDIVIDE CLOCKRADIO/OSCILLATAR FREQUANCY*/ 
    SSD1322_Data(0x91) 
    SSD1322_Command(0xCA) # multiplex ratio 
    SSD1322_Data(0x3F) # duty = 1/64 
    SSD1322_Command(SetDispOffset) # set offset 
    SSD1322_Data(0x00)
    SSD1322_Command(SetDisplayStartLine) # start line 
    SSD1322_Data(0x00)
    
    SSD1322_Command(SetRemap) #set remap
    SSD1322_Data(0x14)
    SSD1322_Data(0x11)
    
    SSD1322_Command(0xAB) # funtion selection 
    SSD1322_Data(0x01) # selection external vdd  
    SSD1322_Command(0xB4)
    SSD1322_Data(0xA0)
    SSD1322_Data(0xfd) 
    SSD1322_Command(SetContrastCurrent) # set contrast current  
    SSD1322_Data(Contrast_level)
    SSD1322_Command(0xC7) # master contrast current control 
    SSD1322_Data(0x0f)
     
    SSD1322_Command(0xB1) # SET PHASE LENGTH
    SSD1322_Data(0xE2)
    SSD1322_Command(0xD1)
    SSD1322_Data(0x82)
    SSD1322_Data(0x20) 
    SSD1322_Command(0xBB) # SET PRE-CHANGE VOLTAGE 
    SSD1322_Data(0x1F)
    SSD1322_Command(0xB6) # SET SECOND PRE-CHARGE PERIOD
    SSD1322_Data(0x08)
    SSD1322_Command(0xBE) # SET VCOMH  
    SSD1322_Data(0x07)
    SSD1322_Command(0xA6) # normal display 
    Clear_ram()
    SSD1322_Command(0xAF) # display ON

def Clear_ram():
    SSD1322_Command(SetColumnAddress) 
    SSD1322_Data(0x00)
    SSD1322_Data(0x77) 
    SSD1322_Command(SetRowAddress)
    SSD1322_Data(0x00)
    SSD1322_Data(0x7f) 
    SSD1322_Command(WriteRamCmd)    
    for y in xrange(128):
        for x in xrange(120):
            SSD1322_Data(0x00)         

def preprocessPicture(pic,buffer):
    for i in xrange(64):
        for j in xrange(32):
            temp = pic[i*32+j]
            temp1=temp&0x80
            temp2=(temp&0x40)>>3
            temp3=(temp&0x20)<<2
            temp4=(temp&0x10)>>1
            temp5=(temp&0x08)<<4
            temp6=(temp&0x04)<<1
            temp7=(temp&0x02)<<6
            temp8=(temp&0x01)<<3
            h11=temp1|(temp1>>1)|(temp1>>2)|(temp1>>3)
            h12=temp2|(temp2>>1)|(temp2>>2)|(temp2>>3)
            h13=temp3|(temp3>>1)|(temp3>>2)|(temp3>>3)
            h14=temp4|(temp4>>1)|(temp4>>2)|(temp4>>3)
            h15=temp5|(temp5>>1)|(temp5>>2)|(temp5>>3)
            h16=temp6|(temp6>>1)|(temp6>>2)|(temp6>>3)
            h17=temp7|(temp7>>1)|(temp7>>2)|(temp7>>3)
            h18=temp8|(temp8>>1)|(temp8>>2)|(temp8>>3)
            d1=h11|h12
            d2=h13|h14
            d3=h15|h16
            d4=h17|h18
    
            buffer.append(d1)
            buffer.append(d2)
            buffer.append(d3)
            buffer.append(d4)                
    
def displayPreprocessedPicture(buffer):
    Set_Row_Address(0)         
    Set_Column_Address(0)
    SSD1322_Command(WriteRamCmd)    
    time.sleep(0.1)
    writeDataBytes(buffer[0:4096]) # SPI library allows only 4096 at a time
    writeDataBytes(buffer[4096:])    
    
def Display_Picture(pic):
    Set_Row_Address(0)         
    Set_Column_Address(0)
    SSD1322_Command(WriteRamCmd)    
    for i in xrange(64):
        for j in xrange(32):
            Data_processing(pic[i*32+j])

def Set_Row_Address(add):
    SSD1322_Command(SetRowAddress)# SET SECOND PRE-CHARGE PERIOD 
    add = 0x3f & add
    SSD1322_Data(add)
    SSD1322_Data(0x3f)

def Set_Row_Address_Large(xpos, xposoffset):
    SSD1322_Command(SetRowAddress) 
    SSD1322_Data(xpos)
    SSD1322_Data(xposoffset)

def Set_Column_Address(add):
    add = 0x3f & add
    SSD1322_Command(SetColumnAddress) # SET SECOND PRE-CHARGE PERIOD  
    SSD1322_Data(0x1c+add)
    SSD1322_Data(0x5b)

def Set_Column_Address_Large(ypos,yposoffset):
    SSD1322_Command(SetColumnAddress) # SET SECOND PRE-CHARGE PERIOD  
    SSD1322_Data(ypos)
    SSD1322_Data(yposoffset)

def Data_processing(temp): # turns 1byte B/W data to 4 bye gray data
	temp1=temp&0x80
	temp2=(temp&0x40)>>3
	temp3=(temp&0x20)<<2
	temp4=(temp&0x10)>>1
	temp5=(temp&0x08)<<4
	temp6=(temp&0x04)<<1
	temp7=(temp&0x02)<<6
	temp8=(temp&0x01)<<3
	h11=temp1|(temp1>>1)|(temp1>>2)|(temp1>>3)
	h12=temp2|(temp2>>1)|(temp2>>2)|(temp2>>3)
	h13=temp3|(temp3>>1)|(temp3>>2)|(temp3>>3)
	h14=temp4|(temp4>>1)|(temp4>>2)|(temp4>>3)
	h15=temp5|(temp5>>1)|(temp5>>2)|(temp5>>3)
	h16=temp6|(temp6>>1)|(temp6>>2)|(temp6>>3)
	h17=temp7|(temp7>>1)|(temp7>>2)|(temp7>>3)
	h18=temp8|(temp8>>1)|(temp8>>2)|(temp8>>3)
	d1=h11|h12
	d2=h13|h14
	d3=h15|h16
	d4=h17|h18

	SSD1322_Data(d1)
	SSD1322_Data(d2)
	SSD1322_Data(d3)
	SSD1322_Data(d4)

def Data_processing_Large(temp): # turns 1byte B/W data to 4 bye gray data
	temp1=temp&0x80
	temp2=(temp&0x40)>>3
	temp3=(temp&0x20)<<2
	temp4=(temp&0x10)>>1
	temp5=(temp&0x08)<<4
	temp6=(temp&0x04)<<1
	temp7=(temp&0x02)<<6
	temp8=(temp&0x01)<<3
	h11=temp1|(temp1>>1)|(temp1>>2)|(temp1>>3)
	h12=temp2|(temp2>>1)|(temp2>>2)|(temp2>>3)
	h13=temp3|(temp3>>1)|(temp3>>2)|(temp3>>3)
	h14=temp4|(temp4>>1)|(temp4>>2)|(temp4>>3)
	h15=temp5|(temp5>>1)|(temp5>>2)|(temp5>>3)
	h16=temp6|(temp6>>1)|(temp6>>2)|(temp6>>3)
	h17=temp7|(temp7>>1)|(temp7>>2)|(temp7>>3)
	h18=temp8|(temp8>>1)|(temp8>>2)|(temp8>>3)
	d1=h11|h12
	d2=h13|h14
	d3=h15|h16
	d4=h17|h18

	SSD1322_Data(d1)
	SSD1322_Data(d2)
	SSD1322_Data(d3)
	SSD1322_Data(d4)
			
def Write_number(value, column):
    for i in xrange(16):
        Set_Row_Address(i);
        Set_Column_Address(column);
        SSD1322_Command(WriteRamCmd); 
        Data_processing(numberImages[16*value+i])
    
def adj_Contrast():
    DrawString(6,0," Contrast level")
    
    while(True):
        number = (int(input("Enter a contrast value: ")))
        number1=number/100;
        number2=number%100/10;
        number3=number%100%10;
        Write_number(number1,0);
        Write_number(number2,2);
        Write_number(number3,4);    
    
        SSD1322_Command(SetContrastCurrent)
        SSD1322_Data(number)    
    
def Display_Chess(value1,value2):
    Set_Row_Address(0)
    Set_Column_Address(0)       
    SSD1322_Command(WriteRamCmd)    
    for i in xrange(32):
        for k in xrange(32):
            Data_processing(value1)
        for k in xrange(32):
            Data_processing(value2)    

def Gray_test():
    Set_Row_Address(0)
    Set_Column_Address(0)
    SSD1322_Command(WriteRamCmd)
    
    for m in xrange(32):
        j = 0
        for k in xrange(16):
            for i in xrange(8):
                SSD1322_Data(j)
            j = j + 0x11        
    
    for m in xrange(32):
        j = 255
        for k in xrange(16):
            for i in xrange(8):
                SSD1322_Data(j)
            j = j - 0x11

def DrawString(x, y, pStr):
   for c in pStr:
        cc = ord(c)
            
        if cc>=0x80:
            DrawSpecialChar(x,y,cc)
            x = x + 4            
        else:
            DrawSingleAscii(x,y,cc)
            x = x + 2
            
def DrawSpecialChar(x, y, s):
    s = s - 0x80
    for i in xrange(16):
        Set_Row_Address(y+i)
        Set_Column_Address(x)
        SSD1322_Command(WriteRamCmd)
        for k in xrange(2):
            Data_processing(specialChars[s*16+k+i*2])

def DrawSingleAscii(x, y, char):
    ofs = (char-32) * 16
    for i in xrange(16):
        Set_Row_Address(y+i)
        Set_Column_Address(x)
        SSD1322_Command(WriteRamCmd)
        str = SmaleFontArray[ofs + i]
        Data_processing(str)

def DrawSingleAsciiLarge(x,y,n):
	ofs = 28
	SSD1322_Command(SetRemap) #set remap
	SSD1322_Data(0x14)
	SSD1322_Data(0x11)
	xoffset = LargeFontArray[n][0]
	xcount = LargeFontArray[n][1]
	Set_Column_Address_Large(ofs + x, ofs + x + xoffset)
	Set_Row_Address_Large(y, y + 100)
	SSD1322_Command(WriteRamCmd)
	for i in xrange(xcount):
		str = LargeFontArray[n][i+2]
		Data_processing_Large(str)

	SSD1322_Command(SetRemap) #set remap
	SSD1322_Data(0x14)
	SSD1322_Data(0x11)
    		 
def ShowVolume(volume):
	ones = volume % 10
	tens = ((volume % 100) - ones)/10
	hundreds = (volume  - (1000  * (volume /1000))) / 100
	tousends =  volume / 1000
	
	if volume  == 0:  
		DrawSingleAsciiLarge(0,0x0d, 10)
		DrawSingleAsciiLarge(8,0x0d, 11)
		DrawSingleAsciiLarge(16,0x0d, 11)
		DrawSingleAsciiLarge(24,0x0d, 11)
	elif volume > 0 and volume < 10:
		DrawSingleAsciiLarge(0,0x0d, 11)
		DrawSingleAsciiLarge(8,0x0d, 11)
		DrawSingleAsciiLarge(16,0x0d, ones)
		DrawSingleAsciiLarge(24,0x0d, 11)
	elif volume > 9 and volume < 100:
		DrawSingleAsciiLarge(0,0x0d, 11)
		DrawSingleAsciiLarge(8,0x0d, tens)
		DrawSingleAsciiLarge(16,0x0d, ones)
		DrawSingleAsciiLarge(24,0x0d, 11)
	elif volume > 99 and volume < 1000:
		DrawSingleAsciiLarge(0,0x0d, hundreds)
		DrawSingleAsciiLarge(8,0x0d, tens)
		DrawSingleAsciiLarge(16,0x0d, ones)
		DrawSingleAsciiLarge(24,0x0d, 11)	
	
	
def main():    
	print "Resetting Amplifier ..."
	resetOLED()    
	
	lcd.init(2)

	print "Initializing Amplifier ..."
	Initial()

	print "All pixels on/off ..."
	SSD1322_Command(0xa5) # --all display on
	time.sleep(1.0)
	SSD1322_Command(0xa4) # --all Display off
	time.sleep(1.0)

	SSD1322_Command(0xa6) # --set normal display    

	print "Wait ..."
	Display_Chess(0x00,0x00) # clear display
	DrawString (0,0, "Power On - Waiting")
	time.sleep(2.0)
	DrawString (0,0, "Ready   ")
	time.sleep(2.0)
	DrawString (0,0, "Volumen ")
	DrawSingleAsciiLarge(24,0x0d, 10)
	ShowVolume(9)
	    
    
if __name__ == "__main__":
    main()
    
