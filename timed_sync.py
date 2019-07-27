#Timed Sync: Handles synchronization between a variable network of RPis. Takes an input file as a commmand line param, which houses the Labels (e.g. R1\n R2) of the neighbors
#neighbors of the machine by passing an input file containing all the neighbors via the command line.

import select
import socket
import sys
import Queue
import time
import fcntl
import struct

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
#dictionary keyed by neighbor sockets, values are bool, that show if this neighbor is ready to accept input from yet
readyNeighbor = {}
#timestamps for each neighbor
timeStamps = {}

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
		readyNeighbor[pidb[line]] = False
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
t = 0						#counter for the time intervals
tmax = 10				#the number of intervals
goMessage = "GO"
noGoMessage = "NO_GO"

#our i/o while loop 
while t <= tmax:
	k = 1
	RESET = True
	startTime = time.time()
	endTime = startTime
	

	#Timed loop
	while endTime - startTime <= 1.0:	
		if RESET:
			startTime = 0
			endTime = 0
			if allConnected:
				for key,sock in neighborSock.items():
					readyNeighbor[key] = False
					if sock not in outputs:
						outputs.append(sock)
			k = 1
			for key in timeStamps.keys():
				timeStamps[key] = -1
			SEND_GO = False
			SEND_NO_GO = False
			GO = False
			killProcess = False
			RESET = False
			readyToAdvance = False
		#END Reset
		
		readable, writable, exceptional = select.select(inputs, outputs, inputs, 1)			#see which sockets are ready to be writting, read from and which are throwing exceptions
		#resetting the whole thing
	
		if inI:		#If this der is the timer, send the GO signal
			if not GO and allConnected:
				print 'Timer is sending GO signal'
				time.sleep(1)
				SEND_GO = True
				GO = True
				#SEND_NO_GO = True
			#	GO = False
					
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
					data = data.split(':')
					#also split by '/' separator in future
					for message in data:
						print 'received ', message, 'from ', s.getpeername()
						if message == noGoMessage:
							readyNeighbor[s.getpeername()[0]] = False
							if GO:
								GO = False
								RESET = True
								SEND_NO_GO = True
						if message == goMessage:							#GO flag received, now we can immediately begin performing ratio consensus
							readyNeighbor[s.getpeername()[0]] = True
							if not GO:
								if allConnected:
									GO = True
									SEND_GO = True
								else:
									SEND_NO_GO = True
						if readyNeighbor[s.getpeername()[0]]:									#if this neighbor has sent the GO flag, we will start reading its input
							try: 
								if int(message) > timeStamps[s.getpeername()[0]]:
									print 'timestamp for ', s.getpeername(), 'being updated to ', int(message)
									timeStamps[s.getpeername()[0]] = int(message)
									if int(message) > k + 1:
										print "Out of sync at k = ", k, ", read ", int(message), "from ", s.getpeername()
										killProcess = True
							except Exception as e:
								print "Caught exception in parsing messages: ", e
					#data = int(splitData[len(splitData) - 1])					#in case multiple values were concatenated in the input buffer, split it up and use the most recently sent value
				else:
					#no data
					print 'Socket ', s.getpeername(), 'is unresponsive, closing connection and shutting down.' 
					killProcess = True
					if s in outputs:
						outputs.remove(s)
					inputs.remove(s)
					s.close()

		#END receiving block
		if GO and SEND_GO:
			startTime = time.time()

		syncCounter = 0
		#check if we have updated timestamps from every neighbor
		for sock, stamp in timeStamps.items():
			if (stamp >= k):
				syncCounter += 1
				print "sync count incremented to ", syncCounter, ". K will increment when it is ", len(neighborSock)
		if syncCounter == len(neighborSock):
			readyToAdvance = True
		elif syncCounter > len(neighborSock):
			print 'ERROR: syncCount greater than number of neighbors.'
			print 'syncCount = ', syncCounter
			print 'num of neighbors = ', len(neighborSock)
			killProcess = True 

		"""
		if syncCount == len(neighborSock):
			readyToAdvance = True
			syncCount = 0
		elif syncCount > len(neighborSock):
			print 'ERROR: syncCount greater than number of neighbors.'
			print 'syncCount = ', syncCount
			print 'num of neighbors = ', len(neighborSock)
			exit(0)
		"""

		#message sending
		for s in writable:
			if GO:	
				if SEND_GO:
					s.send(":" + goMessage)
				send_mssg = ":" + str(k)	
				print 'Sending ', send_mssg, ' to ', s.getpeername()
				s.send(send_mssg)
				outputs.remove(s)

			if SEND_NO_GO:
				s.send(":" + noGoMessage)
		#End sending loop
		SEND_NO_GO = False
		SEND_GO = False

		#if currently running, the program will save the end time
		if GO:
			endTime = time.time()

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
