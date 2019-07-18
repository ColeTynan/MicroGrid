#!/bin/bash
#! /usr/bin/expect
#FORMAT: ./send_to_PIs.sh file_to_send.py file_containing_IPs.txt folder

IPs='/mnt/c/Users/cole/Documents/Internship work/microgrid/sync/IP.txt'
file=$1
FOLDER=$2
while read line; do
	`scp $file pi@"$line":~/"$FOLDER"`
done < "$IPs"
echo "File sent"
