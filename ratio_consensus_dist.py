#timed sync: handles synchronization between a variable network of rpis. takes an input file as a commmand line param, which houses the labels (e.g. r1\n r2) of the neighbors
#neighbors of the machine by passing an input file containing all the neighbors via the command line.
#TODO: add reading of an input file (the pr data file), change decision of master node to generalize code more
#TODO: strenuously test the static version of this, compare to the single machine implementation
#todo: think of edge cases (e.g. different graph structures, varying input values, etc.) and test these as well
#note: we need data for the presentation and the research paper, so make sure to record tests when we have a working version to go off of

import select
import socket
import sys
import time
import fcntl
import struct
import csv

#class to house information about the neighbors of the PI
class Neighbor:
	def __init__(self, theSocket):
		self.k = -1
		self.y = list()
		self.z = list()
		self.y = [0.0]*10000
		self.z = [0.0]*10000
		self.sock = theSocket
		self.ready = False
		self.isOpen = True

	def setReady(self, flag):
		try:
			if type(flag) is not bool:
				raise TypeError('WRONG TYPE')
			self.ready = flag
			return True
		except TypeError as e:
			#print >>sys.stderr, 'ERROR: wrong type given to setReady()'
			return False

	def isReady(self):
		return self.ready
	
	def reset(self):
		self.k = -1
		del self.y[:]
		del self.z[:]
		self.ready = False

	def closeSock(self):
		sock.close()
		self.isOpen = False
#Neighbor class

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
			#print 'all have connected!'
			#print 'Connected neighbors:'
			#for v,n in dict.items():
			pass
				#print v
	return allGood
#def all_have_connected
		
#code for getting this pi's ip-address( retrieved from 'https://stackoverflow.com/questions/24196932/how-can-i-get-the-ip-address-of-eth0-in-python')
def get_ip_address(ifname):
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		return socket.inet_ntoa(fcntl.ioctl(
				s.fileno(),
				0x8915,  # SIOCGIFADDR
				struct.pack('256s', ifname[:15])
		)[20:24])
#def get_ip_address


#~~~~~~~~~~~MAIN CODE BLOCK BEGINS~~~~~~~~~~~~#

#dictionary for the IPs of the raspberry pis
#TODO: set up and record the IPs of the other pis
pidb = {'R1': "169.254.86.232",
				'R2': "169.254.142.58",
				'R3': "169.254.180.72",
				'R4': "169.254.160.208",
				'R5': "169.254.121.217",
				'R6': "169.254.17.57",
				'R7': "169.254.249.0",
				'R8': "169.254.128.136"
		 }

#port to listen to when connecting to remote IPs
PORT = 20000 
THIS_IP = get_ip_address('eth0')

#loop variables and messages
tmax = 2								#Maximum number of time intervals (outer loop)
t = 0										#iterator for outer loop TODO: have this be a parameter read from a file
goMessage = "GO"				#message that is received and sent, indicating that sending and receving of data should begin
noGoMessage = "NO_GO"		#message that is sent by a Pi that is not yet fully connected, indicating a shutdown of the system of Pis should begin
endMessage = "END"			#message sent when inner loop ends, indicates to other Pis to stop receiving 

#dictionary of neighbor objects
neighbors = {}

#use this socket to receive the incoming connections
recvsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#bind the receiving socket to this ip
while True:
	try:
		THIS_COMP = (THIS_IP, PORT)
		#print 'Attempting to create receiving socket:', THIS_COMP
		recvsocket.bind(THIS_COMP)
		break
	except Exception as e:
		#print "Failed to create receiving socket: ", e
		#print "Retrying...\n"
		time.sleep(1)

recvsocket.setblocking(0)
recvsocket.listen(3)

inputFile = sys.argv[1] 
f = open(inputFile)
outFile = open("output.txt", "w+")

#TODO: set up parsing for information in data file about the DER (if its in I, gmin, gmax, etc) for simplified, just if its the "timer" or not

#Read the info for this specific DER
#specifies gmin, gmax, if the DER is in I, etc. 
#FORMAT: g_min g_max In_I_bool(0 or 1) |I| 
try:
	info = f.readline()
	info = info.split()
	g_min = float(info[0])
	g_max = float(info[1])
	inI = False
	if int(info[2]) != 0:
		inI = True
	sizeOfI = int(info[3])
	tempPr = float(info[4])
except Exception as e:
	pass
 #print e
 #print "Check input file is correct"
##print 'inI = ', inI
#TODO: in Ratio Consensus, in the case of multiple DERs in I, there needs to be a method of deciding which DER will be the timer
#Probably would be best to just decide in the input file instead of implementing a convoluted method of deciding which will take the lead
#TODO: Actually implement ratio consensus

#We start by seeking out neighbors. some fail to accept connections, we wait for them to come online
for line in f:
	newsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		line = line.rstrip('\n')
		newsock.connect((pidb[line],PORT))
		#print 'Connection successful with', newsock.getpeername()
		neighbors[pidb[line]] = Neighbor(newsock)
	except Exception as e:
		#print 'Connection failed with IP', pidb[line]
		neighbors[pidb[line]] = 0

