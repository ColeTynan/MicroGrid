import socket
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

# in future implementation, perhaps use input  files to define relationships
# IDEA: create class for dealing with neighboring pis, to determine which go first and whatnot
# will need to use multithreading to deal with several pis communicating with each other at once
# may need to create a priority queue of some kind to determine in what order the pis will be talking

#handshake with neighbor
def handshake(outsock, insock ):        #add functionality to take a socket as input to generalize
    print "Attempting handshake..."
    while True:
        print "Sending initial probe."
        outsock.sendto(HNDSHK_MSSG_GIVE, (N_IP, UDP_PORT))   #sends initial probing message to other pi
        try:
            recvMess, addr = sockin.recvfrom(1024)          #waits for a message
            print "received a message.."
            if recvMess == HNDSHK_MSSG_GIVE:              #if message is first contact, send return message
                sockout.sendto(HNDSHK_MSSG_RECV, (N_IP, UDP_PORT))  #Sending confirmation of mssg received
                print "message received is initial probe, returning handshake"
                break 
            elif recvMess == HNDSHK_MSSG_RECV:            #get confirmation fo receipt from other pi
                print "Message received was response to handshake, connection established"
                PHP = True                                  #this pi will have priority
                break
        except socket.timeout:
            "No response received, resending query"
            continue

    print "Handshake complete." 

#code begins
#generalize IP address and neighbor building
#FORMAT OF INPUT FILE
# each line contains the ip address of a neighbor

print "Reading IP addresses of all neighbors"


N_IP = "169.254.142.58" #neighbors ip address
MY_IP = get_ip_address('eth0')    #this pi's ip address
UDP_PORT = 5005
HNDSHK_MSSG_GIVE = "0"      #message sent when initially probing for raspberry pi
HNDSHK_MSSG_RECV = "1"      #message sent when responding to message from other pi
PHP = False                 #Pi Has Priority : if true this pi will go first in exchanging messages


sockout= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sockin = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sockin.settimeout(5.0)

sockin.bind(( MY_IP, 5005)) #bind the receiving socket with the ip address and port


handshake(sockout)

for t in range(0, 10):  #the time intervals t
    while True:
        try:
            sockout.sendto(str(t), (N_IP, UDP_PORT))
            message, addr = sockin.recvfrom(1024)
            print "For t = " + str(t)
            if int(message) == t: 
                print "Synced, incoming: " + message
            else: 
                print "Not synced: " + message
            break;
        except socket.timeout:
            print "No message received, resending messages"
            continue
        









