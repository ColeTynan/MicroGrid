# Microgrid

send_to_pis
	Use this script to send a file to each of the PIs with the following format:
.send_to_PIs.sh file_to_send.py folder(optional) text_file_containing_IP_addresses(optional, default is all Pis)

activate_rat_con
USAGE: ./path/activate graph_structure(integer value from 0-7) reference_file(int value) IP_File.txt(int value) [leave as 0 for defaults]
	Graph structure options (figures in accompanying document)
 1. ring4.txt					-- ring of four agents
 2. ring8.tx						-- ring of eight agents
 4. smallASym.txt			-- small asymmetrical structure of four agents
 5. hook.txt						-- shaped like a "hook" or a linked list
 6. treeBal7.txt				-- a balanced binary tree strcture
 7. treeUnb7.txt				-- unbalanced binary tree
	reference file options
 1. reg-d-abridged.CSV -- the first ten values from reg-d
 2. reg-d.CSV					-- The full reg-d file, containing 1200 entries
 3. reg-d-factor5.CSV	-- reg-d but every value is increased by a factor of 5 (TODO)
	IP file options
 1. First four Pis
 2. first eight pis
 3. all Pis				(TODO) 

	
