import os
import time
import RPi.GPIO as GPIO
import spidev 
from  LargeFont import classLargeFont
from  SmaleFont import classSmaleFont

spi = spidev.SpiDev()

LargeFontArray = classLargeFont.bytes
SmaleFontArray = classSmaleFont.bytes

#SSD1322 Pins
LCD_RES = 25	#Reset
LCD_CS  = 23	#Chip select
LCD_DC = 24  	#Data Command

#SSD1322 Command
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
#SSD1322 Variables
Contrast_level =0xFF
yfpos = 0x14

class Lcd:
	
	VERSION = "Oled_04.01.15"
	
	def getVersion(self):
		return self.VERSION
		
	def Clear_ram(self):
		self.SSD1322_Command(SetColumnAddress) 
		self.SSD1322_Data(0x00)
		self.SSD1322_Data(0x77) 
		self.SSD1322_Command(SetRowAddress)
		self.SSD1322_Data(0x00)
		self.SSD1322_Data(0x7f) 
		self.SSD1322_Command(WriteRamCmd)    
		for y in xrange(128):
			for x in xrange(120):
				self.SSD1322_Data(0x00)         
	
	def SSD1322_Command(self,dataByte):
		GPIO.output(LCD_DC,False) # Select command register
		spi.writebytes([dataByte])

	def SSD1322_Data(self,dataByte):
		GPIO.output(LCD_DC,True) # Select data register
		spi.writebytes([dataByte])    

	def writeDataBytes(self,dataBytes):
		GPIO.output(LCD_DC,True) # Select data register	
		spi.writebytes(dataBytes)
		
	def SPI_Init(self):
		spi.open(0,0)
		spi.cshigh = False   # CS active low
		spi.lsbfirst = False # Send MSB first
		spi.mode = 3         # Clock idle high, data on 2nd edge (end of pulse)
		spi.max_speed_hz = 5000000 

	def init(self,revision=2):
		spi.open(0,0)
		spi.cshigh = False   # CS active low
		spi.lsbfirst = False # Send MSB first
		spi.mode = 3         # Clock idle high, data on 2nd edge (end of pulse)
		spi.max_speed_hz = 5000000 
		time.sleep(0.1) 

		GPIO.setwarnings(False)	     # Disable warnings
		GPIO.setmode(GPIO.BCM)   
		time.sleep(0.1) 
		
		GPIO.setup(LCD_RES,GPIO.OUT) # 25 RESET (low to reset)
		GPIO.output(LCD_RES,True)    #    Release the RESET

		GPIO.setup(LCD_CS,GPIO.OUT) #  Chip select
		GPIO.output(LCD_CS,False)    # Chip Select

		GPIO.setup(LCD_DC,GPIO.OUT)   # 24 D/C
		time.sleep(0.4) 

		GPIO.output(LCD_RES,True) 
		GPIO.output(LCD_DC,True)
		GPIO.output(LCD_CS,True)
		time.sleep(0.2)
		GPIO.output(LCD_CS, False)
		time.sleep(0.2)
		GPIO.output(LCD_RES,False) # Activate reset
		time.sleep(0.5 )      # Hold it low for half a second
		GPIO.output(LCD_RES,True)  # Release reset
		time.sleep(0.2)       # Give the chip a second to come up
		
		GPIO.output(LCD_CS,False)    # Chip Select
		
		self.SSD1322_Command(0xFD)
		
		self.SSD1322_Command(0xFD) # SET COMMAND LOCK 
		self.SSD1322_Data(0x12) # UNLOCK 
		self.SSD1322_Command(SetDisplayON)# DISPLAY OFF 
		self.SSD1322_Command(0xB3) # DISPLAYDIVIDE CLOCKRADIO/OSCILLATAR FREQUANCY*/ 
		self.SSD1322_Data(0x91) 
		self.SSD1322_Command(0xCA) # multiplex ratio 
		self.SSD1322_Data(0x3F) # duty = 1/64 
		self.SSD1322_Command(SetDispOffset) # set offset 
		self.SSD1322_Data(0x00)
		self.SSD1322_Command(SetDisplayStartLine) # start line 
		self.SSD1322_Data(0x00)
		
		self.SSD1322_Command(SetRemap) #set remap
		self.SSD1322_Data(0x14)
		self.SSD1322_Data(0x11)
		
		self.SSD1322_Command(0xAB) # funtion selection 
		self.SSD1322_Data(0x01) # selection external vdd  
		self.SSD1322_Command(0xB4)
		self.SSD1322_Data(0xA0)
		self.SSD1322_Data(0xfd) 
		self.SSD1322_Command(SetContrastCurrent) # set contrast current  
		self.SSD1322_Data(Contrast_level)
		self.SSD1322_Command(0xC7) # master contrast current control 
		self.SSD1322_Data(0x0f)
		 
		self.SSD1322_Command(0xB1) # SET PHASE LENGTH
		self.SSD1322_Data(0xE2)
		self.SSD1322_Command(0xD1)
		self.SSD1322_Data(0x82)
		self.SSD1322_Data(0x20) 
		self.SSD1322_Command(0xBB) # SET PRE-CHANGE VOLTAGE 
		self.SSD1322_Data(0x1F)
		self.SSD1322_Command(0xB6) # SET SECOND PRE-CHARGE PERIOD
		self.SSD1322_Data(0x08)
		self.SSD1322_Command(0xBE) # SET VCOMH  
		self.SSD1322_Data(0x07)
		self.SSD1322_Command(0xA6) # normal display 
		self.Clear_ram()
		self.SSD1322_Command(0xAF) # display ON
		GPIO.output(LCD_CS,True)

	def displayPreprocessedPicture(self,buffer):
		GPIO.output(LCD_CS,False)
		Set_Row_Address(0)         
		Set_Column_Address(0)
		self.SSD1322_Command(WriteRamCmd)    
		time.sleep(0.1)
		writeDataBytes(buffer[0:4096]) # SPI library allows only 4096 at a time
		writeDataBytes(buffer[4096:])    
		GPIO.output(LCD_CS,True)
		
	def Display_Picture(self,pic):
		GPIO.output(LCD_CS,False)
		Set_Row_Address(0)         
		Set_Column_Address(0)
		self.SSD1322_Command(WriteRamCmd)    
		for i in xrange(64):
			for j in xrange(32):
				Data_processing(pic[i*32+j])
		GPIO.output(LCD_CS,True)
		
	def Set_Row_Address(self,add):
		GPIO.output(LCD_CS,False)
		self.SSD1322_Command(SetRowAddress)# SET SECOND PRE-CHARGE PERIOD 
		add = 0x3f & add
		self.SSD1322_Data(add)
		self.SSD1322_Data(0x3f)
		GPIO.output(LCD_CS,True)
		
	def Set_Row_Address_Large(self,xpos, xposoffset):
		GPIO.output(LCD_CS,False)
		self.SSD1322_Command(SetRowAddress) 
		self.SSD1322_Data(xpos)
		self.SSD1322_Data(xposoffset)
		GPIO.output(LCD_CS,True)
		
	def Set_Column_Address(self,add):
		GPIO.output(LCD_CS,False)
		add = 0x3f & add
		self.SSD1322_Command(SetColumnAddress) # SET SECOND PRE-CHARGE PERIOD  
		self.SSD1322_Data(0x1c+add)
		self.SSD1322_Data(0x5b)
		GPIO.output(LCD_CS,True)
		
	def Set_Column_Address_Large(self,ypos,yposoffset):
		GPIO.output(LCD_CS,False)
		self.SSD1322_Command(SetColumnAddress) # SET SECOND PRE-CHARGE PERIOD  
		self.SSD1322_Data(ypos)
		self.SSD1322_Data(yposoffset)
		GPIO.output(LCD_CS,True)
		
	def Data_processing(self,temp): # turns 1byte B/W data to 4 bye gray data
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

		self.SSD1322_Data(d1)
		self.SSD1322_Data(d2)
		self.SSD1322_Data(d3)
		self.SSD1322_Data(d4)
	
	def Data_processing_Large(self,temp): # turns 1byte B/W data to 4 bye gray data
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

		self.SSD1322_Data(d1)
		self.SSD1322_Data(d2)
		self.SSD1322_Data(d3)
		self.SSD1322_Data(d4)
	
	def Write_number(self,value, column):
		GPIO.output(LCD_CS,False)
		for i in xrange(16):
			Set_Row_Address(i);
			Set_Column_Address(column);
			self.SSD1322_Command(WriteRamCmd); 
			Data_processing(numberImages[16*value+i])
		GPIO.output(LCD_CS,True)
		
	def adj_Contrast(self):
		GPIO.output(LCD_CS,False)
		DrawString(6,0," Contrast level")
		while(True):
			number = (int(input("Enter a contrast value: ")))
			number1=number/100;
			number2=number%100/10;
			number3=number%100%10;
			Write_number(number1,0);
			Write_number(number2,2);
			Write_number(number3,4);    
		
			self.SSD1322_Command(SetContrastCurrent)
			self.SSD1322_Data(number)    
		GPIO.output(LCD_CS,True)
	
	def Clear_Lcd(self,value1):
		GPIO.output(LCD_CS,False)
		self.Set_Row_Address(0)
		self.Set_Column_Address(0)       
		self.SSD1322_Command(WriteRamCmd)    
		for i in xrange(32):
			for k in xrange(32):
				self.Data_processing(value1)
			for k in xrange(32):
				self.Data_processing(value1)    
		GPIO.output(LCD_CS,True)
		
	def Lcd_On(self):
		GPIO.output(LCD_CS,False)
		self.SSD1322_Command(0xa5) # --all display on
		GPIO.output(LCD_CS,True)
	
	def Lcd_Off(self):
		GPIO.output(LCD_CS,False)
		self.SSD1322_Command(0xa4)
		self.SSD1322_Command(0xa6) # --set normal display
		GPIO.output(LCD_CS,True)
	
	def Lcd_Normal_Display(self):
		GPIO.output(LCD_CS,False)
		self.SSD1322_Command(0xa6) # --set normal display	
		GPIO.output(LCD_CS,True)
	
	def Gray_test(self):
		GPIO.output(LCD_CS,False)
		Set_Row_Address(0)
		Set_Column_Address(0)
		self.SSD1322_Command(WriteRamCmd)
		for m in xrange(32):
			j = 0
			for k in xrange(16):
				for i in xrange(8):
					self.SSD1322_Data(j)
				j = j + 0x11        
		
		for m in xrange(32):
			j = 255
			for k in xrange(16):
				for i in xrange(8):
					self.SSD1322_Data(j)
				j = j - 0x11
		GPIO.output(LCD_CS,True)
	
	def DrawString(self,x, y, pStr):
		GPIO.output(LCD_CS,False)
		for c in pStr:
			cc = ord(c)
			if cc<0x80:
				self.DrawSingleAscii(x,y,cc)
				x = x + 2
		GPIO.output(LCD_CS,True)
		
	def DrawSingleAscii(self,x, y, char):
		GPIO.output(LCD_CS,False)
		ofs = (char-32) * 16
		for i in xrange(16):
			self.Set_Row_Address(y+i)
			self.Set_Column_Address(x)
			self.SSD1322_Command(WriteRamCmd)
			str = SmaleFontArray[ofs + i]
			self.Data_processing(str)
		GPIO.output(LCD_CS,True)
		
	def DrawSingleAsciiLarge(self,x,y,n):
		GPIO.output(LCD_CS,False)
		ofs = 28
		self.SSD1322_Command(SetRemap) #set remap
		self.SSD1322_Data(0x14)
		self.SSD1322_Data(0x11)
		xoffset = LargeFontArray[n][0]
		xcount = LargeFontArray[n][1]
		self.Set_Column_Address_Large(ofs + x, ofs + x + xoffset)
		self.Set_Row_Address_Large(y, y + 100)
		self.SSD1322_Command(WriteRamCmd)
		for i in xrange(xcount):
			str = LargeFontArray[n][i+2]
			self.Data_processing_Large(str)

		self.SSD1322_Command(SetRemap) #set remap
		self.SSD1322_Data(0x14)
		self.SSD1322_Data(0x11)
		GPIO.output(LCD_CS,True)
		
	def ShowVolume(self,volume,mute):
		ones = volume % 10
		tens = ((volume % 100) - ones)/10
		hundreds = (volume  - (1000  * (volume /1000))) / 100
		tousends =  volume / 1000
		
		if mute == 1:
			onespos = 48
			tenspos = 40
			hundredpos = 32
			tousendpos = 24
			mutepos = 56
			self.DrawSingleAsciiLarge(mutepos,yfpos, 11)
		else:
			onespos = 56
			tenspos = 48
			hundredpos = 40
			tousendpos = 32
			
		if volume  == 0:  
			self.DrawSingleAsciiLarge(hundredpos,yfpos, 11)
			self.DrawSingleAsciiLarge(tenspos,yfpos, 11)
			self.DrawSingleAsciiLarge(onespos,yfpos, 11)
			
			self.DrawSingleAsciiLarge(56,yfpos, 10)
			
		elif volume > 0 and volume < 10:
			self.DrawSingleAsciiLarge(hundredpos,yfpos, 11)
			self.DrawSingleAsciiLarge(tenspos,yfpos, 11)
			self.DrawSingleAsciiLarge(onespos,yfpos,11)
			self.DrawSingleAsciiLarge(onespos,yfpos, ones)
			
		elif volume > 9 and volume < 100:
			self.DrawSingleAsciiLarge(hundredpos,yfpos, 11)
			self.DrawSingleAsciiLarge(tenspos,yfpos, tens)
			self.DrawSingleAsciiLarge(onespos,yfpos, ones)

		elif volume >=100 and volume < 1000:
			self.DrawSingleAsciiLarge(hundredpos,yfpos, hundreds)
			self.DrawSingleAsciiLarge(tenspos,yfpos, tens)
			self.DrawSingleAsciiLarge(onespos,yfpos, ones)
			
	
	def ShowMute(self):
		self.DrawSingleAsciiLarge(48,yfpos, 11)
		self.DrawSingleAsciiLarge(56,yfpos, 10)
	
	def ShowUnMute(self):
		self.DrawSingleAsciiLarge(48,yfpos, 11)
		self.DrawSingleAsciiLarge(56,yfpos, 11)
		
	def ShowInputChannel(self,inpchannel):
		channelones = inpchannel % 10
		if inpchannel >= 0:
			self.DrawSingleAsciiLarge(0x08,yfpos, channelones)
		
		
# End of Class