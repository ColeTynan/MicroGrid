#!/bin/bash

#activateRunRatCon.sh
#use this to run the script that runs the ratio consensus program on each pi, which sends all output to a remote machine to compile and format the data acquired
#USAGE: ./path/activate graph_structure(integer value from 0-7) reference_file(int value) IP_File.txt(int value) [leave as 0 for defaults]
#Alternate usage: Run without parameters and you will be prompted for them
#	Graph structure options (figures in accompanying document)
# 1. ring4.txt					-- ring of four agents
# 2. ring8.tx						-- ring of eight agents
# 4. smallASym.txt			-- small asymmetrical structure of four agents
# 5. hook.txt						-- shaped like a "hook" or a linked list
# 6. treeBal7.txt				-- a balanced binary tree strcture
# 7. treeUnb7.txt				-- unbalanced binary tree
#	reference file options
# 1. reg-d-abridged.CSV -- the first ten values from reg-d
# 2. reg-d.CSV					-- The full reg-d file, containing 1200 entries
# 3. reg-d-factor5.CSV	-- reg-d but every value is increased by a factor of 5 (TODO)
#	IP file options
# 1. First four Pis
# 2. first eight pis
# 3. all Pis				(TODO) 

FORMAT_REMINDER='USAGE: ./path/activate graph_structure(integer value from 0-7) reference_file(int value) IP_File.txt(int value) [leave as 0 for defaults]'
SCRIPT='runratcon.sh'
GRAPHS=('graphs/ring4.txt' 'graphs/ring8.txt' 'graphs/smallASym1.txt' 'graphs/smallASym2.txt' 'graphs/hook.txt' 'graphs/treeBal7.txt' 'graphs/treeUnb7.txt')
IP_FILES=('IPs/fourIP.txt' 'IPs/eightIP.txt')
REF_FILES=('reg-d-abridged.CSV' 'reg-d.CSV' 'reg-d-factor5.CSV')
DEF_REF=0
DEF_IP=0
DEF_GRAPH=0

GRAPH_I=$1
REF_I=$2
IP_I=$3

#~~~ Alternative Method of Choosing Parameters ~~~
#prompt for graph structure
if [[ -z "$GRAPH_I" ]]; then
	echo "Which graph structure would you like to test?"
	echo "Graph structure options (See accompanying PDF for illustrations):
	 1. ring4.txt						-- ring of four agents
	 2. ring8.tx						-- ring of eight agents
	 4. smallASym.txt				-- small asymmetrical structure of four agents
	 5. hook.txt						-- shaped like a "hook" or a linked list
	 6. treeBal7.txt				-- a balanced binary tree strcture
	 7. treeUnb7.txt				-- unbalanced binary tree "
	read -n 1 GRAPH_I
	echo ""
fi 

if [[ "$GRAPH_I" -gt 0 ]]; then
	GRAPH_I="$((GRAPH_I - 1))"
else
	GRAPH_I="$DEF_GRAPH"
fi

#Getting reference signal if not used as command line input
if [[ -z "$REF_I" ]]; then
	echo "Which reference signal data file would you like to use?"
	echo "Reference file options:
	 1. reg-d-abridged.CSV	-- the first ten values from reg-d.
	 2. reg-d.CSV						-- The full reg-d file, containing 1200 entries. Takes ~40 minutes. 
	 3. reg-d-factor5.CSV		-- reg-d but every value is increased by a factor of 5 (TODO, unavailable)"
	read -n 1 REF_I
	echo ""
fi

if [[ "$REF_I" -gt 0 ]]; then
	REF_I="$((REF_I - 1))"
else
	REF_I="$DEF_REF"
fi

#Getting input for IP file (TODO: provide a workaround for this. Usually running on all pis doesnt cause problems)
if [[ -z "$IP_I" ]]; then
	echo "IP file options: (will remove this option later, not necessary)
	 1. First four Pis
	 2. first eight pis
	 3. all Pis				(TODO, not available yer)" 
	 read -n 1 IP_I
	 echo ""
fi 

if [[ "$IP_I" -gt 0 ]]; then
	IP_I="$((IP_I - 1))"
else
	IP_I="$DEF_IP"
fi


GRAPH_I="${GRAPHS["$GRAPH_I"]}"
IP_I="${IP_FILES["$IP_I"]}"
REF_I="${REF_FILES["$REF_I"]}"

echo "$GRAPH_I"
echo "$IP_I"
echo "$REF_I"

#clear folder containing all output files in the aggregrator
`ssh pi@169.254.136.2 "rm -r csvFiles && mkdir csvFiles"`
while read line; do
	 `ssh -n -f pi@"$line" "sh -c 'nohup ~/"$SCRIPT" "$GRAPH_I" "$REF_I" > out.txt 2>&1 &'"`
	 echo "Sent to $line"
done < "$IP_I"
