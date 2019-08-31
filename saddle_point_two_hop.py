#!/usr/bin/env python
#Saddle Point -- Two-hop version
#Takes information from both neighbors and neighbors of neighbors in order to reach a solution
#Faster than single hop by a factor of ~10
#USAGE: ./saddle_point_two_hop graphs/graph_structure.txt referenceFiles/signal_file.CSV
#Programmer: Cole W Tynan-Wood
#Credit to Priyank Srivastava and Tor Anderson for providing all of the math and much assistance in creating
#this program. Contact me at (910) 859-1660 if you have questions about how any of this works.

import select
import socket
import Queue
import sys
import time
import fcntl
import struct
import csv

DEBUG = True
#class to house information about the neighbors of the PI
class Neighbor:

	#overloaded initializer for specified socket (socket can be set as zero, same thing as unspecified
	def __init__(self, theSocket):
		self.k = -1
		self.sock = theSocket
		self.ready = False
		self.isOpenBool = False
		if theSocket:
			self.isOpenBool = True
		self.th = False
		self.oh = False
		self.numPaths = 0				#Number of two-step paths to this neighbor (only applies if two steps away)

	#create or change the socket for a neighbor object
	def makeSock(self, newSock):
		self.sock = newSock
		self.isOpenBool = True
	
	#Set the neighbor to be ready to send or recv from
	def setReady(self, flag):
		try:
			if type(flag) is not bool:
				raise TypeError('WRONG TYPE')
			self.ready = flag
			return True
		except TypeError as e:
			print >>sys.stderr, 'ERROR: wrong type given to setReady()'
			return False

	def isOpen(self):
		return self.isOpenBool

	def isReady(self):
		return self.ready
	
	def setOneHop(self):
		self.oh = True

	def isOneHop(self):
		return self.oh
	#sets the boolean that indicated whether this neighbor is a neighbor of a neighbor
	def setTwoHop(self):
		self.th = True

	#return true if this neighbor is a neighbor of a neighbor
	def isTwoHop(self):
		return self.th

	#Reset k value for neighbor and indicate that it is not ready to interact with
	def reset(self):
		self.k = -1
		self.ready = False

	#closes the socket encased by the neighbor object and sets status to off
	def closeSock(self):
		sock.close()
		self.isOpenBool = False
#Neighbor class

#calculate the derivate of a simple a*x^b polynomial (mononomial i guess) given x and return numerical output
def costFuncPrime(x, a, b):
	return float((a*b)*(x**(b - 1.0)))

#returns true if all neighbors in a dictionary of neighbor objects are open or they have been created
def all_true(dict):
	allGood = True
	for s,v in dict.items():
		if not v.isOpen():
			allGood = False
	return allGood
#all_true for lists

#function that checks that the dictionary of neighbors is fully populated and displays output (purely to reduce bloat later in program)
def all_have_connected(dict):
	allGood = all_true(dict)
	if allGood:
				print 'all have connected!'
				print 'Connected neighbors:'
				for v,n in dict.items():
					print v
					pass
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

#parameters for iteration
time_limit = 3.0															#Time limit in seconds
rest_time = 1.0																#time between outer loop iterations
step_size = 0.01															#can play with this value a little

#loop variables and messages
goMessage = "GO"				#message that is received and sent, indicating that sending and receving of data should begin
noGoMessage = "NO_GO"		#message that is sent by a Pi that is not yet fully connected, indicating a shutdown of the system of Pis should begin
endMessage = "END"			#message sent when inner loop ends, indicates to other Pis to stop receiving 
stopMessage = "STOP"		#message send by the timer initially, that will propogate and stop the calculations after a certain amount of time
#FORMAT = "FORMAT = python saddle_point_two_step.py info_about_der.txt pr_values.csv OR leave blank for defaults" #This is outdated

#use this socket to receive the incoming connections
recvsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#bind the receiving socket to this ip
while True:
	try:
		THIS_COMP = (THIS_IP, PORT)
		print 'Attempting to create receiving socket:', THIS_COMP
		recvsocket.bind(THIS_COMP)
		break
	except Exception as e:
		print "Failed to create receiving socket: ", e
		print "Retrying...\n"
		time.sleep(1)

recvsocket.setblocking(0)
recvsocket.listen(0)
#Pass the program the file containing all the information about itself (gmin, gmax, neighbors, etc) as first param, data file with pr as second
#to every PI be default, or maybe accessible remotely by the PI iff it is a member of I.

#file where static information about the pi is located
infoFileName = '/home/pi/graphs/info.txt'

#Read the info for this specific DER
#specifies gmin, gmax, if the DER is in I, etc. 
#FORMAT: g_min g_max In_I_bool(0 or 1) |I| is_timer(1/0) costFunctionScalar(some integer > 1) costFunctionExponent(even integer > 1)

