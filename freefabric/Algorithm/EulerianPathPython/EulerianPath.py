#!/usr/bin/env python

import random

graph = {}

#An undirected graph has an eulerian path if and only if it is connected and all vertices except 2 have even degree.
#One of those 2 vertices that have an odd degree must be the start vertex, and the other one must be the end vertex.

#Helper fucntions
def check_for_eulerian_path(graph):

    even_deg = 0
    odd_deg = 0

    even_deg_nodes = []
    odd_deg_nodes = []

    #Check if graph is not connected
    for key in graph:
        if len(graph[key]) == 0:
            raise Exception("Unconnected graph!")

    for key in graph:
        if len(graph[key]) % 2 == 0:
            even_deg += 1
            even_deg_nodes.append(key)
        else:
            odd_deg += 1
            odd_deg_nodes.append(key)

    if odd_deg == 0:
        print "Nodes with even deg:", even_deg
        print "Nodes with odd deg:", odd_deg
        return even_deg_nodes

    if odd_deg == 2:
        print "Even deg:", even_deg
        print "Odd deg:", odd_deg
        return odd_deg_nodes

    else:
        raise Exception("There is no Eulerian path for this graph")

def remove_edge(u, v):
    u_adj = graph[u]
    v_adj = graph[v]
    
    u_ptr = graph[u].index(v)
    v_ptr = graph[v].index(u)

    del u_adj[u_ptr]
    del v_adj[v_ptr]

#The function
def get_eulerian_path(nodes, matrix):

    stack = []
    location = -1
    path = []
    path_edges_tuple = []
    end_points = []

    try:
        nodes_file = open(nodes, "r")
        nodes = nodes_file.read()

        adj_matrix_file = open(matrix, "r")
        adj_matrix = adj_matrix_file.read()
    
    except (IOError, OSError) as e:
        print "Error opening file:", e
    
    else:
        for row,line in enumerate(nodes.split(',')):
            graph[row] = []
        for row,line in enumerate(adj_matrix.split('\n')):
            for col,val in enumerate(line.split(' ')):
                if val == '1':
                    graph[row].append(col)
                    
    finally:
        nodes_file.close()
        adj_matrix_file.close()
    

    print "Graph:", graph
                    
    try:
        end_points = check_for_eulerian_path(graph)
    except Exception as e:
        print e

    else:
        location = random.choice(end_points) #Pick up a stack location at random (arrangement not important for undirected graph)
        stack.append(555) #Initialize the stack with fake value to emulate do-while loop
        
        while (stack):
            while (graph[location]):
                prev_location = location
                stack.append(prev_location)
                location = graph[location][0]
                remove_edge(prev_location, location)
                path_edges_tuple.append((prev_location, location))

            if stack[0] == 555:
                del stack[0]
                
            path.append(location)
            location = stack.pop()

        path.append(location)
        return path_edges_tuple
        #return path
    
path_edges_tuple = get_eulerian_path("nodes.txt", "adj_matrix.txt")
print "Path edges:", path_edges_tuple