time_limit = 1.0															#Time limit in seconds
numNeighbors = len(neighbors) + 1
allConnected = all_have_connected(neighbors)
thisY = list()
thisZ = list()
thisY.append(tempPr)									#Init the Y-array
#TODO: Create and init the Z array, add code to loop to calculate.

inputs = [ recvsocket ]
outputs = [ ]
exceptional = [ ]

for k, v in neighbors.items():
	if v:
		v.sock.setblocking(0)
		inputs.append(v.sock)
		outputs.append(v.sock)

#initialize y and z values
initZ = g_max - g_min
initY = 0.0
if inI:
	initY = (tempPr/float(sizeOfI)) - g_min
else: 
	initY = - g_min

##print 'Starting timer...'
start = time.time()

#booleans and counters
#our i/o while loop 
while t <= tmax:

	k = 0
	RESET = True
	startTime = time.time()
	endTime = startTime
	END_INNER = False
	
	#Timed loop
	while not END_INNER:	
		if RESET:
			startTime = 0
			endTime = 0
			for key,neigh in neighbors.items():
				if neigh:
					neigh.reset()
					if neigh.sock not in outputs:
						outputs.append(neigh.sock)
			k = 0
			SEND_GO = False
			SEND_NO_GO = False
			GO = False
			killProcess = False
			del thisY[:]
			thisY = [0.0]*10000
			thisZ = [0.0]*10000
			thisY[0] = initY
			thisZ[0] = initZ
			readyToAdvance = False
			RESET = False
		#END Reset
		
		readable, writable, exceptional = select.select(inputs, outputs, inputs, 0)			#see which sockets are ready to be writting, read from and which are throwing exceptions
		#resetting the whole thing
	
		if inI:		#If this der is the timer, send the GO signal
			if not GO and allConnected:
				##print 'Timer is sending GO signal'
				time.sleep(1)
				SEND_GO = True
				GO = True	
		for s in readable:
			if s is recvsocket:						#if we have a new connection, then accept it and add it to database of connected neighbors and check if all have connected
				conn, client_address = s.accept()
				#print >>sys.stderr, 'new connection with ', client_address, ' established'
				conn.setblocking(0)
				neighbors[client_address[0]] = Neighbor(conn)
				inputs.append(conn)	
				outputs.append(conn)
				allConnected = all_have_connected(neighbors)
			else:
				data = s.recv(1024)
				neighbor_ip = s.getpeername()
				if data:	
					#if the timestamp for this is not a duplicate, save it
					##print 'received ', data, ' from ', neighbor_ip
					#Split input up by message separator. 
					data = data.split(':')
					for message in data:
						#Format of message after split: t_value[0] k_value[1] y_value[2] z_value[3] 
						#try: 
							message = message.split('/')
														#TODO: add calculations and code for z_values
							#print 'received ', message, 'from ', neighbor_ip
							if message[0] == noGoMessage:
								neighbors[neighbor_ip[0]].setReady(False)
								if GO:
									GO = False
									RESET = True
									SEND_NO_GO = True
							elif message[0] == goMessage:							#GO flag received, now we can immediately begin performing ratio consensus
								neighbors[neighbor_ip[0]].reset()
								neighbors[neighbor_ip[0]].setReady(True) 
								
								if not GO:
									if allConnected:
										GO = True
										SEND_GO = True
									else:
										SEND_NO_GO = True
							elif message[0] == endMessage:				#NOTE: Probably don't need this.
								neighbors[neighbor_ip[0]].setReady(False)
								#TODO: figure out a way to handle neighbors getting ahead or behind with the iteration
							elif message[0] == '':
								pass

							elif neighbors[neighbor_ip[0]].isReady():									#if this neighbor has sent the GO flag, we will start reading its input
								#print 'went into the calculating step'
								t_value = int(message[0])
								k_value = int(message[1])
								y_value = float(message[2])
								z_value = float(message[3])

								if True:

								#try:

									if (t_value == t):
										if (k_value > neighbors[neighbor_ip[0]].k) and (k_value <= k + 1 ):
											#print 'timestamp for ', neighbor_ip, 'being updated from ', neighbors[neighbor_ip[0]].k ,'to ', k_value
											neighbors[neighbor_ip[0]].k = k_value
											#print 'len(thisY) : ', len(thisY), ' and k_value is ', k_value
											if len(thisY) <= (k_value + 1):
												thisY.append(y_value)				#NOTE: optimize later?
											else:	
												if not SEND_NO_GO and allConnected:
													thisY[k_value + 1] += y_value 
											if len(thisZ) <= (k_value + 1):
												thisZ.append(z_value)				#NOTE: optimize later?
											else:	
												if not SEND_NO_GO and allConnected:
													thisZ[k_value + 1] += z_value 

										else:
											#print "Out of sync at k = ", k, ", read ", k_value, "from ", neighbor_ip
											killProcess = True
											#print 'The neighbors current value of k:', neighbors[neighbor_ip[0]].k
											#print 'k_value > neighbors[neighbor_ip[0]].k): ', (k_value > neighbors[neighbor_ip[0]].k) 
											#print '(k_value <= k + 1 ):', (k_value <= k + 1 )
									else:
										#print 'We have a neighbor on a different t: ', neighbor_ip, ' with neighbor t = ', t_value, ' and our t: ', t
										#print 'The neighbors current value of k:', neighbors[neighbor_ip[0]].k
										#print 'k_value > neighbors[neighbor_ip[0]].k): ', (k_value > neighbors[neighbor_ip[0]].k) 
										#print '(k_value <= k + 1 ):', (k_value <= k + 1 )
										killProcess = True
										"""
								#except IndexError:
									#print 'Tried to access a nonextistent index'
									#print 'len(thisY) = ', len(thisY), 'and tried to access k = ', k_value, 'whle this ders k =', k
									
									
						#except Exception as e:
							#print "Caught exception in parsing messages: ", e
							pass
							"""

					#data = int(splitData[len(splitData) - 1])					#in case multiple values were concatenated in the input buffer, split it up and use the most recently sent value
				#if data END
				else:  #if no data is received, end the connection and close the process
					#no data
					#print 'Socket ', neighbor_ip, 'is unresponsive, closing connection and shutting down.' 
					killProcess = True
		#END receiving block

		#timer checks
		if GO: 
			if SEND_GO:
				startTime = time.time()
			endTime = time.time()
			if endTime- startTime >= time_limit:
				END_INNER = True

		#message sending
		for s in writable:
			if GO:	
				if SEND_GO:
					s.send(":" + goMessage)
					#print 'Sending GO signal to ', s.getpeername()
				elif END_INNER:
					#print 'Sending END_INNER signal to ', s.getpeername()
					s.send(":" + endMessage)
					continue
				send_mssg = str(t) + "/" + str(k) + "/" + str(thisY[k]) + "/"  + str(thisZ[k])
				send_mssg = ":" + send_mssg	
				#print 'Sending ', send_mssg, ' to ', s.getpeername()
				s.send(send_mssg)
				outputs.remove(s)
			elif SEND_NO_GO:
				#print 'Sending NO_GO'
				s.send(":" + noGoMessage)
		#End sending loop
		SEND_NO_GO = False
		SEND_GO = False


		syncCounter = 0
		#check if we have updated timestamps from every neighbor
		for key, neigh in neighbors.items():
			if neigh:
				if (neigh.k >= k):
					syncCounter += 1
					##print "sync count incremented to ", syncCounter, ". K will increment when it is ", len(neighbor)

		if syncCounter == len(neighbors):
			thisY[k + 1] = thisY[k + 1]/float(len(neighbors) + 1)				#perform the rc calculations
			thisZ[k + 1] = thisZ[k + 1]/float(len(neighbors) + 1)				#perform the rc calculations
			k += 1
			thisY[k + 1] += (thisY[k]) 																	#add the next value
			thisZ[k + 1] += (thisZ[k]) 																	#add the next value

			for key,neigh in neighbors.items():
				outputs.append(neigh.sock)
		elif syncCounter > len(neighbors):
			#print 'ERROR: syncCount greater than number of neighbors.'
			#print 'syncCount = ', syncCounter
			#print 'num of neighbors = ', len(neighbors)
			killProcess = True 


		#Error catching code block
		for s in exceptional:
			#print 'Socket', s.getpeername(), ' is throwing errors, turning it off and shutting down process'
			killProcess = True

		#reset all of our variables -- later this will include the ratio-consensus variables
		#code block checks to see if k needs to be incremented
			#thisY[k + 1] should now have the summation of all neighbors y[k] values, time to divide by the number of neighbors + 1
						#allconnected check

		#End processes check
		if killProcess:		
			for s in inputs:
				inputs.remove(s)
				if s in outputs:
					outputs.remove(s)
				neighbors[s.getpeername()[0]].close()
				#NOTE: does s still exist? Is it a copy of the socket stored in the data structure? Test this or look it up
			recvsocket.close()
			break
		#killprocess

	g_star = g_min + (thisY[k]/thisZ[k])*(g_max - g_min)
	outFile.write("t = " + str(t) + "; k = " + str(k) + "; y[k] = " + str(thisY[k]) + "; z[k] = " + str(thisZ[k]) + "; g_star = " + str(g_star) + "\n")
	#print 'Ending t = ', t , ' with k = ', k
	#print 'We have averaged the values to be ', thisY[k - 1]
	#print 'Start time = ', startTime-start, 'seconds from start of outer loop'
	#print 'EndTime = ', endTime - start, ' seconds'
	#print 'time elapsed = ',  endTime - startTime, ' seconds'
	t += 1
	if killProcess:
		break
	#Outer loop

#output final time stamps (Debugging)
#print 'k for this machine ', THIS_IP, ': ', k

