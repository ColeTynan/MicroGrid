#!/bin/bash

#FORMAT: ./send_to_PIs.sh file_to_send.py file_containing_IPs.txt folder

IPs="IP.txt"
file=$1
FOLDER=$3
while read line; do
	`scp $file pi@"$line":~/"$FOLDER"`
done < $IPs
echo "File sent"
