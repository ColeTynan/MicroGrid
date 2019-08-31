#!/bin/bash
#FORMAT: ./send_to_PIs.sh file_to_send.py folder(optional, leave blank or put 0 to indicate home directory) file_containing_IPs.txt(optional, default is the first eigh Pis)

DEFAULT_IP='/mnt/c/Users/cole/Documents/Internship_Work/microgrid/IPs/eightIP.txt'

FILE=$1
FOLDER=$2
IPs=$3

if [[ -z "$IPs" ]]; then
	IPs=$DEFAULT_IP
fi
if [[ "$2" == "0" ]]; then
	FOLDER=""
fi

while read line; do
	echo "Sending to $line"
	`scp $FILE pi@"$line":~/"$FOLDER"`
done < "$IPs"
echo "Completed sending file"
