#!/bin/bash


r1=169.254.86.232
r2=169.254.142.58
r3=169.254.180.72
r4=169.254.160.208

Nodes[1]=r1
Nodes[2]=r2
Nodes[3]=r3
Nodes[4]=r4

r1_neighbor_1=${r2}
r1_neighbor_2=${r3}

r2_neighbor_1=${r1}
r2_neighbor_2=${r4}

r3_neighbor_1=${r1}
r3_neighbor_2=${r4}

r4_neighbor_1=${r2}
r4_neighbor_2=${r3}

Neighbor_1[1]=r1_neighbor_1
Neighbor_1[2]=r2_neighbor_1
Neighbor_1[3]=r3_neighbor_1

sed -i "s/this_ip"