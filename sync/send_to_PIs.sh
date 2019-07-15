#!/bin/bash

file='IP.txt'
while read line; do
echo $line
done < $file
