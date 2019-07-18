import select
import socket
import sys
import queue
import time

#======Start of Server Creation=====#
# Create a TCP/IP socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setblocking(0)

# Bind the socket to the port
server_address = ('169.254.86.232', 10001)
print ('starting up on %s port %s' % server_address, file=sys.stderr)
server.bind(server_address)

#Listen for incoming connections
server.listen(5)

#=====End of Server Creation=====#

#=====Start of Data Structure & Variable Initialization=====#
#Dict of IPs and their corresponding ports for the neighboring controllers
neighbors = {
    '169.254.142.58' : 10002
}

#SEP (Upper level protocol to how to receive bytes bigger than initial set size)
sep = '\n'
#Processed (Protocol for moving forward only when we receive this signal)
processed = '#####'

#Create dict between neighbors_ip mapping to true or false indication of processed status
neighborIPs_processed = {}

#Create own timestamp for this device
this_timestamp = 0

#Create a list of neighbors and their associated timestamp that we get
neighborIPs_timestamp = {}

#Create a dict of IPs corresponding to output sockets
IP_output_sockets = {}
#Create a dict of IPs corresponding to input sockets 
IP_input_sockets = {}

# Sockets to which we expect to write
outputs = []
# Sockets from which we read from
inputs = [ server ]

#For each corresponding ip/port, we create a new socket and connect to it
#The server is going to wait for a socket to become writable before sending any data
# Each output connection then needs a queue to act as a buffer for data to be sent through
# This buffer is in the form of {socket -> Queue[message1, message2, ... ]}
message_queues = {}

#Complete list of sockets to watch out for errors
totalSockets = inputs + outputs

#Variable used later to keep track of the total number of message received in an iteration
#Number of message rece
msg_received_count = 0

#=====End of Variable initialization=====#

#=====Start of Connection initialization with neighbors=====#
# Only runs once on startup
for ip_key, port_value  in neighbors.items():

    #Create new socket for the correpsonding ip_key and port
    server_address = (ip_key, port_value)
    new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #====Continually try to connect to the neighboring node using the socket we created====#
    new_socket.settimeout(10)
    while True:
        try:
            new_socket.connect(server_address)
            break
        except:
            print ("Connection Failed, on %s port %s, retrying in 0.5s" % server_address, file=sys.stderr)
            time.sleep(0.5)
    #====Successful Connection====#

    print( "Connection Success on %s port %s, continuing"
            % server_address, file=sys.stderr )

    #Give the connection a queue to contain data we want to send
    message_queues[new_socket] = queue.Queue()
    #In addition to connecting, we want to queue up the first 
    message_queues[new_socket].put(this_timestamp)

    #Set non-blocking for select
    new_socket.setblocking(0)
    
    #Match ip key to the new socket in the output dict
    IP_output_sockets[ip_key] = new_socket

    #Add to outputs list for select
    outputs.append(new_socket)
#=====End of Connection Initialization with neighbors=====#

# Debugs for output/input lists
#print(outputs, file=sys.stderr)
#print(inputs, file=sys.stderr)

