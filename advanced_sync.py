import socket
import sys
import Queue
import time
import fcntl
import struct

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
lodb = 	{'R1': "127.0.0.1",
		 'R2': "127.0.0.1",
		 'R3': "127.0.0.1",
		 'R4': "127.0.0.1"
		}


#dictionary of neighbor sockets
neighbors = {}
inputFile = "./neighbors/" + sys.argv[1] 

f = open(inputFile)

#code block parses the neighbors input file. Change the lodb to pidb when actually implementing
#initial probing for neighboring pis, if not found the program will simply continue on and wait for a connection

for line in f:
	newsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		line = line.rstrip('\n')
		newsock.connect((lodb[line],PORT))
		print 'Connection successful with', newsock.getpeername()
		neighbors[lodb[line]] = newsock
	except Exception as e:
		print 'Connection failure: ', e


#use this socket to receive the incoming connections
recvsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#bind the receiving socket to this ip, and cycle through ports until ones available
while True:
	try:
		recvsocket.bind((THIS_IP, PORT))
		break
	except:
		PORT = PORT + 1
		print PORT

input = [ recvsocket ]
output = [ ]
exceptional = [ ]
#We start by seeking out neighbors. some fail to accept connections, we wait for them to come online


