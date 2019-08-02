#!/bin/bash

#USAGE: ./activate script_to_run 

IPs='/mnt/c/Users/cole/Documents/Internship_Work/microgrid/sync/IP.txt'
while read line; do
	 `ssh -n -f pi@"$line" "sh -c 'nohup ~/runratcon.sh > /dev/null 2>&1 &'"`
	 echo "Sent to $line"
done < "$IPs"


#nohup ~/runratcon.sh > foo.out 2> foo.err < /dev/null &"
