#~~ratio consensus distributed algorithm~~
#This program simulates a ratio consensus calculation for a single machine
#neighbors of the machine by passing an input file containing all the neighbors via the command line.

import select
import socket
import sys
import Queue
import time
import fcntl
import struct

#TODO: add data to input file to give DER info to each RPi, and add parsing capabilities here
#TODO: create structure for housing information for each neighbor
class Neighbor:
	def __init__(self, thisSocket):
		self.sock = thisSocket
		self.ip = thisSocket.getpeername()[0]
		self.y = list()
		self.z = list()
		#TODO: FINISH?

#returns true if all elements in a dictionary are "True" or they have been created
def all_true(dict):
	allGood = True
	for s,v in dict.items():
		if  not v:
			allGood = False
	return allGood


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


# ~~~~ MAIN CODE BLOCK ~~~~
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
tmax = 20

#dictionary of neighbor sockets
neighbors = {}
#timestamps for each neighbor

#use this socket to receive the incoming connections
recvsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#bind the receiving socket to this ip, and cycle through ports until ones available
#TODO: turns out this exception check is pretty pointless, just remove later
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
recvsocket.listen(3) #what does this accomplish?

inputFile = sys.argv[1] 
f = open(inputFile)

#code block parses the neighbors input file. Change the lodb to pidb when actually implementing
#initial probing for neighboring pis, if not found the program will simply continue on and wait for a connection

for line in f:
	newsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		line = line.rstrip('\n')
		#create new instance of neighbor class
		newsock.connect((pidb[line],PORT))
		print 'Connection successful with', newsock.getpeername()
		neighbors[pidb[line]] = Neighbor(newSock)

	except Exception as e:
		print 'Connection failure: ', e
		neighbors[pidb[line]] = 0

allConnected = all_have_connected(neighbors)

inputs = [ recvsocket ]
outputs = [ ]
exceptional = [ ]

for k, v in neighbors.items():
	if v:
		v.setblocking(0)
		inputs.append(v)
		outputs.append(v)

#timing

#booleans and counters
t = 0		#TODO: make this an input parameter, eventually want to be able to read from an XVL file
syncCount = 0
readyToAdvance = False
killProcess = False

#our i/o while loop 
while t <= tmax:		
	start = time.time()
	while ((time.time() - start) < 1.0) or not allConnected: #TODO: use online clock to synchronize actions of the PIs instead of this clunky system
	#see which sockets are ready to be written, read from and which are throwing exceptions
		readable, writable, exceptional = select.select(inputs, outputs, inputs)
		for s in readable:
			if s is recvsocket:
				#handle new connections coming in
				conn, client_address = s.accept()
				print >>sys.stderr, 'new connection with ', client_address, ' established'
				conn.setblocking(0)
				neighbors[client_address[0]] = Neighbor(conn)
				inputs.append(conn)
				outputs.append(conn)
				allConnected = all_have_connected(neighbors)
			else:
				data = s.recv(1024)
				if data:
					#print 'received ', data, ' from ', s.getpeername()
					splitData = data.split(':') #data format --> :time_stamp y[t] z[t] magnitude_of_I
					data = int(splitData[len(splitData) - 1])					#in case multiple values were concatenated in the input buffer, split it up and use the most recently sent value
					data = data.split()																#value_of_t[0] value_of_k[1] y[t][2] z[t][3] 	
					#print 'timestamp for ', s.getpeername(), 'being updated to ', int(data)
					#TODO write parsing for each message, will be easy with split()
	
					neighbors[s.getpeername()[0]].y[data[0]][data[1]] = data[2]
					neighbors[s.getpeername()[0]].z[data[0]][data[1]] = data[3]
				
					
					if int(data[0]) > t:			#if the received message is one time-inc ahead, we have to catch up
						
						#TODO: do something	
							
						break
						#print "sync count incremented to ", syncCount, ". K will increment when it is ", len(neighbors)
				else:
					#no data
					print 'Socket ', s.getpeername(), 'is unresponsive, closing connection and shutting down.' 
					killProcess = True
					if s in outputs:
						outputs.remove(s)
					inputs.remove(s)
					s.close()

		#check if we have updated timestamps from every neighbor
		if syncCount == len(neighbors):
			readyToAdvance = True
			syncCount = 0
		elif syncCount > len(neighbors):
			print 'ERROR: syncCount greater than number of neighbors.'
			print 'syncCount = ', syncCount
			print 'num of neighbors = ', len(neighbors)
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
				for key,sock in neighbors.items():
					outputs.append(sock)

		if killProcess:
			for s in inputs:
				inputs.remove(s)
				if s in outputs:
					outputs.remove(s)
				s.close()
			recvsocket.close()
			break



