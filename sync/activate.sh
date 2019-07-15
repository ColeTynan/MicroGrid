#!/bin/bash

file='IP.txt'
declare -a addresses

let count=0
while read line; do
	echo $line
	addresses[$count]=$line
	((count++))
	
done < $file
