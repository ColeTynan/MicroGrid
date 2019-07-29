#Timed Sync: Handles synchronization between a variable network of RPis. Takes an input file as a commmand line param, which houses the Labels (e.g. R1\n R2) of the neighbors
#neighbors of the machine by passing an input file containing all the neighbors via the command line.

import fcntl
import Queue
import select
import socket
import struct
import sys
import time

#TODO: create structure for housing information for each neighbor

#returns true if all elements in a dictionary are "True" or they have been created
def all_true(dict):
	allGood = True
	for s,v in dict.items():
		if  not v:
			allGood = False
	return allGood

#all_true for lists

#function that checks that the dictionary of neighbors is fully populated and displays output
def all_have_connected(dict):
	allGood = all_true(dict)
	if allGood:
			print 'all have connected!'
			print 'Connected neighbors:'
			for v,n in dict.items():
				print v
	return allGood
		
#code for getting this pi's ip-address( retrieved from 'https://stackoverflow.com/questions/24196932/how-can-i-get-the-ip-address-of-eth0-in-python')
def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

#dictionary for the IPs of the raspberry pis
pidb = {'R1': "169.254.86.232",
				'R2': "169.254.142.58",
				'R3': "169.254.180.72",
				'R4': "169.254.160.208"
		}

#port to listen to when connecting to remote IPs
PORT = 20000 
THIS_IP = get_ip_address('eth0')
#maximum iteration
kmax = 10000

#dictionary of neighbor sockets
neighborSock = {}
#timestamps for each neighbor
timeStamps = {}
#Sent Disconnection link for all neighbors
disconnectNeighbors = {}

#use this socket to receive the incoming connections
recvsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#bind the receiving socket to this ip, and cycle through ports until ones available
while True:
	try:
		THIS_COMP = (THIS_IP, PORT)
		print 'Attempting to create receiving socket:', THIS_COMP
		recvsocket.bind(THIS_COMP)
		break
	except Exception as e:
		print "Failed to create receiving socket: ", e
		exit(0)

recvsocket.setblocking(0)
recvsocket.listen(3)

inputFile = sys.argv[1] 
f = open(inputFile)

#TODO: set up parsing for information in data file about the DER (if its in I, gmin, gmax, etc) for simplified, just if its the "timer" or not

#Read the info for this specific DER
#specifies gmin, gmax, if the DER is in I, etc. 
#FORMAT: gmin gmax In_I_bool(0 or 1) |I| 
inI = False
info = f.readline()
info = info.split()
if int(info[2]) != 0:
	inI = True
print 'inI = ', inI
#TODO: in Ratio Consensus, in the case of multiple DERs in I, there needs to be a method of deciding which DER will be the timer

#We start by seeking out neighbors. some fail to accept connections, we wait for them to come online
for line in f:
	newsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		line = line.rstrip('\n')
		timeStamps[pidb[line]] = -1				#TODO: change timeStamp to a dictionary of lists to store the placeholder y/z values
		disconnectNeighbors[pidb[line]] = False
		newsock.connect((pidb[line],PORT))
		print 'Connection successful with', newsock.getpeername()
		neighborSock[pidb[line]] = newsock
	except Exception as e:
		print 'Connection failed with IP', pidb[line]
		neighborSock[pidb[line]] = 0

allConnected = all_have_connected(neighborSock)

inputs = [ recvsocket ]
outputs = [ ]
exceptional = [ ]

for k, v in neighborSock.items():
	if v:
		v.setblocking(0)
		inputs.append(v)
		outputs.append(v)

#timing
#print 'Starting timer...'
start = time.time()

#booleans and counters
t = 0					#counter for the time intervals
tmax = 10				#the number of intervals
next_t = False			#Buffer to send the canceling t signal to the next machines required for both timer and regular nodes
k = 1
readyToAdvance = False
syncCount = 0
killProcess = False

#=== Current Signal represents the state of this machine === #
#-1 = Stop
# 0 = Start
# 1 = Reset
current_signal = -1

startTime = 0
endTime = 0

not_all_disconnected = True

