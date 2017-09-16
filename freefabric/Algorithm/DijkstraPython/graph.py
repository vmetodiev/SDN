#!/usr/bin/env python

__author__ = "Varban Metodiev"

__credits__ = [ " 'Dijkstra's Algorithm - Illustrated Explanation' by Eoin Bailey" ]

__license__ = "GPL"
__version__ = "0.99b"
__maintainer__ = "Varban Metodiev"
__email__ = "varban.metodiev@gmail.com"
__status__ = "Working"

class Node(object):
    
    __node_id = None

    previous_id = None
    visited_flag = None
    distance_from_node = None

    neighbor_cost = {}

    def __init__(self, node_id):
        self.__node_id = node_id

    def setPreviousId(self, prev_id):
        self.previous_id = prev_id

    def getPreviousId(self):
        return self.previous_id

    def getNodeId(self):
        return self.__node_id

    def getVisitedFlag(self):
        return self.visited_flag

    def setVisitedFlag(self):
        self.visited_flag = 1

    def getDistanceFromNode(self):
        return self.distance_from_node

    def setDistanceFromNode(self, dist):
        self.distance_from_node = dist

    def setNeighborCost(self, neigh_cost_dict):
        self.neighbor_cost = neigh_cost_dict

    def getNeighborCost(self, node_id):
        node_id_value = int()
        if node_id in self.neighbor_cost.keys():
            node_id_value = int(self.neighbor_cost[node_id])
            return node_id_value


class Vertex(object):
    
    pair_left = None
    pair_right = None
    cost = None

    def __init__(self, left, right, cost):
        self.pair_left = left
        self.pair_right = right
        self.cost = cost

    def getVertexLeftPair(self):
        return self.pair_left

    def getVertexRightPair(self):
        return self.pair_right

    def getVertexCost(self):
        return self.cost

    def printVertexPair(self):
        p_left = self.pair_left.getNodeId()
        p_right = self.pair_right.getNodeId()
        print p_left, p_right, self.cost
        
class Graph(object):
    
    __graph_name = None
    __graph_description = None

    last_vertex = None
    vertex_list = []

    def __init__(self, name, description):
        self.__graph_name = name
        self.__graph_description = description

    def addVertex(self, left, right, cost):
        self.last_vertex = Vertex(left, right, cost)
        self.vertex_list.append(self.last_vertex)
        return self.last_vertex

    def printVertexes(self):
        for counter in range(len(self.vertex_list)):
            self.vertex_list[counter].printVertexPair()
            print "==========="
