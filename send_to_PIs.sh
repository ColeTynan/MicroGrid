#!/bin/bash
#FORMAT: ./send_to_PIs.sh file_to_send.py folder file_containing_IPs.txt 

DEFAULT_IP='/mnt/c/Users/cole/Documents/Internship_Work/microgrid/IPs/allIP.txt'

file=$1
FOLDER=$2
IPs=$3

if [[ -z "$IPs" ]]; then
	IPs=$DEFAULT_IP
fi


while read line; do
	echo "Sending to $line"
	`scp $file pi@"$line":~/"$FOLDER"`
done < "$IPs"
echo "File sent"
