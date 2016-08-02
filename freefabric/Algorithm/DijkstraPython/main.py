#!/usr/bin/env python

__author__ = "Varban Metodiev"
__credits__ = [ " 'Dijkstra's Algorithm - Illustrated Explanation' by Eoin Bailey" ]
__license__ = "GPL"
__version__ = "0.99b"
__maintainer__ = "Varban Metodiev"
__email__ = "varban.metodiev@gmail.com"
__status__ = "Working"

from dijkstra import *

#Create nodes
node1 = Node(1)
node2 = Node(2)
node3 = Node(3)
node4 = Node(4)
node5 = Node(5)
node6 = Node(6)
node7 = Node(7)
node8 = Node(8)
node9 = Node(9)


#Create Graph
tmpGraph = Graph("TheGraph", "WeightedGraph")

tmpGraph.addVertex(node1, node2, 7)
tmpGraph.addVertex(node2, node1, 7)

tmpGraph.addVertex(node1, node3, 4)
tmpGraph.addVertex(node3, node1, 4)

tmpGraph.addVertex(node2, node3, 2)
tmpGraph.addVertex(node3, node2, 2)

tmpGraph.addVertex(node1, node4, 5)
tmpGraph.addVertex(node4, node1, 5)

tmpGraph.addVertex(node2, node5, 25)
tmpGraph.addVertex(node5, node2, 25)

tmpGraph.addVertex(node3, node8, 9)
tmpGraph.addVertex(node8, node3, 9)

tmpGraph.addVertex(node4, node6, 9)
tmpGraph.addVertex(node6, node4, 9)

tmpGraph.addVertex(node5, node7, 10)
tmpGraph.addVertex(node7, node5, 10)

tmpGraph.addVertex(node6, node8, 20)
tmpGraph.addVertex(node8, node6, 20)

tmpGraph.addVertex(node7, node9, 2)
tmpGraph.addVertex(node9, node7, 2)

tmpGraph.addVertex(node8, node9, 3)
tmpGraph.addVertex(node9, node8, 3)

print "Graph:"
tmpGraph.printVertexes()

#Set node distances, choose start node
tmpDijkstra = Dijkstra(tmpGraph)
tmpDijkstra.createNeighborNodes()
tmpDijkstra.showNeighborNodes()

#SPF - Setting Max distance to 555
spf_list = tmpDijkstra.findSpfDijkstra(1, 555)
print "Showing path from node7 to the start node:"
tmpDijkstra.showPathFromNode(node7, spf_list);
