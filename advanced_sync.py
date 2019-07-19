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
kmax = 100

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

inputFile = "./neighbors/" + sys.argv[1] 
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

k = 1
while k <= kmax:
#	print >>sys.stderr, 'Waiting for neighbors to chime in'
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
			print 'received ', data, ' from ', s.getpeername()
			if data:
				#if data == "-1":
				#	print 'received kill message, shutting down process'
				#	killProcess = True

				#if the timestamp for this is not a duplicate, save it
				if int(data) > timeStamps[s.getpeername()[0]]:
					timeStamps[s.getpeername()[0]] = int(data)
				
				if s not in outputs:
					outputs.append(s)

				#do check for already having stored the timestamp for this neighbor
				#TODO: handle a "no data" case 

	print 'Checking timestamps...'
	readyToAdvance = True
	for n,v in timeStamps.items():
		if v < k:							#TODO: decide whether this makes sense
			readyToAdvance = False
			print 'v for ', n, '=', v 
	
	for s in writable:
		if allConnected:
			if readyToAdvance:
				k += 1
				print "increasing k"
				readyToAdvance = False
			s.send(str(k))
			print 'sending k=', k
			outputs.remove(s)

#	if killProcess:
#		exit(0)