#===== Main Program ====#
while inputs:

    readable, writable, exceptional = select.select(inputs, outputs, totalSockets)

    '''
    readable,writable,exceptional
        These are three lists -subsets of the contents of the lsits passed in
        Readable
            Incoming data buffered and are available to be read
        Writable
            Free space in their buffer and can be written to
        Exceptional
            Has an error
    '''

    '''
    ===Readable===
    #Handle inputs
    Cases:
    1) The socket is the main "server" socket, the one listening for connections
        then the "readable" condition means it is ready to accept another incoming
        connection.
            We also add the new connection to the list of inputs
    '''

    '''
    2) An established connection with a client that has sent data.
        The data is read with recv(), then placed on the queue so it can be sent through
            the socket and back to the client
    '''

    '''
    3) A readable socket without data available is from a client that has disconnected,
            and the stream is ready to be closed
    '''

    for s in readable:
        if s is server:
            # A "readable" server socket is ready to accept a connection
            connection, client_address = s.accept()

            print ('new connection from', client_address, file=sys.stderr)
            
            # Set non-blocking for select
            connection.setblocking(0)

            # Add this connection to the list of inputs
            inputs.append(connection)

            #Get the IP address of this new connection
            # And add it as a neighbor and fill it with -1 to represent initial connection
            ip_address = connection.getpeername()[0]
            neighborIPs_timestamp[connection] = -1

            # Map this IP to the input socket
            IP_input_sockets[ip_address] = connection


        else:
            
            # Try to receive initial data
            data = s.recv(1024)

            if data:
                data = data.decode()

                # Loop to receive the complete message
                while sep not in data:
                    receive = s.recv(256)
                    receive = receive.decode()
                    data += receive
                
                #Check if the data we received corresponding to a returning 'processed' signal
                if (data == processed):

                    print ('received returning processing signal from %s' % data, file=sys.stderr)

                    #Remove from inputs since we no longer expect a reply
                    inputs.remove(s)
                    #Add into output channel to send new data
                    if s not in outputs:
                        outputs.append(s)

                    #Get IP and indicate that this neighbor has been processed
                    ip_address = s.getpeername()[0]
                    neighborIPs_processed[ip_address] = True
                
                #If it is not a returning 'processed' signal then it must be data being sent and requires reading
                else:
                    # Parse into integer #
                    data = int(data)

                    print ('received "%s" from %s' % (data, s.getpeername()), file=sys.stderr)
                    print ('socket name: %s' % s, file=sys.stderr)

                    # Update new integer timestamp
                    ip_address = s.getpeername()[0]
                    neighborIPs_timestamp[ip_address] = data
                    
                    ## ===== Process Start for next iteration subroutine ===== ##
                    #Check if the new msg_received count is equal to the number of neighbors, if so move on to next iteration 
                    msg_received_count += 1
                    if (msg_received_count == len(neighborIPs_timestamp)) :
                        for ip_key, timestamp in neighborIPs_timestamp.items():

                            #Double check timestamps, this should never run
                            if (this_timestamp != timestamp):
                                print ("ERROR: TIMESTAMP NOT EQUAL", file=sys.stderr)
                                exit(1)

                            #===== Processing for next iteration =====#
                            this_timestamp+=1

                            # Queue up new iteration message into all the neighbors for sending
                            message_queues[ip_key].put( this_timestamp )

                    ## ===== Process End for next iteration subroutine ===== ##
                    
                    # Add to output channel for a response indicating we have processed timestamp signal
                    if s not in outputs:
                         outputs.append(s)

            else: # ===== WIP ===== #

                # Interpret empty result as closed connection
                print ('closing', client_address, 'after readitng no data', file=sys.stderr)
                # Stop listening for input on the connection
                # if s in outputs:
                #     outputs.remove(s)
                inputs.remove(s)
                s.close()
                exit(1)

                #Remove message queue
                # del message_queues[s]
    """
    ===Writeable===
    #Handle outputs
    1) Data is in the queue for a connection, the next message is sent.
    2) Otherwise the connection is removed from the list of output connections
        so that the next time loop select() does not indicate the socket is ready to send data
    """

    for s in writable:
        try:
            ip_address = s.getpeername()[0]
            next_msg = message_queues[ip_address].get_nowait()
        except queue.Empty:
            # # No messages waiting so stop checking for writability
            print ('output queue for', s.getpeername(), 'is empty', file=sys.stderr)
            # outputs.remove(s)
            continue
        else:
            print ('sending "%s" to %s' % (next_msg, s.getpeername()), file=sys.stderr)
            send_msg = (str(next_msg) + sep).encode()
            s.send(send_msg)

    """
    ===Exceptional===
    1) Error with socket, close the socket
    """

    for s in exceptional:
        print ('handling exceptional condition for', s.getpeername(), file=sys.stderr)
        #Stop listening for input on the connection
        totalSockets.remove(s)
        if s in inputs:
            inputs.remove(s)
        if s in outputs:
            outputs.remove(s)
        s.close()

        # Remove message queue
        del message_queues[s]