with open(infoFileName) as infoFile:
	info = infoFile.readline()
	info = info.split()
	g_min = float(info[0])
	g_max = float(info[1])
	inI = False
	isTimer = False
	if int(info[2]) != 0:
		inI = True
	sizeOfI = int(info[3])
	if int(info[4]) != 0:
		isTimer = True
	scalar = float(info[5])
	exp = float(info[6])

if DEBUG:
	print 'inI = ', inI
	print 'isTimer = ', isTimer

#the step size h is declared here 
try:
	neighFileName = sys.argv[1] 
except:	#default value assigned if nothing passed to program (four pi setup in ring structure)
	neighFileName = 'graphs/hook.txt'

try: 
	neighFile = open(neighFileName)
except: 
	print "Invalid neighbor file, check name and retry"
	exit(0)

 #We start by seeking out neighbors. some fail to accept connections, we wait for them to come online

numAgents = neighFile.readline()			#NOT USED, just need to get the file iterator to the right place
numAgents = int(numAgents.split('\n')[0])

#dictionary of neighbor objects
neighbors = {}

for line in neighFile:
	newsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		line = line.rstrip('\n')
		newsock.connect((pidb[line],PORT))
		print 'Connection successful with', newsock.getpeername()
		neighbors[pidb[line]] = Neighbor(newsock)
	except Exception as e:
		print 'Connection failed with IP', pidb[line]
		neighbors[pidb[line]] = Neighbor(False)
	neighbors[pidb[line]].setOneHop()

#parse the filename to get the nighbor-neighbor file
NNSplit = neighFileName.split('/')
NNFileName = 'graphs/two_hop/' + NNSplit[1]
try: 
	NNFile = open(NNFileName)
except: 
	print "Invalid two-hop file, check name and retry"
	exit(0)

numNeighbors = len(neighbors)


#Fill out neighbors of neighbors and connect to any that are on and listening
for line in NNFile:
	line = line.split()			#FORMAT of line: two_hop_neighbor(Ri) num_paths(some int)
	# line[0] : the code for the two-hop neighbor in question (R1, R2, etc), line[1] : the number of paths to this two-hop neighbor
	if pidb[line[0]] not in neighbors:
		try:
			newsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			newsock.connect((pidb[line[0]],PORT))
			neighbors[pidb[line[0]]] = Neighbor(newsock)
			if DEBUG:
				print 'Connection successful with neighbor of neighbor', newsock.getpeername()
		except Exception as e:
			if DEBUG:
				print 'Connection failed with IP', pidb[line[0]]
				print e
			neighbors[pidb[line[0]]] = Neighbor(False)
	neighbors[pidb[line[0]]].setTwoHop()		#set the two-hop flag
	neighbors[pidb[line[0]]].numPaths = int(line[1])
				
numAllNeighbors = len(neighbors)
#Parse signal file
try:
	signalFileName = sys.argv[2]
except: 
	#if inI:
	signalFileName = 'referenceSignals/reg-d-abridged.CSV'
#	else:
		#pass

# ~~ Read the reference signal file ~~~
pr = list()				#The list of reference signal values, indexes indicate time-intervals
vConst = 1.0/float(numAgents)

tmax = 0					#Maximum number of time intervals (outer loop) that will be determined by reading the signal input file
with open(signalFileName) as pr_input_file:
	csv_reader = csv.reader(pr_input_file, delimiter=',')
	for row in csv_reader:
		pr.append(float(row[1]))
		tmax += 1

#Init lists, counters, and iteration limits
t = 1																					#iterator for outer loop 
allConnected = all_have_connected(neighbors)	#returns true if all neighbors have connected
thisX = list()						#x - values
thisZ = list()						# z - values
thisL = list()						#lambda values
xDot = list()							#
zDot = list()
lDot = list()
#the lists for inputting sockets to select
inputs = [ recvsocket ]
outputs = [ ]
exceptional = [ ]
	
#add all available sockets to the inputs list
for k, v in neighbors.items():
	if v.isOpen():
		v.sock.setblocking(0)
		inputs.append(v.sock)

