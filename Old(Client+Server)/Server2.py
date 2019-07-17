import select
import socket
import sys
import queue

# Create a TCP/IP socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setblocking(0)

# Bind the socket to the port
server_address = ('localhost', 10001)
print ('starting up on %s port %s' % server_address, file=sys.stderr)
server.bind(server_address)


#Listen for incoming connections
server.listen(5)

#Dict of IPs and their corresponding ports for the neighboring controllers
neighbors = {
    '168.25..' : '10001'
}

#Create a dict of sockets corresponding to neighbors
output_sockets = {}

# Sockets to which we expect to write
outputs = []

#For each corresponding ip/port, we create a new socket and connect to it
for ip_key, port_value  in neighbors.items():
    new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    new_socket.connect(server_address)
    new_socket.setblocking(0)
    output_sockets[ip_key] = new_socket
    outputs.append(new_socket)
    server_address = (ip_key, port_value)

#Create own timestamp for this device
this_timestamp = 0

#Create a list of neighbors and their associated timestamp that we get
neighbors_timestamp = {}

# Sockets from which we read from
inputs = [ server ]

# Complete list of sockets to watch out for errors
totalSockets = inputs + outputs

#The server is going to wait for a socket to become writable before sending any data
# Each output connection then needs a queue to act as a buffer for data to be sent through
message_queues = {}

msg_received_count = 0

#Program main loop using select() to block and wait for network activity
while inputs:

    # Wait for one of the sockets to be ready for processing
    print ('\nwaiting for the next event', file=sys.stderr)
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
            connection.setblocking(0)
            inputs.append(connection)
            
            #Add this new connection as a neighbor and fill it with -1 to represent begin of connection
            neighbors_timestamp[connection] = -1
            
            ip_address = connection.getpeername()[0]
            # Give the connection a queue for data we want to send
            message_queues[ip_address] = queue.Queue()

        else:
            data = s.recv(1024)
            if data:
                # A readable client socket has data
                print ('received "%s" from %s' % (data, s.getpeername()), file=sys.stderr)
                print ('socket name: %s' % s, file=sys.stderr)

                neighbors_timestamp[s] = data

                msg_received_count += 1

                if (msg_received_count == len(neighbors_timestamp)):
                    for conn, timestamp in neighbors_timestamp.items():
                        if (this_timestamp != timestamp):
                            print ("ERROR: TIMESTAMP NOT EQUAL", file=sys.stderr)
                            exit(1)
                        #If they are equal
                        this_timestamp+=1


                ip_address = s.getpeername()[0]
                message_queues[ip_address].put(data)
                # # Add output channel for response
                # if s not in outputs:
                #     outputs.append(s)

            else:
                # Interpret empty result as closed connection
                print ('closing', client_address, 'after readitng no data', file=sys.stderr)
                # Stop listening for input on the connection
                # if s in outputs:
                #     outputs.remove(s)
                inputs.remove(s)
                s.close()

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
            # print ('output queue for', s.getpeername(), 'is empty', file=sys.stderr)
            # outputs.remove(s)
            continue
        else:
            print ('sending "%s" to %s' % (next_msg, s.getpeername()), file=sys.stderr)
            s.send(next_msg)
            
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