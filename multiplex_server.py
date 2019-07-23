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

# == Subroutine to get this device's IP address == #
ip_file = open("this_ip.txt", "r")
full_ip_address = ip_file.readline()
full_ip_address = full_ip_address.split(":")
server_address = (full_ip_address[0], int(full_ip_address[1]))
# == End of subroutine to get this device's IP address == #

print ('starting up on %s port %s' % server_address, file=sys.stderr)
server.bind(server_address)

#Listen for incoming connections
server.listen(5)

#=====End of Server Creation=====#

#=====Start of Data Structure & Variable Initialization=====#

#Dict of IPs and their corresponding ports for the neighboring controllers
neighbors = {}
#Dict of connections that we need to connection to (Initially is the same as neighbors)
neighboring_connections_dict = {}
#SEP (Upper level protocol to how to receive bytes bigger than initial set size)
sep = '\n'
#Processed (Protocol for moving forward only when we receive this signal)
processed = '#####'

#Create dict between neighbors_ip mapping to true or false indication of processed status
neighborsIP_processed_bool = {}
#Create dict between nieghbors_ip mapping to true or false indication of timestamp updated status
neighborsIP_updated_timestamp_bool = {}
#List of IPs that we are currently connected to
neighborsIP_connected_list = []
#Create a dict of neighbors and their associated timestamp that we get
neighborsIP_timestamp = {}

#Create own timestamp for this device
this_timestamp = 0

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
# Debugs for output/input lists
#print(outputs, file=sys.stderr)
#print(inputs, file=sys.stderr)

# === Subroutine to process neighbor file and initialize neighbors === #
neighbor_file = open("neighbor_file.txt", "r")
for x in neighbor_file:
    string_parse = x.split(":")
    print("Neighbor:", string_parse)
    neighbors[string_parse[0]] = int(string_parse[1])
    neighboring_connections_dict[string_parse[0]] = int(string_parse[1])
    neighborsIP_processed_bool[string_parse[0]] = False
    neighborsIP_updated_timestamp_bool[string_parse[0]] = False
    neighborsIP_timestamp[string_parse[0]] = -1
# === End of subroutine === #
neighbor_file.close()
print (neighbors)

#=====Start of Connection initialization with neighbors=====#
# Only runs on the remaining connections that we still need
for ip_key, port_value in neighboring_connections_dict.items():

    #Create new socket for the correpsonding ip_key and port
    server_address = (ip_key, port_value)
    new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        #====Try to connect to the neighboring node using the socket we created====#
        new_socket.settimeout(10)
        try:
            new_socket.connect(server_address)
        except:
            print ("Connection Failed, on %s port %s, retrying in 0.5s" % server_address, file=sys.stderr)
            time.sleep(0.5)
        else:
            #====Successful Connection====#
            print( "Connection Success on %s port %s, continuing"
                    % server_address, file=sys.stderr )

            if ip_key not in neighborsIP_connected:
                neighborsIP_connected.append(ip_key)

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

            #Remove this connection from the dictionary
            del neighboring_connections_dict[ip_key]
            break
    
#=====End of Connection Initialization with neighbors=====#


# Debug Var
iteration_count = -1

