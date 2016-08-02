The project itself:

FreeFabric is an open source SDN forwarding fabric that lies on top of the Ryu Controller. It consists of the following modules:


![Alt text](freefabric/Documentation/Pics/FreeFabric.png?raw=true "FreeFabric Diagram")



- Algorithm – this module wraps a set of Graph algorithms for path finding, currently we have implemented Dijkstra's and Eulerian Path

- FDL – Forwarding Description Language – inspired by the 'Frenetic' language, FDL will be a domain specific language for programming the Fabric's behaviour – for example – dividing the network into segments and writing specific forwarding rules for each segment (define which headers to parse and modify and how to handle the packets)

- Routing Protocols – Quagga deamon for integration with well-known routing protocols like OSPF and BGP

- Management – integration with RADIUS and other protocols for OSS/BSS

- Topology Handler – this module automatically discovers the switches inside the network and the end nodes connected to them (the hosts).

- OFCTL_REST – is a Ryu application that provides a REST interface for the OpenFlow communication


All of the modules should communicate between each other via REST requests and responses.


Current state:

- FDL syntax is about to be defined

- Dijkstra's and Eulerian Path are already implemented, as mentioned above

- The current functionality of the 'Topology Handler' maps all switches, all switch links, all edge hosts, mac-to-ip pairs and mac-to-port pairs

- A manual TRILL-like forwarding with virtual MAC address has been developed as a proof of concept – see Documentation/POC/Forwarding.pdf


Testing and deployment:

- As a development environment, we use the virtual machine from http://sdnhub.org/tutorials/sdn-tutorial-vm/


Goals for the near future:

- Automate the TRILL-like forwarding ('ticket' provisioning via the virual MACs, path calculation via SPF algorithm and OpenFlow rules provisioning after the path has been calculated). This should be developed even if the FDL compiler is not ready.

- Adapt the Topology Handler to OpenStack

- Define the FDL syntax, develop a compiler, adapt all other modules to the generated code by the compiler (FDL should compile to REST calls)


Contribution:

- Any questions, recommendations, criticism and help are welcome!
