#-------------------------------------------------------------------------------
# Copyright 2016 Congduc Pham, University of Pau, France.
# 
# Congduc.Pham@univ-pau.fr
#
# This file is part of the low-cost LoRa gateway developped at University of Pau
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with the program.  If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------
# Jul/2016 adapted by N. Bertuol under C. Pham supervision 
# 
# nicolas.bertuol@etud.univ-pau.fr
#
# Oct/2016. re-designed by C. Pham to use self-sufficient script per cloud
# Congduc.Pham@univ-pau.fr

import urllib2
import subprocess
import time
import ssl
import socket
import datetime
import sys
import re

# get key definition from external file to ease
# update of cloud script in the future
import key_ThingSpeak

try:
	key_ThingSpeak.source_list
except AttributeError:
	key_ThingSpeak.source_list=[]

# didn't get a response from thingspeak server?
connection_failure = False

# retry if return from server is 0?
retry = False

#plot snr instead of seq
_thingspeaksnr=False

# function to check connection availability with the server
def test_network_available():
	connection = False
	iteration = 0
	response = None
	
	# we try 4 times to connect to the server.
	while(not connection and iteration < 4) :
	    	try:
	    		# 3sec timeout in case of server available but overcrowded
			response=urllib2.urlopen('https://api.thingspeak.com/', timeout=3)
			connection = True
	    	except urllib2.URLError, e: pass
		except socket.timeout: pass
		except ssl.SSLError: pass
	    	
	    	# if connection_failure == True and the connection with the server is unavailable, don't waste more time, exit directly
	    	if(connection_failure and response is None) :
	    		print('Thingspeak: the server is still unavailable')
	    		iteration = 4
	    	# print connection failure
	    	elif(response is None) :
	    		print('Thingspeak: server unavailable, retrying to connect soon...')
	    		# wait before retrying
	    		time.sleep(1)
	    		iteration += 1
	    		
	return connection
	
# send a data to the server
def send_data(data, second_data):
	global connection_failure

	print 'rcv msg to log (\!) on ThingSpeak (',
				
	#use default channel?
	if data[0]=='':
		data[0]=key_ThingSpeak._private_thingspeak_channel_key
		print 'default',
	else:
		print data[0],
	
	print ',',
		
	#use default field?
	if data[1]=='':
		data[1]='1'
		print 'default',
	else:
		print data[1],				
	
	print '): '+data[2]
		
	#in the current example, log the data on the specified field x, then log the sequence number on field x+4
	#assuming that the first 4 fields are used for up to 4 sensors and the next 4 fields are used for their sequence number
	cmd = 'curl -s -k -X POST --data '+\
		'field'+data[1]+'='+data[2]+\
		'&field'+str(int(data[1])+4)+'='+second_data+\
		' https://api.thingspeak.com/update?key='+data[0]
	
	print("ThingSpeak: will issue curl cmd")
	print(cmd)
	args = cmd.split()
	
	#retry enabled
	if (retry) :
		out = '0'
		iteration = 0
		
		while(out == '0' and iteration < 6 and not connection_failure) :
			try:
				out = subprocess.check_output(args, shell=False)

				#if server return 0, we didn't wait 15sec, wait then
				if(out == '0'):
					print('ThingSpeak: less than 15sec between posts, retrying in 3sec')
					iteration += 1
					time.sleep( 3 )
				else:
					print('ThingSpeak: returned code from server is %s' % out)
			except subprocess.CalledProcessError:
				print("ThingSpeak: curl command failed (maybe a disconnection)")
				
				#update connection_failure
				connection_failure = True
				
	#retry disabled
	else :
		try:
			out = subprocess.check_output(args, shell=False)
			if (out == '0'):
				print('ThingSpeak: returned code from server is %s, do not retry' % out)
			else :
				print('ThingSpeak: returned code from server is %s' % out)
				
		except subprocess.CalledProcessError:
			print("ThingSpeak: curl command failed (maybe a disconnection)")
			connection_failure = True
			
	
def thingspeak_uploadSingleData(data, second_data):
	global connection_failure

	connected = test_network_available()
	
	# if we got a response from the server, send the data to it
	if(connected):
		connection_failure = False
		
		print("ThingSpeak: uploading (single)")
		send_data(data, second_data)
	else:
		connection_failure = True
		
	if(connection_failure):
		print("ThingSpeak: not uploading")
	
