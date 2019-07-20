#Advanced Sync: Handles synchronization between a variable network of RPis. Can specify the 
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
recvsocket.listen(3) #scale later?

inputFile = sys.argv[1] 
f = open(inputFile)

#code block parses the neighbors input file. Change the lodb to pidb when actually implementing
#initial probing for neighboring pis, if not found the program will simply continue on and wait for a connection

for line in f:
	newsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		line = line.rstrip('\n')
		timeStamps[pidb[line]] = -1
		newsock.connect((pidb[line],PORT))
		print 'Connection successful with', newsock.getpeername()
		neighborSock[pidb[line]] = newsock
	except Exception as e:
		print 'Connection failure: ', e
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

#We start by seeking out neighbors. some fail to accept connections, we wait for them to come online

#timing
start = time.time()

#booleans and counters
k = 1
syncCount = 0
readyToAdvance = False
killProcess = False

#our i/o while loop 
while k <= kmax:
	#see which sockets are ready to be writting, read from and which are throwing exceptions
	readable, writable, exceptional = select.select(inputs, outputs, inputs)

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
				splitData = data.split(':')
				data = int(splitData[len(splitData) - 1])					#in case multiple values were concatenated in the input buffer, split it up and use the most recently sent value

				if int(data) > timeStamps[s.getpeername()[0]]:
					#print 'timestamp for ', s.getpeername(), 'being updated to ', int(data)
					timeStamps[s.getpeername()[0]] = int(data)
					if int(data) >= k:
						syncCount += 1
						#print "sync count incremented to ", syncCount, ". K will increment when it is ", len(neighborSock)
			else:
				#no data
				print 'Socket ', s.getpeername(), 'is unresponsive, closing connection and shutting down.' 
				killProcess = True
				if s in outputs:
					outputs.remove(s)
				inputs.remove(s)
				s.close()

	#check if we have updated timestamps from every neighbor
	if syncCount == len(neighborSock):
		readyToAdvance = True
		syncCount = 0
	elif syncCount > len(neighborSock):
		print 'ERROR: syncCount greater than number of neighbors.'
		print 'syncCount = ', syncCount
		print 'num of neighbors = ', len(neighborSock)
		exit(0)

	for s in writable:
			send_mssg = ':' + str(k)
			s.send(send_mssg)
		#	print 'sending k=', k, ' to ', s.getpeername()
			outputs.remove(s)	#removing from outputs until we get a new k value

	for s in exceptional:
		print 'Socket', s.getpeername(), ' is throwing errors, turning it off and shutting down process'
		inputs.remove(s)
		if s in outputs:
			outputs.remove(s)
		s.close()
		killProcess = True

	
	if allConnected:
		if readyToAdvance:
			k += 1
			readyToAdvance = False
			for key,sock in neighborSock.items():
				outputs.append(sock)

	if killProcess:
		for s in inputs:
			inputs.remove(s)
			if s in outputs:
				outputs.remove(s)
			s.close()
		recvsocket.close()
		break

"""
#output final time stamps (Debugging)
print 'k for this machine ', THIS_IP, ': ', k
print len(timeStamps)
for key, value in timeStamps.items():
	print key, ': ', value
"""

end = time.time()
print 'Total time taken=', end - start