#===== Main Program ====#
while inputs:
    iteration_count+=1
    readable, writable, exceptional = select.select(inputs, outputs, totalSockets)
    print("   ")
    print(iteration_count)
    print("Readable:")
    print(readable)
    print("    ")
    print("Inputs:")
    print(inputs)
    print("    ")
    print("Outputs:")
    print(outputs)
    print("     ")
    print("Writable:")
    print(writable)
    print("     ")
    print("Message Queue:")
    for socketr, queuer in message_queues.items():
        print("Socket: ", socketr.getpeername()[0])
        for elem in queuer.queue:
            print("Queue Element:", elem)
        print("    ")
    print("     ")
    print("This_timestamp: ", this_timestamp)
    print("msg_recv_count", msg_received_count)
    print("length of neighbors", len(neighbors))
    for ip, timestamp in neighborsIP_timestamp.items():
        print ("IP: ", ip)
        print ("timestamp: ", timestamp)

    #if(iteration_count == 10000):
    #    print("Exiting...")
    #    exit(0)

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

            if ip_address not in neighborsIP_connected_list:
                neighborsIP_connected_list.append(ip_address)
            # Map this IP to the input socket
            IP_input_sockets[ip_address] = connection

            # Create new queues for new connections
            message_queues[connection] = queue.Queue()

        else:

            # Try to receive initial data
            data = s.recv(1024)

            if data:
                print(data)
                data = data.decode()
                processed_data = data.split(sep)
                processed_data = processed_data[0]
                print("processed_data:", processed_data)
                #Check if the data we received corresponding to a returning 'processed' signal
                if (processed_data == processed):

                    print ('received returning processing signal from %s' % data, file=sys.stderr)

                    #Remove from inputs since we no longer expect a reply
                    inputs.remove(s)
                    #Add into output channel to send new data
                    if s not in outputs:
                        print("Socket is put back into outputs from processed")
                        outputs.append(s)

                    #Get IP and indicate that this neighbor has been processed
                    ip_address = s.getpeername()[0]
                    neighborsIP_processed_bool[ip_address] = True

                #If it is not a returning 'processed' signal then it must be data being sent and requires reading
                else:

                    # Loop to receive the complete message
                    print("Data: ",data)
                    while sep not in data:
                        receive = s.recv(256)
                        receive = receive.decode()
                        data += receive

                    # Parse into integer #
                    data = int(data)

                    print ('received "%s" from %s' % (data, s.getpeername()), file=sys.stderr)

                    ip_address = s.getpeername()[0]

                    other_previous_timestamp = 0
                    updated_timestamp = False
                    try:
                        other_previous_timestamp = neighborsIP_timestamp[ip_address]
                    except KeyError:
                        other_previous_timestamp = data
                        updated_timestamp = True
                    else:
                        if((data - other_previous_timestamp) == 1):
                            updated_timestamp = True
                    
                    if updated_timestamp:
                        neighborsIP_updated_timestamp_bool[ip_address] = True

                    # Update new integer timestamp
                    neighborsIP_timestamp[ip_address] = data

                    #Check if the new msg_received count is equal to the number of neighbors, if so move on to next iteration
                    msg_received_count += 1
                    
                    inputs.remove(s)
                    # Add to output channel for a response indicating we have processed timestamp signal
                    if s not in outputs:
                        outputs.append(s)

            else: # ===== WIP ===== #

                # Interpret empty result as closed connection
                print ('closing', client_address, 'after reading no data', file=sys.stderr)
                # Stop listening for input on the connection
                # if s in outputs:
                #     outputs.remove(s)
                inputs.remove(s)
                s.close()
                exit(1)

                #Remove message queue
                # del message_queues[s]

    ## ===== Process Start for next iteration subroutine ===== ##
    
    if (this_timestamp == 1000):
        print("Exiting...")
        exit(0)

    if (msg_received_count == len(neighbors)):

        received_all_timestamps = True
        all_neighbors_processed = True

        #===== Processing for next iteration =====#
        for ip_key, timestamp in neighborsIP_timestamp.items():

            #Double check timestamps, if it is unequal, we skip the checks
            if (this_timestamp != timestamp):
                received_all_timestamps = False
                break

            if (this_timestamp > timestamp):
                received_all_timestamps = False
                break
        
        for ip_key, processed_bool in neighborsIP_processed_bool.items():

            if not processed_bool:
                all_neighbors_processed = False
                break

        if (received_all_timestamps and all_neighbors_processed):
            this_timestamp+=1
            for ip_key, port_value in neighbors:

                # Queue up new iteration message into all the neighbors for sending
                timestamp_output_socket = IP_output_sockets[ip_key]
                message_queues[timestamp_output_socket].put( this_timestamp )
                msg_received_count = 0

                receive_data_socket = IP_input_sockets[ip_key]
                #Put processed into message queue to send
                message_queues[receive_data_socket].put(processed)

    ## ===== Process End for next iteration subroutine ===== ##

    """
    ===Writeable===
    #Handle outputs
    1) Data is in the queue for a connection, the next message is sent.
    2) Otherwise the connection is removed from the list of output connections
        so that the next time loop select() does not indicate the socket is ready to send data
    """

    for s in writable:

        #===== Start of Message Gathering =====#
        try:
            next_msg = message_queues[s].get_nowait()
        except queue.Empty:
            # No messages in queue, but continue waiting in case a message pops up
            # print ('output queue for', s.getpeername(), 'is empty retrying...', file=sys.stderr)
            continue
        else:
            print("NextMSG: ", next_msg)
            print("Processed: ", processed)
            # Once a valid message has been retrieved, process the message
            if ( next_msg == processed ):
                print ('sending processed return %s to %s' % (next_msg, s.getpeername()), file=sys.stderr)
                s.send(next_msg.encode())

            else:
                print ('sending "%s" to %s' % (next_msg, s.getpeername()), file=sys.stderr)
                send_msg = (str(next_msg) + sep).encode()
                s.send(send_msg)

            #Remove from output queue back to input
            # We're either expecting new timestamped message or expecting processed return signal
            outputs.remove(s)
            if s not in inputs:
                print("socket %s is put back into inputs", s)
                inputs.append(s)

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