#our i/o while loop 
while not_all_disconnected:

	if inI and all_have_connected and t != tmax:
		current_signal = 0
		endTime = time.time()
		if (endTime - startTime) >= 1:
			t+=1
			startTime = time.time()
			current_signal = 1
	
	if current_signal == 1:
		if allConnected:
			for key,sock in neighborSock.items():
				if sock not in outputs:
					outputs.append(sock)
		for key in timeStamps.keys():
			timeStamps[key] = -1
		current_signal = 0
		k = 1
	
	if t == tmax:
		if allConnected:
			for key,sock in neighborSock.items():
				if sock not in outputs:
					outputs.append(sock)


	readable, writable, exceptional = select.select(inputs, outputs, inputs)			#see which sockets are ready to be writting, read from and which are throwing exceptions
	#resetting the whole thing
			
	for s in readable:
		if s is recvsocket:
			conn, client_address = s.accept()
			print >>sys.stderr, 'new connection with ', client_address, ' established'
			conn.setblocking(0)
			neighborSock[client_address[0]] = conn
			inputs.append(conn)	
			outputs.append(conn)
			allConnected = all_have_connected(neighborSock)
		else:
			data = s.recv(1024)
			if data:	
				#if the timestamp for this is not a duplicate, save it
				#print 'received ', data, ' from ', s.getpeername()
				#FORMAT: t, current_signal, k, ____
				split_data = data.split(':')
				#also split by '/' separator in future
				print 'received ', data, 'from ', s.getpeername()
				other_t = int(split_data[0])
				other_k = int(split_data[1])
				other_signal = int(split_data[2])

				try: 
					ip_address = s.getpeername()[0]
					#Update T
					if not inI and (other_t > t):
						t = other_t
						#Change current signal to reset only if we received a signal from t+1 that we are starting a new second
						if other_signal == 1:
							current_signal = 1
					#Update K
					if other_k > timeStamps[ip_address] and t == other_t:
						print 'timestamp for ', s.getpeername(), 'being updated to ', other_k
						timeStamps[ip_address] = other_k
						if other_k > k + 1:
							print "Out of sync at k = ", k, ", read ", other_k , "from ", s.getpeername()
							killProcess = True
							print "sync count incremented to ", syncCount, ". K will increment when it is ", len(neighborSock)
					
				except Exception as e:
					print "Caught exception in parsing messages: ", e
			else:
				#no data
				print 'Socket ', s.getpeername(), 'is unresponsive, closing connection and shutting down.' 
				killProcess = True
				if s in outputs:
					outputs.remove(s)
				inputs.remove(s)
				s.close()

	syncCounter = 0
	#check if we have updated timestamps from every neighbor
	for sock, stamp in timeStamps.items():
		if (stamp >= k):
			syncCounter += 1
	if syncCounter == len(neighborSock):
		readyToAdvance = True
	elif syncCounter > len(neighborSock):
		print 'ERROR: syncCount greater than number of neighbors.'
		print 'syncCount = ', syncCount
		print 'num of neighbors = ', len(neighborSock)
		killProcess = True 
	#message sending
	for s in writable:
		if t == tmax:
			disconnectNeighbors[s.getpeername()[0]] = True
		send_msg = str(t) + ":" + str(k) + ":" + str(current_signal)
		print 'Sending ', send_msg, ' to ', s.getpeername()
		s.send(send_msg)
		outputs.remove(s)

	#Check for sent all disconnections
	if all_true(disconnectNeighbors):
		not_all_disconnected = False

	#Error catching code block
	for s in exceptional:
		print 'Socket', s.getpeername(), ' is throwing errors, turning it off and shutting down process'
		inputs.remove(s)
		if s in outputs:
			outputs.remove(s)
		s.close()
		killProcess = True

	#reset all of our variables -- later this will include the ratio-consensus variables
	#code block checks to see if k needs to be incremented
	if allConnected:
		if readyToAdvance:
			k += 1
			readyToAdvance = False
			for key,sock in neighborSock.items():
				outputs.append(sock)

	#End processes check
	if killProcess:
		for s in inputs:
			inputs.remove(s)
			if s in outputs:
				outputs.remove(s)
			s.close()
		recvsocket.close()
		break
		
	if inI:
		print 'Ending t = ', t , ' with k = ', k
		print 'Start time = ', startTime-start, 'seconds from start of outer loop'
		print 'EndTime = ', endTime - start, ' seconds'
		print 'time elapsed = ',  endTime - startTime, ' seconds'
		t += 1

#output final time stamps (Debugging)
print 'k for this machine ', THIS_IP, ': ', k
print len(timeStamps)
for key, value in timeStamps.items():
	print key, ': ', value

"""
end = time.time()
print 'Total time taken=', end - start, ' seconds.'
"""
