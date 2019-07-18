#Advanced Sync: Handles synchronization between a variable network of RPis. Can specify the 
#neighbors of the machine by passing an input file containing all the neighbors via the command line.


import select
import socket
import sys
import Queue
import time
import fcntl
import struct

def all_true(dict):
	allGood = True
	for s,v in dict.items():
		if  not v:
			allGood = False
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
PORT = 10000 
THIS_IP = get_ip_address('eth0')
#local database, using ports to simulate different devices

#dictionary of neighbor sockets
neighborSock = {}
#dictionary of booleans

inputFile = "./neighbors/" + sys.argv[1] 
f = open(inputFile)

#code block parses the neighbors input file. Change the lodb to pidb when actually implementing
#initial probing for neighboring pis, if not found the program will simply continue on and wait for a connection

allConnected = True
for line in f:
	newsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		line = line.rstrip('\n')
		newsock.connect((pidb[line],PORT))
		print 'Connection successful with', newsock.getpeername()
		neighborSock[pidb[line]] = newsock
	except Exception as e:
		print 'Connection failure: ', e
		neighborSock[pidb[line]] = 0
		allConnected = False


#use this socket to receive the incoming connections
recvsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#bind the receiving socket to this ip, and cycle through ports until ones available
while True:
	try:
		THIS_COMP = (THIS_IP, PORT)
		print 'Attempting to create socket at', THIS_COMP
		recvsocket.bind(THIS_COMP)
                break
	except Exception as e:
		print "We've got a problem: ", e
		exit(0)

recvsocket.setblocking(0)
recvsocket.listen(3) #scale later?

inputs = [ recvsocket ]
outputs = [ ]
exceptional = [ ]

for k, v in neighborSock.items():
    if v:
	v.setblocking(0)
	inputs.append(v)
#We start by seeking out neighbors. some fail to accept connections, we wait for them to come online


k = 0
while inputs:
	print >>sys.stderr, 'Waiting for neighbors to chime in'
	readable, writable, exceptional = select.select(inputs, outputs, inputs)
	
	for s in readable:
		if s is recvsocket:
			conn, client_address = s.accept()
			print >>sys.stderr, 'new connection with ', client_address, ' established'
			conn.setblocking(0)
			neighborSock[client_address] = conn
			inputs.append(conn)	
			for s,v in neighborSock.items():
				print v.getpeername()
			if all_true(neighborSock):
				allConnected = True
				print 'all have connected!'
				print 'Connected neighbors:'
				for v,n in neighborSock.items():
					print n.getpeername()

		else:
			data = s.receive(1024)
			
									#handle checking that the iteration is correct
#TODO: handle new data from neighbors if all of the neighbors are connected

