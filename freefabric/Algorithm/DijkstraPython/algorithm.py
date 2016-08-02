#!/usr/bin/env python

__author__ = "Varban Metodiev"

__credits__ = [ " 'Dijkstra's Algorithm - Illustrated Explanation' by Eoin Bailey" ]

__license__ = "GPL"
__version__ = "0.99b"
__maintainer__ = "Varban Metodiev"
__email__ = "varban.metodiev@gmail.com"
__status__ = "Working"


from graph import *

class Dijkstra(object):

    vertexes = []
    neigh_dict = dict()

    start_node = None

    def __init__(self, graph):
        self.vertexes = graph.vertex_list

    def createNeighborNodes(self):

        adj_array = []
        listed_nodes = []
        
        for counter_left in range(len(self.vertexes)):
            left =  self.vertexes[counter_left].getVertexLeftPair().getNodeId()

            if left not in listed_nodes:

                listed_nodes.append(left)
                dictionary = dict()
                
                for counter_right in range(len(self.vertexes)):
                    left_inner = self.vertexes[counter_right].getVertexLeftPair().getNodeId()
                    if (left_inner == left):
                        value = self.vertexes[counter_right].getVertexRightPair()
                        dictionary.update({value.getNodeId():self.vertexes[counter_right].getVertexCost()})
                        print "Dictionary is:", dictionary
                        adj_array.append(value)

                self.neigh_dict.update({left : adj_array})
                adj_array = list()
                self.vertexes[counter_left].getVertexLeftPair().setNeighborCost(dictionary)


    def findSpfDijkstra(self, start_node, inf_distance):

        #Check for starting point
        starting_points = self.neigh_dict.keys()
        print "Starting points are:", starting_points
        
        if start_node not in starting_points:
            print "Cannot start from that node!"
        else:
            print "Starting from:", start_node

        #Mark start point Dist = 0, all other Dist = "INF"
        nodes_list = []
        dijkstra_nodes_list = []

        for key in starting_points:
            index = self.neigh_dict[key]
            print "key:", key, "index", index

            for element in index:
                if (element.getNodeId() == start_node):
                    element.setDistanceFromNode(int(0))

                else:
                    element.setDistanceFromNode(int(inf_distance))
                    
                if element not in nodes_list:
                    nodes_list.append(element)

        for check in nodes_list:
            print "Nodes consistency check:", check.getNodeId(), "with dist:", check.getDistanceFromNode()
             
        #Dijskstra
        while (len(nodes_list) > 0):
            node_with_min_dist = min(nodes_list, key=lambda(item): item.distance_from_node)
            node_with_min_dist.setVisitedFlag()
            distance = node_with_min_dist.getDistanceFromNode()
            
            if (node_with_min_dist.getNodeId() in starting_points):
                for node in self.neigh_dict[node_with_min_dist.getNodeId()]:
                    for element in nodes_list:
                        if (element.getNodeId() == node.getNodeId()):
                            if(element.getVisitedFlag != 1):
                                abc = node_with_min_dist.getNeighborCost(element.getNodeId())
                                if (element.getDistanceFromNode() > distance + node_with_min_dist.getNeighborCost(element.getNodeId())):
                                    element.setDistanceFromNode(distance + node_with_min_dist.getNeighborCost(element.getNodeId()))
                                    element.setPreviousId(node_with_min_dist.getNodeId())

                if (node_with_min_dist.getVisitedFlag != 1):
                    nodes_list.remove(node_with_min_dist)
                    dijkstra_nodes_list.append(node_with_min_dist)
                    starting_points.remove(node_with_min_dist.getNodeId())

            else:
                nodes_list.remove(node_with_min_dist)
                dijkstra_nodes_list.append(node_with_min_dist)

	return dijkstra_nodes_list
			
    def showNeighborNodes(self):
        print "From showNeighborNodes method:\n", self.neigh_dict
