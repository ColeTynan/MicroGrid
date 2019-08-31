# Microgrid

WELCOME!

This is my microgrid optimization simulation for several different algorithms. Connect your computer up to the ethernet switch and follow these instructions
to set up your computer to work with the Pis.

~~~~ SETUP INSTRUCTIONS ~~~~
1. Share ssh key with the Pis, which allows ssh without prompting a password, and is required for the script to work. TODO: write script that automates this procedure
2. Run the executable. It will prompt you to select which algorithm you would like to run, which graph structure (illustrations
	are located in the word document called GraphStructures.docx in the home directory. TODO: make this document)
3. ssh into the "Controller" or "Accumulator" Pi. Its IP is 169.254.136.2, with username pi and password "raspberry".
in the home directory you will find a file called "results.csv". This is the file containing the output from all the Pis.
NOTE: You can also ssh into each of the Pis directly, and look at their respective output files. These are the only files
to show the number of iterations of the algorithm reached for each time-interval.



~~~~ SCRIPTS ~~~~

setup.sh
	TODO: Write this script and make documentation for it

send_to_pis.sh
	Use this script to send a file to each of the PIs.

	USAGE: ./send_to_PIs.sh file_to_send.ext folder(optional, leave empty for home directory) text_file_containing_IP_addresses(optional, default is all Pis) 

activate_microgrid_simulation.sh
	This script runs the show. This can remotely run the algorithms and there are a variety of graph structures to choose from.

	USAGE: ./path/activate graph_structure(integer value from 0-7) reference_file(int value) IP_File.txt(int value) [leave as 0 for defaults]
	OR just run the script without some or all parameters, it will automatically prompt you for missing fields.


