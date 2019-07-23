#!/bin/bash

file=$1
IPs='/mnt/c/Users/jiami/Desktop/VSCode_srip/ip_list.txt'
echo "Starting..."
while read line; do
	command="scp ${file} pi@${line}:~"
	echo $command
	eval $command
done < "$IPs"
echo "File sent"