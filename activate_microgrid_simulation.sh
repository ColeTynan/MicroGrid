#!/bin/bash

#activate_microgrid_simulation.sh
#use this to run a simulation on each pi, which sends all output to a remote machine to compile and format the data acquired
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
IP_FILES=('IPs/fourIP.txt' 'IPs/eightIP.txt' 'IPs/allIP.txt')

REF_FILES=()
for file in ./referenceSignals/*.CSV; do
	REF_FILES+=("$file")
done
	
#REF_FILES=('reg-d-abridged.CSV' 'reg-d.CSV' 'reg-d-factor1000.CSV' 'reg-d-factor1000-abridged.CSV')
#SIM_FILES=('runratcon.sh' 'runsadpoint.sh' 'run_sp_two_step.sh')
DEF_REF=0
DEF_IP=2
DEF_GRAPH=0
DEF_SIM=0
SIM_I=$1
GRAPH_I=$2
REF_I=$3
IP_I=$4

#~~~ Alternative Method of Choosing Parameters ~~~
#Prompt for simulation to run
if [[ -z "$SIM_I" ]]; then
	echo "Which simulation would you like to test?"
	echo -e "Simulations:\n\t1. Ratio Consensus\n\t2. Saddle Point Dynamic (one-hop)\n\t3. Saddle Point Dynamic (two-hop)"
	read -n 1 SIM_I
	echo ""
fi 

if [[ "$SIM_I" -gt 0 ]]; then
	SIM_I="$((SIM_I - 1))"
else
	SIM_I="$DEF_SIM"
fi

#prompt for graph structure
if [[ -z "$GRAPH_I" ]]; then
	echo "Which graph structure would you like to test?"
	for ((i = 0; i < "${#GRAPHS[@]}"; i++)); do
		index="$((i+1))"
		echo -e "\t"$index". ${GRAPHS["$i"]}"
	done
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
	for ((i = 0; i < "${#REF_FILES[@]}"; i++)); do
		index="$((i+1))"
		echo -e "\t"$index". ${REF_FILES["$i"]}"
	done
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

	echo -e "IP file options:
\t1. First four Pis
\t2. first eight pis
\t3. all Pis"
	read -n 1 IP_I
	 echo ""
fi 

if [[ "$IP_I" -gt 0 ]]; then
	IP_I="$((IP_I - 1))"
else
	IP_I="$DEF_IP"
fi

#SIM_I="${SIM_FILES["$SIM_I"]}"
GRAPH_I="${GRAPHS["$GRAPH_I"]}"
IP_I="${IP_FILES["$IP_I"]}"
REF_I="${REF_FILES["$REF_I"]}"

echo "$GRAPH_I"
echo "$IP_I"
echo "$REF_I"

#clear folder containing all output files in the aggregrator
`ssh pi@169.254.136.2 "rm -r csvFiles && mkdir csvFiles"`
while read line; do
	 `ssh -n -f pi@"$line" "sh -c 'nohup ~/runsim.sh "$SIM_I" "$GRAPH_I" "$REF_I" > out.txt 2>&1 &'"`
	 echo "Sent to $line"
done < "$IP_I"

