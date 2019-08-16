#aaatio Consensus (and later, optimization as well): handles synchronization between a variable network of rpis. takes an input file as a commmand line param, which houses the labels (e.g. r1\n r2) of the neighbors
#neighbors of the machine by passing an input file containing all the neighbors via the command line.
#todo: think of edge cases (e.g. different graph structures, varying input values, etc.) and test these as well

import select
import socket
import Queue
import sys
import time
import fcntl
import struct
import csv
#TODO: Consider adding argparse to handle cmd line options such as -d for debugging

DEBUG = False
#class to house information about the neighbors of the PI
class Neighbor:
	def __init__(self, theSocket):
		self.k = -1
		self.sock = theSocket
		self.ready = False
		self.isOpen = True
		self.messages = Queue.Queue()
		#TODO: figure out a queue method for handling messages maybe

	def setReady(self, flag):
		try:
			if type(flag) is not bool:
				raise TypeError('WRONG TYPE')
			self.ready = flag
			return True
		except TypeError as e:
			print >>sys.stderr, 'ERROR: wrong type given to setReady()'
			return False

	def isReady(self):
		return self.ready
	
	def reset(self):
		self.k = -1
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

#loop variables and messages
tmax = 0 								#Maximum number of time intervals (outer loop) that will be determined by reading the signal input file
t = 1										#iterator for outer loop TODO: have this be a parameter read from a file
goMessage = "GO"				#message that is received and sent, indicating that sending and receving of data should begin
noGoMessage = "NO_GO"		#message that is sent by a Pi that is not yet fully connected, indicating a shutdown of the system of Pis should begin
endMessage = "END"			#message sent when inner loop ends, indicates to other Pis to stop receiving 
stopMessage = "STOP"		#message send by the timer initially, that will propogate and stop the calculations after a certain amount of time
FORMAT = "FORMAT = python ratio_consensus_dist.py info_about_der.txt pr_values.csv OR leave blank for defaults"

#dictionary of neighbor objects
neighbors = {}

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
#NOTE: Consider the question: If only one node actually physically receives Pr, then should every node have access to it? That is, should the input file for Pr be given
#to every PI be default, or maybe accessible remotely by the PI iff it is a member of I.

try:
	infoFileName = sys.argv[1] 
except:	#default value assigned if nothing passed to program (four pi setup in ring structure)
	infoFileName = '/home/pi/graphs/ring4.txt'

infoFile = open(infoFileName)

#TODO: set up parsing for information in data file about the DER (if its in I, gmin, gmax, etc) for simplified, just if its the "timer" or not

#Read the info for this specific DER
#specifies gmin, gmax, if the DER is in I, etc. 
#FORMAT: g_min g_max In_I_bool(0 or 1) |I| is_timer(1/0) num_in_grid(integer)
try:
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
	num_in_grid = int(info[5])
except Exception as e:
	print e
	print "Check input file is correct"
	exit(0)

if DEBUG:
	print 'inI = ', inI
	print 'isTimer = ', isTimer

try:
	signalFileName = sys.argv[2]
except: 
	#if inI:
	signalFileName = 'reg-d-abridged.CSV'
#	else:
		#pass

#TODO: in Ratio Consensus, in the case of multiple DERs in I, there needs to be a method of deciding which DER will be the timer
#Probably would be best to just decide in the input file instead of implementing a convoluted method of deciding which will take the lead

#if in I, read the input CSV file (NOTE: maybe make this a command line argument to test in future with much smaller data sizes?)

#the step size h is declared here TODO: if this approach fails to get good results, need to find a way to share the max degree of the grid to all the agents
step_size = 1.0/float(num_in_grid - 1)

 #We start by seeking out neighbors. some fail to accept connections, we wait for them to come online
for line in infoFile:
	newsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		line = line.rstrip('\n')
		newsock.connect((pidb[line],PORT))
		print 'Connection successful with', newsock.getpeername()
		neighbors[pidb[line]] = Neighbor(newsock)
	except Exception as e:
		print 'Connection failed with IP', pidb[line]
		neighbors[pidb[line]] = 0


pr = list()
with open(signalFileName) as pr_input_file:
	csv_reader = csv.reader(pr_input_file, delimiter=',')
	for row in csv_reader:
		pr.append(float(row[1]))
		tmax += 1


