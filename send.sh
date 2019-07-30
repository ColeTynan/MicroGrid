#!/bin/bash

file=$1
IPs='/mnt/c/Users/jiami/Desktop/VSCode_srip/sync/IP.txt'
echo "Starting..."
while read line; do
	command="scp ${file} pi@${line}:~/sync/"
	echo $command
	eval $command
done < "$IPs"
echo "File sent"