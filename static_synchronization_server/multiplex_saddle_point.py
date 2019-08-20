import select
import socket
import sys
import queue
import time
from neighbor_node_saddle_point import NeighborNode
import copy

# == Subroutine to get this device's IP address == #
input_file = open("multiplex_saddle_point_input.txt", "r")
full_ip_address = input_file.readline()
full_ip_address = full_ip_address.split(":")
server_address = (full_ip_address[0], int(full_ip_address[1]))
# == End of subroutine to get this device's IP address == #

#======Start of Server Creation=====#
# Create a TCP/IP socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setblocking(0)

# Bind the socket to the port
print ('starting up on %s port %s' % server_address, file=sys.stderr)
server.bind(server_address)

#Listen for incoming connections
server.listen(5)
#=====End of Server Creation=====#

#=====Start of Data Structure & Variable Initialization=====#

# ===== Initialization of Constants ===== #
#END (Upper level protocol to how to receive bytes bigger than initial set size)
END = '\n'
#SEP (Seperator between different pieces of information in the byte string that we send)
SEP = ':'
# ===== End of Initialization of Constants ===== #

#Create own timestamp for this device
this_timestamp = 0

# ==== Var actually not needed for now, may be used for future implementation of
# ===== some other signal able to turn on and off the network independent on set
# ====== t_max and timer signals ===== #
#Initialize the default outer loop val for this device (0 neutral)
# 0 = Neutral (stay at current state), propogate neutral state
# 1 = Reset Signal
# -1 = Switch to stop state, propogate stop signal
this_state_signal = 0

#Map of IPs to NeighborNode objects
neighbors = {}

#Variable to determine if all necessary connections are valid and verified
all_nodes_connected = False

# Sockets to which we expect to write
outputs = []
# Sockets from which we read from
inputs = [ server ]
#Complete list of sockets to watch out for errors
totalSockets = inputs + outputs

#Maximum number of neighbors
max_neighbors = float(3)

#Output file for writing
output_file = open('output_file.txt', 'w+')

#Number of messages we're sending
NUM_MESSAGES = 7

#=====End of Variable initialization=====#

# Debugs for output/input lists
##print(outputs, file=sys.stderr)
##print(inputs, file=sys.stderr)

# === Subroutine to process this node's characteristics defined by input file === #
# ==== Format of Data Entry: gmin gmax initialization_set_bool initialization_set_cardinality this_y_val
# ===== Limits:
#               gmin: 0 - inf 
#               gmax: 0 - inf
#               initialization_set_bool: 0 or 1 (indicating T/F as being part of initialization set)
#               initialization_set_cardinality: 1 - inf (Size of initialization set)
#               this_y_val: 0 - inf
# ====== Example:    0  10  0  1
characteristics = input_file.readline()
characteristics = characteristics.split()

this_gmin = int(characteristics[0])
this_gmax = int(characteristics[1])
this_initialization_node = int(characteristics[2])
initialization_set_cardinality = int(characteristics[3])
init_Pref = float(characteristics[4])
init_v = float(characteristics[5])

input_vars = input_file.readline()
input_vars = input_vars.split()
this_x = float(input_vars[0])
this_z = float(input_vars[1])
this_lambda = float(input_vars[2])
ALPHA_STEP = float(input_vars[3])

input_equation_vars = input_file.readline()
input_equation_vars = input_equation_vars.split()
equation_multiplier = float(input_equation_vars[0])
equation_shifter = float(input_equation_vars[1])
equation_exponential = float(input_equation_vars[2])

# === End of subroutine === #

# === Subroutine to process list of neighbors and initialize neighbors === #
for x in input_file:
    string_parse = x.split(":")
    print("Neighbor:", string_parse)
    neighbor_ip_address = string_parse[0]
    neighbor_port = string_parse[1]
   
    new_neighbor = NeighborNode(neighbor_ip_address, neighbor_port)
    new_neighbor.timestamp_vals = {}
    neighbors[neighbor_ip_address] = new_neighbor
