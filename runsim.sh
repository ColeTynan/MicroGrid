#!/bin/bash
#Program runs ratio_consensus, sends output to the remote "accumulator/controller" pi and runsa a remote
#script in order to compile all the outputs from each pi into one CSV file for easy analysis

REMOTE='169.254.136.2'
PINUMFILE='pinum.txt'
PINUM=$(head -n 1 $PINUMFILE)
FILENAME="output$PINUM.CSV"
DEF_GRAPH="/home/pi/graphs/hook.txt"
SIMS=('ratio_consensus_dist.py' 'saddle_point_one_hop.py' 'saddle_point_two_hop.py')
SIM="${SIMS["$1"]}"
GRAPH=$2
REF_FILE=$3

if [[ -z "$GRAPH" ]]; then
	GRAPH="$DEF_GRAPH"
fi

#getting rid of left over output file from previous run, if it exists
if [[ -e "output.CSV" ]]; then
	`rm output.CSV`
fi

echo "$REF_FILE"
`python "$SIM" "$GRAPH" "$REF_FILE"`
#Checks if output.CSV exists first before sending
#Send output to remote location and compile all into one file
if [[ -e "output.CSV" ]]; then
	`cp output.CSV "$FILENAME"`
	`rm output.CSV`
	`scp ./"$FILENAME" pi@"$REMOTE":~/csvFiles/`
	`ssh pi@"$REMOTE" "sh ~/run_comp.sh $REF_FILE"`
fi