#MAIN LOOP: Here we will take input and send output to all neighbors
with open('output.CSV', 'w+') as output_file:
	out_writer = csv.writer(output_file, delimiter=',')

	while t <= tmax:	
		k = 0
		startTime = 0
		endTime = 0
		for key,neigh in neighbors.items():
			if neigh.isOpen():
				neigh.reset()
				if neigh.sock not in outputs:
					outputs.append(neigh.sock)
		SEND_GO = False
		SEND_NO_GO = False
		GO = False
		KILLP = False
		STOP = False

		#Saddle-Point Dynamics initialization of variables
		del thisX[:]
		del thisZ[:]
		del thisL[:]
		del xDot[:]
		del zDot[:]
		del lDot[:]
		thisX = [0.0]*100000
		thisZ = [0.0]*100000
		thisL = [0.0]*100000
		xDot = [0.0]*100000
		zDot = [0.0]*100000
		lDot = [0.0]*100000

		readyToAdvance = False
		RESET = False
		

		while not STOP:	
			#Checking if time-limit has been reached yet (if the timer) and 
			if GO and isTimer and not SEND_NO_GO:
				endTime = time.time()
				if endTime - startTime >= time_limit:
					STOP = True

			readable, writable, exceptional = select.select(inputs, outputs, inputs, 0)			#see which sockets are ready to be written to, read from, and which are throwing exceptions

			
			if isTimer and not GO and allConnected:
				if DEBUG:
					print 'Timer is setting GO flag and SEND_GO flag'
				time.sleep(rest_time)
				startTime = time.time()
				SEND_GO = True
				GO = True

			# ~~~ Message Parsing ~~~
			for s in readable:
				if s is recvsocket:						#if we have a new connection, then accept it and add it to database of connected neighbors and check if all have connected
					conn, client_address = s.accept()
					print >>sys.stderr, 'new connection with ', client_address, ' established'
					conn.setblocking(0)
					neighbors[client_address[0]].makeSock(conn)
					inputs.append(conn)	
					outputs.append(conn)
					
					allConnected = all_true(neighbors)
					if allConnected:
						if DEBUG:
							print "All connected."
							print "Immediate neighbors:"
							for s,v in neighbors.items():
								if not v.isTwoHop():
									print s
							print "Neighbors of Neighbors:"
							for s,v in neighbors.items():
								if v.isTwoHop():
									print s

				else:				#If the connection is not a new connection then process the data received from this neighbor
					neighbor_ip = s.getpeername()
					data = s.recv(1024)
					if data:
						if DEBUG:
							print 'received ', data, ' from ', neighbor_ip

						#Split input up by message separator. 
						dataSplit = data.split(':')
						for message in dataSplit:
							#Format of message after split: t_value[0] k_value[1] x_value[2] z_value[3] l_value[4]
							message = message.split('/')
							if message[0] == noGoMessage:
								if DEBUG:
									print 'received NOGO from ', neighbor_ip
								neighbors[neighbor_ip[0]].setReady(False)
								if GO:
									GO = False
									SEND_NO_GO = True
							elif message[0] == goMessage:							#GO flag received, now we can immediately begin performing ratio consensus
								if DEBUG:
									print 'received GO from ', neighbor_ip
								neighbors[neighbor_ip[0]].reset()
								neighbors[neighbor_ip[0]].setReady(True) 
								
								if not GO and not SEND_NO_GO:
									if allConnected:
										GO = True
										SEND_GO = True
										startTime = time.time()
									else:
										if DEBUG:
											print 'NO_GO flag set'
										SEND_NO_GO = True
							elif message[0] == stopMessage:				#if Received STOP message, we can stop processing messages and propogate the STOP signal
								if int(message[1]) == t:
									STOP = True
									neighbors[neighbor_ip[0]].setReady(False)
							elif message[0] == '':
								pass

							elif neighbors[neighbor_ip[0]].isReady():									#if this neighbor has sent the GO flag, we will start reading its input
								t_value = int(message[0])
								k_value = int(message[1])
								x_value = float(message[2])
								z_value = float(message[3])
								l_value = float(message[4])
								d_value = float(message[5])

								try:
									if (t_value == t):
										if (k_value > neighbors[neighbor_ip[0]].k) and (k_value <= k + 1 ):
											neighbors[neighbor_ip[0]].k = k_value
											if not SEND_NO_GO and allConnected:
												if neighbors[neighbor_ip[0]].isOneHop():
													xDot[k_value] += z_value
													zDot[k_value] += l_value + x_value + (float(numNeighbors) + d_value)*z_value - float(pr[t-1])*float(vConst)
													lDot[k_value] -= z_value
												if neighbors[neighbor_ip[0]].isTwoHop():
													zDot[k_value] -= float(neighbors[neighbor_ip[0]].numPaths) * z_value
										else:
											KILLP = True
											if DEBUG:
												print "Out of sync at k = ", k, ", read ", k_value, "from ", neighbor_ip
												print 'The neighbors current value of k:', neighbors[neighbor_ip[0]].k
												print 'k_value > neighbors[neighbor_ip[0]].k): ', (k_value > neighbors[neighbor_ip[0]].k) 
												print '(k_value <= k + 1 ):', (k_value <= k + 1 )
									elif t < t_value:
										if DEBUG:
											print 'We have a neighbor on a higher t: ', neighbor_ip, ' with neighbor t = ', t_value, ' and our t: ', t
											print 'The neighbors current value of k:', neighbors[neighbor_ip[0]].k
											print 'k_value > neighbors[neighbor_ip[0]].k): ', (k_value > neighbors[neighbor_ip[0]].k) 
											print '(k_value <= k + 1 ):', (k_value <= k + 1 )
										neighbors[neighbor_ip[0]].messages.put_nowait(data)
								except IndexError:
									print 'Tried to access a nonextistent index'
									print 'len(thisX) = ', len(thisX), 'and tried to access k = ', k_value, 'whle this ders k =', k
									pass
																			
						#if data END
					else:  #if no data is received, end the connection and close the process
						print 'Socket ', neighbor_ip, 'is unresponsive, closing connection and shutting down.' 
						KILLP = True
			#END receiving block

			#Send NO_GO and then reset the pi, if SEND_NO_GO flag is set
			if SEND_NO_GO:
				for ip, neigh in neighbors.items():
					if neigh.isOpen():
						print 'Sending NO_GO to ', ip
						neigh.sock.send(":" + noGoMessage)
				RESET = True
				break

			#Sending messages and flags
			for s in writable:
				if GO:	
					if SEND_GO:
						s.send(":" + goMessage)
						if DEBUG:
							print 'Sending GO signal to ', s.getpeername()
					send_mssg = str(t) + "/" + str(k) + "/" + str(thisX[k]) + "/" + str(thisZ[k]) + "/" + str(thisL[k]) + "/" + str(numNeighbors)
					send_mssg = ":" + send_mssg	
					if DEBUG:
						print 'Sending ', send_mssg, ' to ', s.getpeername()
					try:
						s.send(send_mssg)
					except:
						#this socket has disconnected
						KILLP = True
						break
					outputs.remove(s)
			#End sending loop
			SEND_GO = False

			#Time's up, light the beacon of Gondor
			if STOP:
				for key,neigh in neighbors.items():
					if neigh.isOpen():
						if DEBUG: 
							print 'Sending STOP to ', neigh.sock.getpeername()
						neigh.sock.send(":" + stopMessage + "/" + str(t))

			#check if we have updated timestamps from every neighbor for current k
			syncCounter = 0
			for key, neigh in neighbors.items():
				if neigh.isOpen():
					if (neigh.k >= k):
						syncCounter += 1		

			if syncCounter == numAllNeighbors:
				xDot[k] -= costFuncPrime(thisX[k], scalar, exp) + thisL[k] + thisX[k] - float(numNeighbors)*thisZ[k] + pr[t - 1]*vConst
				zDot[k] -= (float(numNeighbors))*(thisL[k] + thisX[k] - pr[t - 1] * vConst + thisZ[k] * (1.0 + float(numNeighbors)))
				lDot[k] += thisX[k] + float(numNeighbors)*thisZ[k] - pr[t-1]*vConst

				thisX[k + 1] = thisX[k] + xDot[k]*step_size				
				thisZ[k + 1] = thisZ[k] + zDot[k]*step_size		
				thisL[k + 1] = thisL[k] + lDot[k]*step_size	

				#ensure that x is within the bounds
				if thisX[k + 1] < g_min:
					thisX[k + 1] = g_min
				elif thisX[k + 1] > g_max:
					thisX[k + 1] = g_max

				k += 1
				for key,neigh in neighbors.items():
					if neigh.sock not in outputs:
						outputs.append(neigh.sock)
				
			elif syncCounter > numAllNeighbors:
				print 'ERROR: syncCount greater than number of neighbors.'
				print 'syncCount = ', syncCounter
				print 'num of (all) neighbors = ', numAllNeighbors
				KILLP = True 

			#Error catching code block
			for s in exceptional:
				print 'Socket', s.getpeername(), ' is throwing errors, turning it off and shutting down process'
				KILLP = True

			#End processes check
			if KILLP:		
				for s in inputs:
					inputs.remove(s)
					if s in outputs:
						outputs.remove(s)
					try:
						neighbors[s.getpeername()[0]].close()
					except:
						pass
				recvsocket.close()
				break
			#killprocess

		if DEBUG:
			print 'Ending t = ', t , ' with k = ', k
			#print 'We have averaged the values to be ', thisX[k - 1]
			print 'time elapsed = ',  endTime - startTime, ' seconds'
		if RESET:
			t = 1
		else:
			out_writer.writerow([str(t), str(k), str(thisX[k-1]), str(thisZ[k-1]), str(thisL[k-1])])
			t += 1

		#break out of outer loop if kill process flag is set
		if KILLP:
			break
		#Outer loop

if KILLP:
	print 'Had fatal error for this machine at k = ', k
if DEBUG:
	print 't for machine ', THIS_IP, ': ', t