# === End of subroutine === #

input_file.close()

# === Function Definitions for the program === #

def verify_all_connections():
    all_have_connected = True
    for neighbor_node in neighbors.values():
        if not neighbor_node.socket:
            all_have_connected = False
    return all_have_connected

# === End of function definitions === #


#=====Start of Connection initialization with neighbors=====#
# Only runs on the remaining connections that we still need
for ip_address, neighbor_node in neighbors.items():

    ip_key = neighbor_node.ip_address
    port_value = int(neighbor_node.port)

    #Create new socket for the corresponding ip_key and port
    server_address = (ip_key, port_value)
    new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #====Try to connect to the neighboring node using the socket we created====#
    try:
        print("Trying to connect to ", server_address)
        new_socket.connect(server_address)
    except:
        print ("Connection Failed, on %s port %s" % server_address)
    else:
        #====Successful Connection====#
        print( "Connection Success on %s port %s" % server_address)

        #Set non-blocking for select
        new_socket.setblocking(0)

        #Add socket to neighbors
        neighbor_node.socket = new_socket

        #Add to inputs/outputs list for select
        outputs.append(new_socket)
        inputs.append(new_socket)

all_nodes_connected = verify_all_connections()

#=====End of Connection Initialization with neighbors=====#

not_disconnected = True


start_time = time.time()
#Bool to start the timer when the whole progrma starts
start_time_bool = False

end_time = time.time()

this_t = 0
t_max = 1

