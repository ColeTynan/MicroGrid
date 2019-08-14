#!/bin/bash
#use this to run a program on each pi in the background
#USAGE: ./path/activate script_to_run.sh IP_File.txt

DEFAULT_SCRIPT='runratcon.sh'
DEFAULT_IP='/mnt/c/Users/cole/Documents/Internship_Work/microgrid/sync/IP.txt'
SCRIPT=$1
IPs=$2
if [[ -z "$IPs" ]]; then
	IPs=$DEFAULT_IP
fi

if [[ -z "$SCRIPT" ]]; then
	SCRIPT=$DEFAULT_SCRIPT
fi

while read line; do
	 `ssh -n -f pi@"$line" "sh -c 'nohup ~/"$SCRIPT" > stdout.txt 2>&1 &'"`
	 echo "Sent to $line"
done < "$IPs"


#nohup ~/runratcon.sh > foo.out 2> foo.err < /dev/null &"
