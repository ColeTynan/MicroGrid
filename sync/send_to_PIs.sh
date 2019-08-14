#!/bin/bash
#! /usr/bin/expect
#FORMAT: ./send_to_PIs.sh file_to_send.py file_containing_IPs.txt folder

DEFAULT_IP='/mnt/c/Users/cole/Documents/Internship_Work/microgrid/sync/IP.txt'

file=$1
IPs=$2
if [[ -z "$IPs" ]]; then
	IPs=$DEFAULT_IP
fi

FOLDER=$3

while read line; do
	`scp $file pi@"$line":~/"$FOLDER"`
done < "$IPs"
echo "File sent"