#===== Main Program ====#
while not_disconnected:
    
    print ("This Initialization Bool : ", str(this_initialization_node))
    print ("All connected : ", str(all_nodes_connected))

    if all_nodes_connected and not start_time_bool:
        start_time = time.time()
        start_time_bool = True

    # ==== Logic for the timer node and incrementing the timer node ==== #
    if this_initialization_node and all_nodes_connected and this_t != t_max:
        this_state_signal = 0
        end_time = time.time()
        if (end_time - start_time) >= 20:
            print ("+++++++++++++++++++++++++INCREMENTING T @ " + str(end_time - start_time))

            #Write to output file
            output_file.write("Iteration " + str(this_t) + SEP + str(this_x) + END)
            
            this_t += 1
            start_time = time.time()
            this_y_val = float(characteristics[4]) + float(this_t)
            print ("====================RESET=========================")
            if all_nodes_connected:
                for neighbor_node in neighbors.values():
                    #Put all sockets into outputs so we can update t
                    neighbor_socket = neighbor_node.socket
                    if neighbor_socket not in outputs:
                        outputs.append(neighbor_socket)
                    
                    #Change all timestamps to -1 to prepare for next iteration of t
                    neighbor_node.timestamp = -1
                    neighbor_node.processed_bool = True
                    neighbor_node.processed_signal = 1
                    neighbor_node.updated_timestamp_bool = False

            this_timestamp = 0
    
    if this_t == t_max:
        if all_nodes_connected:
            for neighbor_node in neighbors.values():
                neighbor_socket = neighbor_node.socket
                if neighbor_socket not in outputs:
                    outputs.append(neighbor_socket)

    #print("Inputs: ", inputs)
    #print("Outputs: ", outputs)
    print("This Timestamp: ", this_timestamp)
    print("Neighbors: =====")
    for neighbor_node in neighbors.values():
        print("Neighbor IP: ", str(neighbor_node.ip_address))
        print("Neighbor Timestamp: ", str(neighbor_node.timestamp))
    print("This X Val: ", this_x)
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

            # Add this connection to the list of inputs and outputs
            inputs.append(connection)
            outputs.append(connection)

            #Get the IP address of this new connection
            other_ip_address = connection.getpeername()[0]

            neighbor_node = neighbors[other_ip_address]
            neighbor_node.socket = connection
            
            all_nodes_connected = verify_all_connections()

        else:

            # Try to receive initial data
            data = s.recv(1024)

            if data:
                data = data.decode()

                data_strip_END = data.replace(END, "")
                print ("Received ", data_strip_END, ' from ', s.getpeername())
                array_of_vals = data_strip_END.split(SEP)
                
                num_messages = len(array_of_vals)//NUM_MESSAGES

                for x in range(0, num_messages):
                    other_t = copy.copy(int(array_of_vals[x*NUM_MESSAGES]))
                    other_k = copy.copy(int(array_of_vals[x*NUM_MESSAGES + 1]))
                    other_state_signal = copy.copy(int(array_of_vals[x * NUM_MESSAGES + 2]))
                    other_processed_signal = copy.copy(int(array_of_vals[x * NUM_MESSAGES + 3]))
                    other_x = copy.copy(float(array_of_vals[x * NUM_MESSAGES + 4]))
                    other_z = copy.copy(float(array_of_vals[x * NUM_MESSAGES + 5]))
                    other_lambda = copy.copy(float(array_of_vals[x * NUM_MESSAGES + 6]))
                    other_ip_address = copy.copy(s.getpeername()[0])
                    neighbor_node = neighbors[other_ip_address]

                    # Update T for non-timers
                    if not this_initialization_node and other_t > this_t:
                        #print("=============RESET===========", s)
                        
                        #Write to output file
                        output_file.write("Iteration " + str(this_t) + SEP + str(this_x) + END)
                        
                        #Update timestamp and reset variables
                        this_t = other_t
                        this_timestamp = 0
                        this_x = float(characteristics[4]) + float(this_t)

                        for neighbor_address in neighbors:
                            neighbor_node = neighbors[neighbor_address]
                            neighbor_socket = neighbor_node.socket
                            if neighbor_socket not in outputs:
                                outputs.append(neighbor_socket)
                            neighbor_node.timestamp = -1
                            neighbor_node.processed_bool = False
                            neighbor_node.processed_signal = 1
                            neighbor_node.updated_timestamp_bool = False
                            neighbor_node.sent_data = False


                    #Check if the data we received corresponding to a returning 'processed' signal
                    print("other_ip_address :", other_ip_address)
                    neighbor_node = neighbors[other_ip_address]
                    if other_t == this_t:
                        #print("========Proceed=======", s)
                        if other_processed_signal:

                            #Get IP and indicate that this neighbor has been processed
                            neighbor_node.processed_bool = True

                        if neighbor_node.timestamp < other_k:
                            
                            #print("======Update=====", s)
                            # Update new integer timestamp
                            neighbor_node.timestamp = copy.copy(other_k)
                            neighbor_node.updated_timestamp_bool = True

                            #Update Value
                            neighbors[other_ip_address].timestamp_z_vals[other_k % 3] = copy.deepcopy(other_z)
                            neighbors[other_ip_address].timestamp_lambda_vals[other_k % 3] = copy.deepcopy(other_lambda)
    
            else: # ===== WIP ===== #

                # Interpret empty result as closed connection
                #print ('closing', client_address, 'after reading no data', file=sys.stderr)
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
        if this_t == t_max:
            other_ip_address = s.getpeername()[0]
            neighbor_node = neighbors[other_ip_address]
            neighbor_node.disconnected = True
        
        other_ip_address = s.getpeername()[0]
        neighbor_node = neighbors[other_ip_address]
        
        send_msg_list = [
            this_t,
            this_timestamp,
            this_state_signal,
            neighbor_node.processed_signal,
            this_x,
            this_z,
            this_lambda
        ]

        send_msg = ""
        
        for msg in send_msg_list:
            send_msg += str(msg)
            send_msg += SEP
        print ('Sending ', send_msg, ' to ', s.getpeername())

        #Reset processed signal
        neighbor_node.processed_signal = 0
        neighbor_node.sent_data = True

        send_msg = send_msg.encode('utf-8')
        s.send(send_msg)
        outputs.remove(s)

    ## ===== Process Start for next iteration subroutine ===== ##

    received_all_timestamps = True
    all_neighbors_processed = True
    all_sent_data = True

    #===== Processing for next iteration =====#
    for neighbor_node in neighbors.values():

        #Double check timestamps, if it is unequal, we skip the checks
        if this_timestamp != neighbor_node.timestamp and this_timestamp+1 != neighbor_node.timestamp:
            received_all_timestamps = False

        if not neighbor_node.processed_bool:
            all_neighbors_processed = False

        if not neighbor_node.sent_data:
            all_sent_data = False

    if received_all_timestamps and all_neighbors_processed and all_sent_data:
        
        print("==========================Updating Values before next timestamp==================")
        
        this_x_dot = float( -1 * ( (equation_multiplier * this_x)**equation_exponential + equation_shifter ) - this_lambda )
        this_z_dot = float( -1 * max_neighbors * this_lambda )
        this_lambda_dot = this_x_dot + max_neighbors * this_z - init_Pref * init_v

        print("Neighbors : ", neighbors.values())
        for neighbor_node in neighbors.values():
            
            print("Printing neighbor node name : ", neighbor_node.ip_address)
            print("Timestamp values : ", neighbor_node.timestamp_vals)
          
            #Before proceeding, we update this y_val
            this_z_dot += float( neighbor_node.timestamp_lambda_vals[this_timestamp % 3] )
            this_lambda_dot -= float( neighbor_node.timestamp_z_vals[this_timestamp % 3] )
            #Reset variables
            neighbor_node.processed_bool = False
            neighbor_node.updated_timestamp_bool = False
            neighbor_node.sent_data = False
            neighbor_node.processed_signal = 1

            # === Put this socket in outputs so that we can send out new timestamp === #
            neighbor_socket = neighbor_node.socket
            if neighbor_socket not in outputs:
                outputs.append(neighbor_socket)


        print("==================Incrementing Values=================")
        this_x = this_x + ALPHA_STEP * this_x_dot
        this_z = this_z + ALPHA_STEP * this_z_dot
        this_lambda = this_lambda + ALPHA_STEP * this_lambda_dot

        if this_x < this_gmin:
            this_x = this_gmin
        if this_x > this_gmax:
            this_x = this_gmax
        
        print("=================Proceeding to next timestamp=====================")
        this_timestamp+=1

    ## ===== Process End for next iteration subroutine ===== ##

    # === Subroutine for determining when to stop this loop === #
    # ==== Current determination created when we sent all t == t_max signals to all neighbors ==== #

    all_disconnected = True
    for ip_address, neighbor_node in neighbors.items():
        if not neighbor_node.disconnected:
            all_disconnected = False
            break
    
    if all_disconnected:
        not_disconnected = False

    # === End of subroutine === #
    """
    print(not_disconnected)
    ===Exceptional===
    1) Error with socket, close the socket
    """

    for s in exceptional:
        #print ('handling exceptional condition for', s.getpeername(), file=sys.stderr)
        #Stop listening for input on the connection
        totalSockets.remove(s)
        if s in inputs:
            inputs.remove(s)
        if s in outputs:
            outputs.remove(s)
        s.close()

# ==== Final output of program after ending outer loop (Debugging) ==== #
print ("=====================END OF PROGRAM OUTPUT=====================")
print ('t for this machine ', full_ip_address , ': ', this_t)
print ('k for this machine ', full_ip_address , ': ', this_timestamp)
print ('State of this machine', full_ip_address , ': ', this_state_signal)
print ("Printing timestamps below of length: " + str(len(neighbors)))
for neighbor_node in neighbors.values():
    neighbor_timestamp = neighbor_node.timestamp
    neighbor_ip_address = neighbor_node.ip_address
    print ("Neighbor Node: " + str(neighbor_ip_address) + " - Timestamp : " + str(neighbor_timestamp))
output_file.close()
