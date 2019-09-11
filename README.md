# Microgrid

WELCOME!

	This is my microgrid optimization simulation for several different algorithms. Connect your computer up to the ethernet switch and follow these instructions to know how to work with my system.

Contact me at c0l3tw@gmail.com if you have any questions that were left unanswered in this documentation. Also check out the code of the scripts if you are confused on how to use them.
(I usually leave a format guide in the first few lines, though some *may* be outdated by now.)

~~~~ How to use this system ~~~~
 - Initial Setup -
	Share the ssh key of your computer with the Pis, which allows ssh-ing in without prompting a password, and is required for the script to work. 
Here's a helpful tutorial on how to do this --> http://www.linuxproblem.org/art_9.html. Simply do this for all the IPs listed in the IPs/allIP.txt
file or the list at the end of this README, and you're good to go. Use username "pi" and password "raspberry" in this setup.

 - Running the Simulation -
	Run the shell script ./activate_microgrid_simulation.sh, and it will prompt you to select which simulation to run, which graph structure to run on
(illustrations are located in the word document called GraphStructures.docx in the home directory), which reference file to use, and which 
controllers to send the activation command to. If you're unsure about the last one, just select the option labelled "eightIP.txt", and this will run your simulation of 
choice on all of the Pis. It will fail on the Pis that aren't in the graph structure you chose, but that shouldnt effect the outcome. 
	All output is accumulated on a specific Pi, which I call the "Controller" or "Accumulator" Pi throughout the code. Don't let the name "Controller" worry you, it doesn't have any
control on the operation of the Pis. Bit of a misnomer. SSH into it to check the output. Its IP is 169.254.136.2, with username pi and password "raspberry" (same pass for all Pis)
In the home directory you will find a file called "results.csv". This is the file containing the output from all the Pis. The columns are labelled so it shouldn't be too hard to 
read. The number after "output" refers to the number of the Pi. 

NOTE: You can also go into the csvFiles directory on the Accumulator, and look at each Pi's respective output files. This is the only place to find the number of iterations that was
reached for each time-interval. This number wont change between PIs very much, so you only need to check one of the files for each t.

 - Updating/Making new Graph Structures -
	Each Pi has a directory called graphs. In here are input files containing some information that the Pi needs to know to run its simulation for each graph structure. 
In the first line, there is a single integer which represents the number of agents in this graph structure. The following lines contain each of the Pi's immediate 
neighbors for this graph, one label per line (e.g. R1\n R2). For two-hop, there is an additional subdirectory called two_hop that contains input files used by the 
two-hop version of saddle-point. Each file consists of a list of labels corresponding to an agent that is two hops away, and the number of distinct paths to that neighbor.
(e.g. R2 5 for a two-hop neighbor of R2 that has 5 distinct ways of reaching it from the agent in question). For an example of an input file and to edit or add structures,
ssh into each of the Pis and go to the graphs directory to change the data or add your new structure. When making a new structure, make sure the name is the same on each machine, 
and add that name to the list of graph structures in the ./activate_microgrid_simulation.sh script.

	NOTE: The number of paths to the neighbor is information that I think is necessary to operate two-hop, but I may have done the math wrong in that respect.
Contact me and I'll give you the exact formula I used and my thinking that led to that assumption. I haven't extensively tested this program yet so it may have some flaws. 
I only managed to set up the "hook" graph structure for testing with two-hop, so to run two-hop with other graph structures you'll need to make your own input files.

	Each Pi also has an info.txt which is located in the graphs directory as well. This contains information that is specific to the Pi itself, such as gmin, gmax, and
its cost function. Here's a general format for an info file, all contained in the first line.

info.txt format:
g_min g_max receives_Pr(boolean, 0 or 1) number_agents_that_receive_Pr is_timer(boolean, 0 or 1) scalar_for_cost_function exponent_for_cost_function

	Here's some additional explanation for what some of these things mean. g_min, g_max are our bounds for this DER. receives_Pr is 1 if this Pi is one that 
gets the signal value from the ISO. number_agents_receive_pr is self explanatory, and is an integer greater than or equal to 1. is_timer is used in the implementation to
determine which Pi will be the one keeping time. There should only ever be one agent for which this is true. And the scalar/exp for the cost function is simple,
for some arbitrary cost function a*x^b, a is the scalar and b is the exponent. Shifting along the x or y axes is not supported.

--- PI IPs --- 
R1: 169.254.86.232
R2: 169.254.142.58 
R3: 169.254.180.72
R4: 169.254.160.208 
R5: 169.254.121.217
R6: 169.254.17.57
R7: 169.254.249.0
R8: 169.254.128.136
Accumulator: 169.254.136.2

~~~~ SCRIPTS ~~~~

send_to_pis.sh
	Use this script to send a file to each of the PIs. If you make edits to the simulation files, just run this script to update the code on all the Pis.

	USAGE: ./send_to_PIs.sh file_to_send.ext folder(optional, leave empty for home directory) text_file_containing_IP_addresses(optional, default is all Pis) 

activate_microgrid_simulation.sh
	This script runs the show. This can remotely run the algorithms and there are a variety of graph structures to choose from.

	USAGE: ./path/activate graph_structure(integer value from 0-7) reference_file(int value) IP_File.txt(int value) [leave as 0 for defaults]
	OR just run the script without parameters, it will automatically prompt you for missing fields. Leaving zero will choose the default value.

run_sim.sh
	This script is used by the pis alone. This is run by the activate script remotely and runs the simulation of choice, and after execution completes it sends 
	all the output to the accumulator pi to be compiled into one easy to read, formatted CSV file called "results.csv".

compile_csv.py
	This is used by the accumulator to combine all the acquired csv files into the results file.

Simulations
	There is a python script for each of the different simulations that were implemented. 
	1. ratio_consensus_dist.py
	2. saddle_point_one_hop.py
	3. saddle_point_two_hop.py
	To make changes to the time-limit for the calculation stage or any other changes, simply edit the file in your home directory and use ./send_to_pis.sh to
	update the Pis with your changes. The time_limit variable is the one that determines how long the pis will collect data from their neighbors before going
	to the next iteration. It's at line ~200 in ratio_consensus_dist.py and earlier in the document for the other two simulation scripts.


Good luck!

