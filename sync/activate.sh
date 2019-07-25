#!/bin/bash

#USAGE: ./activate script_to_run 

IPs='/mnt/c/Users/cole/Documents/Internship work/microgrid/sync/IP.txt'
script=$1
param=$2
while read line; do
	 `ssh pi@"$line" python -`
done < "$IPs"
