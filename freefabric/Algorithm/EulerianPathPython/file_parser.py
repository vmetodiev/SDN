#!/usr/bin/env python

graph = {}

try:
    nodes_file = open("nodes.txt", "r")
    nodes = nodes_file.read()

    adj_matrix_file = open("adj_matrix.txt", "r")
    adj_matrix = adj_matrix_file.read()
    
except IOError as e:
    print e

else:
    for row,line in enumerate(nodes.split(',')):
        graph[row] = []
    for row,line in enumerate(adj_matrix.split('\n')):
        for col,val in enumerate(line.split(' ')):
            if val == '1':
                graph[row].append(col)


print graph
