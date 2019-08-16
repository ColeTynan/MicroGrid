#!/bin/bash
#Program runs ratio_consensus, sends output to the remote "accumulator/controller" pi and runsa a remote
#script in order to compile all the outputs from each pi into one CSV file for easy analysis

REMOTE='169.254.136.2'
PINUMFILE='pinum.txt'
PINUM=$(head -n 1 $PINUMFILE)
FILENAME="output$PINUM.CSV"

`python ratio_consensus_dist.py`
`cp output.CSV "$FILENAME"`
`scp ./"$FILENAME" pi@"$REMOTE":~/csvFiles/`
`ssh pi@"$REMOTE" "sh ~/runComp.sh"`
