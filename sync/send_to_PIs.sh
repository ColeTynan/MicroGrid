#!/bin/bash

#FORMAT: ./send_to_PIs.sh file_to_send.py file_containing_IPs.txt

IPs=$2
file=$1
while read line; do
	`scp $file pi@"$line":~`
done < $IPs
echo "File sent"
