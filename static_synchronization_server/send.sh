#!/bin/bash
file=$1
IPs='/mnt/c/Users/jiami/Desktop/VSCode_srip/static_synchronization_server/IP.txt'
echo "Starting..."
while read line; do
	command="scp ${file} pi@${line}:~/static_synchronization_server/"
	echo $command
	eval $command
done < "$IPs"
echo "File sent"