#TODO: implement the new version of ratio-consensus
time_limit = 1.0															#Time limit in seconds
numNeighbors = len(neighbors) + 1							#TODO: for new implementation of RC we dont use ourselves in the number of neighbors(???) Verify
allConnected = all_have_connected(neighbors)
thisY = list()
thisZ = list()

inputs = [ recvsocket ]
outputs = [ ]
exceptional = [ ]
	
for k, v in neighbors.items():
	if v:
		v.sock.setblocking(0)
		inputs.append(v.sock)

with open('output.CSV', 'w+') as output_file:
	out_writer = csv.writer(output_file, delimiter=',')
	#initialize y and z values
	#open output file
	if DEBUG:
		print 'Starting timer...'

	start = time.time()

	#booleans and counters
	#our i/o while loop 
	while t <= tmax:	#NOTE: Have this determined by the input file? Either send tmax with GO flag if inI or have it be some hardcoded param for now?
		k = 0
		RESET = True
		startTime = time.time()
		endTime = startTime
		END_INNER = False			#NOTE: Does nothing really of any significance, recommend removal
		STOP = False

		#initialize our y and z values
		initZ = g_max - g_min
		initY = 0.0
		if inI:
			initY = (pr[t]/float(sizeOfI)) - g_min
		else: 
			initY = - g_min

		while not STOP:	
			#Resets all the flags and whatnot
			if RESET:																
				if DEBUG:
					print 'resetting'
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
				STOP = False
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
			if GO and isTimer and not SEND_NO_GO:
				endTime = time.time()
				if endTime - startTime >= time_limit:
					STOP = True
			
			readable, writable, exceptional = select.select(inputs, outputs, inputs, 0)			#see which sockets are ready to be writting, read from and which are throwing exceptions
			#resetting the whole thing
		
			if isTimer and not GO and allConnected:
				if DEBUG:
					print 'Timer is setting GO flag and SEND_GO flag'
				time.sleep(time_limit)
				startTime = time.time()
				SEND_GO = True
				GO = True

			# ~~~ Message Parsing ~~~
			for s in readable:
				if s is recvsocket:						#if we have a new connection, then accept it and add it to database of connected neighbors and check if all have connected
					conn, client_address = s.accept()
					print >>sys.stderr, 'new connection with ', client_address, ' established'
					conn.setblocking(0)
					neighbors[client_address[0]] = Neighbor(conn)
					inputs.append(conn)	
					outputs.append(conn)
					allConnected = all_have_connected(neighbors)
				else:
					neighbor_ip = s.getpeername()
					data = s.recv(1024)
					if data:
					#if the timestamp for this is not a duplicate, save it
						if DEBUG:
							print 'received ', data, ' from ', neighbor_ip
						#Split input up by message separator. 
						dataSplit = data.split(':')
						for message in dataSplit:
							#Format of message after split: t_value[0] k_value[1] y_value[2] z_value[3] 
							#try: 
								message = message.split('/')
								if DEBUG:
									print 'received ', message, 'from ', neighbor_ip
								if message[0] == noGoMessage:
									if DEBUG:
										print 'received NOGO from ', neighbor_ip
									neighbors[neighbor_ip[0]].setReady(False)
									if GO:
										GO = False
										RESET = True
										SEND_NO_GO = True
								elif message[0] == goMessage:							#GO flag received, now we can immediately begin performing ratio consensus
									if DEBUG:
										print 'received GO from ', neighbor_ip
									neighbors[neighbor_ip[0]].reset()
									neighbors[neighbor_ip[0]].setReady(True) 
									
									if not GO:
										if allConnected:
											GO = True
											SEND_GO = True
											startTime = time.time()
										else:
											if DEBUG:
												print 'NO_GO flag set'
											SEND_NO_GO = True
									#endCtr += 1
									#if endCtr == len(neighbors):
									#	pleaseContinue = True
									#TODO: figure out a way to handle neighbors getting ahead or behind with the iteration
								elif message[0] == stopMessage:				#if Received STOP message, we can stop processing messages and propogate the STOP signal
									if int(message[1]) == t:
										STOP = True
										neighbors[neighbor_ip[0]].setReady(False)
								elif message[0] == '':
									pass

								elif neighbors[neighbor_ip[0]].isReady():									#if this neighbor has sent the GO flag, we will start reading its input
									t_value = int(message[0])
									k_value = int(message[1])
									y_value = float(message[2])
									z_value = float(message[3])

									try:
										if (t_value == t):
											if (k_value > neighbors[neighbor_ip[0]].k) and (k_value <= k + 1 ):
												neighbors[neighbor_ip[0]].k = k_value
												if not SEND_NO_GO and allConnected:
													thisY[k_value + 1] += y_value 
													thisZ[k_value + 1] += z_value 
											else:
												killProcess = True
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
										print 'len(thisY) = ', len(thisY), 'and tried to access k = ', k_value, 'whle this ders k =', k
										pass
																				

						#if data END
					else:  #if no data is received, end the connection and close the process
						#no data
						print 'Socket ', neighbor_ip, 'is unresponsive, closing connection and shutting down.' 
						killProcess = True
			#END receiving block

			"""
			if pleaseContinue:
				if DEBUG:
					print 'if continue block reached, breaking at t = ', t
				break
			"""

			#timer checks
					#message sendin
			for s in writable:
				if SEND_NO_GO:
					if DEBUG: 
						print 'Sending NO_GO'
					s.send(":" + noGoMessage)
				if GO:	
					if SEND_GO:
						s.send(":" + goMessage)
						if DEBUG:
							print 'Sending GO signal to ', s.getpeername()
					send_mssg = str(t) + "/" + str(k) + "/" + str(thisY[k]) + "/"  + str(thisZ[k])
					send_mssg = ":" + send_mssg	
					if DEBUG:
						print 'Sending ', send_mssg, ' to ', s.getpeername()
					s.send(send_mssg)
					outputs.remove(s)
			#End sending loop

			#Resetting flags
			SEND_NO_GO = False
			SEND_GO = False

			#Time's up, light the flame of Gondor
			if STOP:
				for key,neigh in neighbors.items():
					neigh.sock.send(":" + stopMessage + "/" + str(t))

			syncCounter = 0
			#check if we have updated timestamps from every neighbor
			for key, neigh in neighbors.items():
				if neigh:
					if (neigh.k >= k):
						syncCounter += 1			#NOTE: may be more scalable to do this while receiving data rather than separately 

			if syncCounter == len(neighbors):
				thisY[k + 1] = thisY[k + 1]*step_size + (1.0 - len(neighbors)*step_size)*thisY[k]				#perform the rc calculations
				thisZ[k + 1] = thisZ[k + 1]*step_size + (1.0 - len(neighbors)*step_size)*thisZ[k]		#perform the rc calculations
				k += 1
				#thisY[k + 1] += (thisY[k]) 																	#add the next value
				#thisZ[k + 1] += (thisZ[k]) 																	#add the next value

				for key,neigh in neighbors.items():
					if neigh.sock not in outputs:
						outputs.append(neigh.sock)
			elif syncCounter > len(neighbors):
				print 'ERROR: syncCount greater than number of neighbors.'
				print 'syncCount = ', syncCounter
				print 'num of neighbors = ', len(neighbors)
				killProcess = True 


			#Error catching code block
			for s in exceptional:
				print 'Socket', s.getpeername(), ' is throwing errors, turning it off and shutting down process'
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
					try:
						neighbors[s.getpeername()[0]].close()
					except:
						pass
				recvsocket.close()
				break
			#killprocess

		g_star = g_min + (thisY[k]/thisZ[k])*(g_max - g_min)
		out_writer.writerow([str(t), str(k), str(g_star)])

		if DEBUG:
			print 'Ending t = ', t , ' with k = ', k
			#print 'We have averaged the values to be ', thisY[k - 1]
			print 'Start time = ', startTime-start, 'seconds from start of outer loop'
			print 'EndTime = ', endTime - start, ' seconds'
			print 'time elapsed = ',  endTime - startTime, ' seconds'

		t += 1
		if killProcess:
			break
		#Outer loop

#output final time stamps (Debugging)
if killProcess:
	print 'Had fatal error for this machine at k = ', k
print 't for machine ', THIS_IP, ': ', t