# upload multiple data
def thingspeak_uploadMultipleData(data_array):
	global connection_failure
	
	connected = test_network_available()
	
	# if we got a response from the server, send the data to it
	if(connected):
		connection_failure = False
		
		print("ThingSpeak: uploading (multiple)")
		print 'rcv msg to log (\!) on ThingSpeak (',		
	
		#use default channel?
		if data_array[0]=='':
			data_array[0]=key_ThingSpeak._private_thingspeak_channel_key
			print 'default',
		else:
			print data_array[0],
			
		print ',',
		
		#use default field?
		if data_array[1]=='':
			fieldNumber = 1
			print 'default',
		else:
			fieldNumber = int(data_array[1])
			print data_array[1],				
	
		print '): '
		
		#we skip the thingspeak channel and field index when iterating	
		iteration = 2

		cmd = 'curl -s -k -X POST --data '
		while(iteration<len(data_array)):
			if(iteration == 2):
				#first iteration
				cmd += 'field'+str(fieldNumber)+'='+data_array[iteration]
			else:
				#other iterations
				cmd += '&field'+str(fieldNumber)+'='+data_array[iteration]
		 
			iteration += 1
			fieldNumber += 1
			
		cmd += ' https://api.thingspeak.com/update?key='+data_array[0]
		
		print("ThingSpeak: will issue curl cmd")
		print(cmd)
		args = cmd.split()
	
		#retry enabled
		if (retry) :
			out = '0'
			iteration = 0
		
			while(out == '0' and iteration < 6 and not connection_failure) :
				try:
					out = subprocess.check_output(args, shell=False)

					#if server return 0, we didn't wait 15sec, wait then
					if(out == '0'):
						print('ThingSpeak: less than 15sec between posts, retrying in 3sec')
						iteration += 1
						time.sleep( 3 )
					else:
						print('ThingSpeak: returned code from server is %s' % out)
				except subprocess.CalledProcessError:
					print("ThingSpeak: curl command failed (maybe a disconnection)")
					
					#update connection_failure
					connection_failure = True
				
		#retry disabled
		else :
			try:
				out = subprocess.check_output(args, shell=False)
				if (out == '0'):
					print('ThingSpeak: returned code from server is %s, do not retry' % out)
				else :
					print('ThingSpeak: returned code from server is %s' % out)
				
			except subprocess.CalledProcessError:
				print("ThingSpeak: curl command failed (maybe a disconnection)")
				connection_failure = True
	else:
		connection_failure = True
		
	if(connection_failure):
		print("ThingSpeak: not uploading")
			
	
def thingspeak_setRetry(retry_bool):

	global retry
	retry = retry_bool
	
def thingspeak_printDataToSend(dataToSend):
	
	iteration = 0
	
	while(iteration<len(dataToSend)):			
		print "==================================="
		print "data number: " + str(iteration)
		print "data value: " + str(dataToSend[iteration])
		print "==================================="
		iteration += 1
			
	

# main
# -------------------

def main(ldata, pdata, rdata, tdata, gwid):

	#this is common code to process packet information provided by the main gateway script (i.e. post_processing_gw.py)
	#these information are provided in case you need them	
	arr = map(int,pdata.split(','))
	dst=arr[0]
	ptype=arr[1]				
	src=arr[2]
	seq=arr[3]
	datalen=arr[4]
	SNR=arr[5]
	RSSI=arr[6]

	if (str(src) in key_ThingSpeak.source_list) or (len(key_ThingSpeak.source_list)==0):
	
		#syntax used by the end-device
		#thingspeak_channel#thingspeak_field#value1/value2/value3/value4... 
		#ex: ##22.4/85... or 22.4/85... or thingspeak_channel##22.4/85... 
		#or #thingspeak_field#22.4/85... to use some default value
				
		# get number of '#' separator
		nsharp = ldata.count('#')			
		#no separator
		if nsharp==0:
			#will use default channel and field
			data=['','']
		
			#contains ['', '', value1, value2, ...]
			data_array = data + re.split("/", ldata)		
		elif nsharp==1:
			#only 1 separator
		
			data_array = re.split("#|/", ldata)
		
			#if the first item has length > 1 then we assume that it is a channel write key
			if len(data_array[0])>1:
				#insert '' to indicate default field
				data_array.insert(1,'');		
			else:
				#insert '' to indicate default channel
				data_array.insert(0,'');		
		else:
			#contains [channel, field, value1, value2, ...]
			data_array = re.split("#|/", ldata)	
		
		#just in case we have an ending CR or 0
		data_array[len(data_array)-1] = data_array[len(data_array)-1].replace('\n', '')
		data_array[len(data_array)-1] = data_array[len(data_array)-1].replace('\0', '')	
	
		#test if there are characters at the end of each value, then delete these characters
		i = 3
		while i < len(data_array) :
			while not data_array[i][len(data_array[i])-1].isdigit() :
				data_array[i] = data_array[i][:-1]
			i += 1
		
		#get number of '/' separator
		nslash = ldata.count('/')	
		index_first_data = 2		
		
		#data_array contains the multiple data to send to thingspeak, last value is the SNR
		data_array.append(str(SNR))
		
		#data contains the single data to send to thingspeak plus channel (data[0]) and field (data[1]) 
		data = []
		data.append(data_array[0]) #channel (if '' default)
		data.append(data_array[1]) #field (if '' default)		
		data.append(data_array[index_first_data]) #value to add (the first sensor value in data_array)
	
		#upload data to thingspeak
		#JUST FOR UPLOAD A SINGLE DATA IN A SPECIFIC FIELD AND SECOND DATA				
		#thingspeak_uploadSingleData(data, second_data)   

		#to upload multiple data with nomenclature fields, comment the previous line and uncomment the following line
		thingspeak_printDataToSend(data_array)
		thingspeak_uploadMultipleData(data_array)
	else:
		print "Source is not is source list, not sending with CloudThingSpeak.py"				
	
if __name__ == "__main__":
	main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
	

