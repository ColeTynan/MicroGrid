#!/bin/bash

#USAGE: ./activate command_to_send

IPs='/mnt/c/Users/cole/Documents/Internship work/microgrid/sync/IP.txt'
CMD=$1
neigh=$2
while read line; do
	 `ssh pi@"$line" \'bash -s\'-- < "$CMD" --"$neigh"`
done < "$IPs"
