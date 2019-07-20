#!/bin/bash
#!/usr/bin/expect

IPs='/mnt/c/Users/jiami/Desktop/VSCode_srip/sync/IP.txt'
file=$1
FOLDER=$2
while read line; do
	`scp "$file" pi@"$line":~/"$FOLDER"`
done < "$IPs"
echo "File sent"
