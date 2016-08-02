#L3 compatibility
#Current version supports IPv4 only

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib import mac
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import arp
from ryu.topology import event, switches
from ryu.topology.api import get_link, get_switch
from ryu.controller import dpset
from ryu.app.wsgi import ControllerBase, WSGIApplication

import threading
import time

import json
import ast
import requests
from webob import Response

# Globals "container"
class GlobalData(object):
    mac_to_port = {}                  # Format: {<dpid>: {'<mac_address>': <port_id>, '<mac_address>': <port_id>, ... }, <dpid>:... }
    mac_to_ip = {}                    # Format: {<dpid>: {'<mac_address>': '<ip_address>', ...} <dpid>:... }
    hosts = {}                        # Format: {<dpid>: {'<mac_address>': <port_id>, '<mac_address>': <port_id>}, <dpid>:... }
    sw_links = []                     # Format: [(2, 1, {'port': 3}), (1, 2, {'port': 1}), ...]
    switch_list = []                  # Format: [1, 2, 3]
    hw_addr = '02:00:00:00:00:01'     # Used for the MAC response, should be modified according to FDL (Forwarding Defitions Logic)

# Globals
threads = []
GlobalTables = GlobalData()

######################################################
# REST API
#
#
# Retrieve the switch stats
#
# get the GlobalTables.mac_to_port {} as JSON
# GET topology_map/mactoport
#
# get the GlobalTables.hosts {} as JSON
# GET topology_map/hosts
#
# get the GlobalTables.sw_links [] as enumerated {} -> JSON
# GET topology_map/sw_links
#
# get the GlobalTables.switch_talbe [] as enumerated {} -> JSON
# GET topology_map/switch_table
#
#####################################################
class TopologyCommunicator(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(TopologyCommunicator, self).__init__(req, link, data, **config)
        self.dpset = data['dpset']
        self.waiters = data['waiters']

    def get_mac_to_port_table(self, req, **_kwargs):
        mac_to_port_table = GlobalTables.mac_to_port
        body = json.dumps(mac_to_port_table)
        return Response(content_type='application/json', body=body)

    def get_mac_to_ip_table(self, req, **_kwargs):
        mac_to_ip_table = GlobalTables.mac_to_ip
        body = json.dumps(mac_to_ip_table)
        return Response(content_type='application/json', body=body)

    def get_hosts_table(self, req, **_kwargs):
        hosts_table = GlobalTables.hosts
        body = json.dumps(hosts_table)
        return Response(content_type='application/json', body=body)

    def get_sw_links_table(self, req, **_kwargs):
        # Convert list to dict and dump it to JSON
        sw_links_table = dict(enumerate(element for element in GlobalTables.sw_links))
        body = json.dumps(sw_links_table)
        return Response(content_type='application/json', body=body)

    def get_switch_table(self, req, **_kwargs):
        # Convert list to dict and dump it to JSON
        switch_table = dict(enumerate(element for element in GlobalTables.switch_list))
        body = json.dumps(switch_table)
        return Response(content_type='application/json', body=body)


class TopologyLearner(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    OFP_LOWEST_PRIO = 0
    OFP_MID_PRIO = 32000
    OFP_HIGH_PRIO = 65000
    ARP_ETHTYPE = 0x0806

    _CONTEXTS = {
        'dpset': dpset.DPSet,
        'wsgi': WSGIApplication
    }

    threadLock = threading.Lock()

    def __init__(self, *args, **kwargs):
        super(TopologyLearner, self).__init__(*args, **kwargs)
        self.dpset = kwargs['dpset']
        wsgi = kwargs['wsgi']
        self.waiters = {}
        self.data = {}
        self.data['dpset'] = self.dpset
        self.data['waiters'] = self.waiters
        mapper = wsgi.mapper

        wsgi.registory['TopologyCommunicator'] = self.data
        path = '/topology_map'

        uri = path + '/mactoport'
        mapper.connect('topology_map', uri,
                       controller=TopologyCommunicator, action='get_mac_to_port_table',
                       conditions=dict(method=['GET']))

        uri = path + '/mactoip'
        mapper.connect('topology_map', uri,
                       controller=TopologyCommunicator, action='get_mac_to_ip_table',
                       conditions=dict(method=['GET']))

        uri = path + '/hosts'
        mapper.connect('topology_map', uri,
                       controller=TopologyCommunicator, action='get_hosts_table',
                       conditions=dict(method=['GET']))

        uri = path + '/sw_links'
        mapper.connect('topology_map', uri,
                       controller=TopologyCommunicator, action='get_sw_links_table',
                       conditions=dict(method=['GET']))

        uri = path + '/switch_table'
        mapper.connect('topology_map', uri,
                       controller=TopologyCommunicator, action='get_switch_table',
                       conditions=dict(method=['GET']))



    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):

        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]

        th_add_flow = threading.Thread(target=self.add_flow, args = (datapath, self.OFP_LOWEST_PRIO, match, actions))
        th_add_flow.start()
        th_add_flow.join()

        match_arp = parser.OFPMatch(eth_type = self.ARP_ETHTYPE)
        th_add_arp_flow = threading.Thread(target=self.add_flow, args = (datapath, self.OFP_HIGH_PRIO, match_arp, actions))
        th_add_arp_flow.start()
        th_add_arp_flow.join()

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

        mod = parser.OFPFlowMod(datapath = datapath, priority = priority, match = match, instructions = inst)

        datapath.send_msg(mod)

    def _send_packet(self, datapath, port, pkt):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        pkt.serialize()
        self.logger.info("packet-out %s" % (pkt,))
        data = pkt.data
        actions = [parser.OFPActionOutput(port=port)]
        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=ofproto.OFPP_CONTROLLER,
                                  actions=actions,
                                  data=data)
        datapath.send_msg(out)


    def is_sw_host_link(self, links, dpid, port_id):
        new_element = []
        links_left_list = [element[0] for element in links]
        links_right_list = [element[1] for element in links]

        if ((dpid in links_left_list) or (dpid in links_right_list)):
            for element in links:
	            if(element[0] == dpid):
		            new_element.append(element)

            for element in new_element:
                if (element[2]["port"] == port_id):
                    return False

            return True

        else:
            return False

    def get_all_hosts(self):
        self.logger.info("All hosts: %s", GlobalTables.hosts)


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        #Execute any remaining threads in the buffer
        for th in threads:
            th.start()
            th.join()
            threads.remove(th)

        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        dst = eth.dst
        src = eth.src

        dpid = datapath.id

        self.learn_host_on_port(dpid, src, in_port)

        #Install a rule not to forward packets from that MAC to OFP_CONTROLLER
        match = parser.OFPMatch(in_port = in_port, eth_src = src)
        actions = []

        th_add_flow = threading.Thread(target=self.add_flow, args = (datapath, self.OFP_LOWEST_PRIO, match, actions))
        th_add_flow.start()
        th_add_flow.join()
        #self.add_flow(datapath, self.OFP_MID_PRIO, match, actions)

        #self.logger.info("hosts: %s", GlobalTables.hosts)

        pkt_ethernet = pkt.get_protocol(ethernet.ethernet)
        if not pkt_ethernet:
            return

        pkt_arp = pkt.get_protocol(arp.arp)
        if pkt_arp:
            self._handle_flex_arp(datapath, in_port, pkt_ethernet, pkt_arp)
        '''
        self.logger.info("mac_to_port: %s", GlobalTables.mac_to_port)
        self.logger.info("mac_to_ip: %s", GlobalTables.mac_to_ip)
        self.logger.info("hosts: %s", GlobalTables.hosts)
        self.logger.info("sw_links: %s", GlobalTables.sw_links)
        self.logger.info("switch_list: %s", GlobalTables.switch_list)
        '''

    def _handle_flex_arp(self, datapath, port, pkt_ethernet, pkt_arp):
        if pkt_arp.opcode != arp.ARP_REQUEST:
            return

        #Learn the MAC to IP
        mac_lst = []
        for each_key in GlobalTables.mac_to_port.keys():
	        x = GlobalTables.mac_to_port[each_key]
	        for mac,port in x.iteritems():
		        mac_lst.append(mac)

        if (pkt_arp.src_mac in mac_lst):
            self.learn_mac_to_ip(datapath.id, pkt_arp.src_mac, pkt_arp.src_ip)
            self.logger.info("INFO: New MAC_TO_IP: %s", GlobalTables.mac_to_ip)


        pkt = packet.Packet()
        pkt.add_protocol(ethernet.ethernet(ethertype = pkt_ethernet.ethertype,
                                           dst = pkt_ethernet.src,
                                           src = GlobalTables.hw_addr))

        pkt.add_protocol(arp.arp(opcode = arp.ARP_REPLY,
                                 src_mac = '02:00:00:00:00:01',
                                 src_ip = pkt_arp.dst_ip,
                                 dst_mac = pkt_arp.src_mac,
                                 dst_ip = pkt_arp.src_ip))

        self.logger.info("INFO: Sending FlexARP response")
        self._send_packet(datapath, port, pkt)

    def _relocate_host_from_table(self, table, key_arg):
        #Check if an entry for that pair exists, is so, remove it (host has just migrated)
        for element in table:
	        for key,value in table[element].iteritems():
			    if key == key_arg:
				    table[element].pop(key)
				    break


    def learn_mac_to_ip(self, dpid, mac, ipv4_src):
#        try:
#            GlobalTables.mac_to_ip[mac] = ipv4_src
#            self.logger.info("MAC_TO_IP=%s", GlobalTables.mac_to_ip)
#        except(KeyError, AttributeError), err:
#            self.logger.info("Error making the MAC_TO_IP association")

        #Check if an entry for that MAC-IP pair exists, is so, remove it (host has just migrated)
        self._relocate_host_from_table(GlobalTables.mac_to_ip, mac)
#        for element in GlobalTables.mac_to_ip:
#	        for key,value in GlobalTables.mac_to_ip[element].iteritems():
#			    if key == mac:
#				    GlobalTables.mac_to_ip[element].pop(key)
#				    break

        #Learn the mac_to_ip association
        self.threadLock.acquire()
        GlobalTables.mac_to_ip.setdefault(dpid, {})
        GlobalTables.mac_to_ip[dpid][mac] = ipv4_src
        self.threadLock.release()

    def learn_host_on_port(self, dpid, src, in_port):
        self._relocate_host_from_table(GlobalTables.mac_to_port, src)
        self._relocate_host_from_table(GlobalTables.hosts, src)
        #Check if an entry for that MAC-Port pair exists, is so, remove it (host has just migrated)
#        for element in GlobalTables.mac_to_port:
#	        for key,value in GlobalTables.mac_to_port[element].iteritems():
#			    if key == src:
#				    GlobalTables.mac_to_port[element].pop(key)
#				    break

        #Learn the mac address that is present on the port
        self.threadLock.acquire()
        GlobalTables.mac_to_port.setdefault(dpid, {})
        GlobalTables.mac_to_port[dpid][src] = in_port

        #Learn the host that is present on the port
        if ( (self.is_sw_host_link(GlobalTables.sw_links, dpid, in_port)) and (len(threads) == 0) ):
            GlobalTables.hosts.setdefault(dpid, {})
            GlobalTables.hosts[dpid][src] = in_port
            self.get_all_hosts()

        else:
            self.logger.info("Pending threads: %s", threads)

        self.threadLock.release()

    def get_topology_data(self):
        self.threadLock.acquire()

        #Delay a second for the LLDP to propagate
        time.sleep(1)

        switch_list = get_switch(self, None)
        GlobalTables.switch_list = [switch.dp.id for switch in switch_list]
        links_list = get_link(self, None)
        GlobalTables.sw_links = [(link.src.dpid, link.dst.dpid, {'port': link.src.port_no}) for link in links_list]

        self.threadLock.release()

        self.logger.info("sw_links: %s", GlobalTables.sw_links)
        self.logger.info("hosts: %s", GlobalTables.hosts)
        self.logger.info("mac_to_port: %s", GlobalTables.mac_to_port)

    def delete_connections(self, dpid):
        self.logger.info("Switch leaved the network")

        self.threadLock.acquire()

        try:
            GlobalTables.sw_links = []
            del GlobalTables.mac_to_port[dpid]
            del GlobalTables.hosts[dpid]
            del GlobalTables.mac_to_ip[dpid]

            self.logger.info("sw_links: %s", GlobalTables.sw_links)
            self.logger.info("hosts: %s", GlobalTables.hosts)
            self.logger.info("mac_to_port: %s", GlobalTables.mac_to_port)

        except (AttributeError, KeyError), err:
            self.logger.info("AttributeError caught")
            self.logger.info(err)


        self.threadLock.release()
        self.get_topology_data()


    @set_ev_cls(event.EventLinkAdd)
    def _event_link_add_handler(self, ev):
        self.logger.info("EventLinkAdd Event Caught")
        dpid = ev.link.src.dpid
        #get topo data
        th_get_topo_data = threading.Thread(target=self.get_topology_data, )
        threads.append(th_get_topo_data)

        for th in threads:
            th.start()
            th.join()
            threads.remove(th)

        th_get_topo_data = None


    @set_ev_cls(event.EventLinkDelete)
    def _event_link_delete_handler(self, ev):
        self.logger.info("EventLinkDelete Event Caught")
        dpid = ev.link.src.dpid
        #delete connections
        th_delete_connections = threading.Thread(target=self.delete_connections, args = (dpid, ))
        #get topo data
        th_get_topo_data = threading.Thread(target=self.get_topology_data, )

        threads.append(th_delete_connections)
        threads.append(th_get_topo_data)

        for th in threads:
            th.start()
            th.join()
            threads.remove(th)

        th_delete_connections = None
        th_get_topo_data = None


    @set_ev_cls(event.EventSwitchEnter)
    def _event_switch_enter_handler(self, ev):
        dpid = ev.switch.dp.id
        #get topo data
        th_get_topo_data = threading.Thread(target=self.get_topology_data, )

        threads.append(th_get_topo_data)

        for th in threads:
            th.start
            th.join
            threads.remove(th)

        th_get_topo_data = None


    @set_ev_cls(event.EventSwitchLeave)
    def _event_switch_leave_handler(self, ev):
        dpid = ev.switch.dp.id
        th_delete_connections = threading.Thread(target=self.delete_connections, args = (dpid, ))
        #get topo data
        th_get_topo_data = threading.Thread(target=self.get_topology_data, )

        threads.append(th_delete_connections)
        threads.append(th_get_topo_data)

        for th in threads:
            th.start()
            th.join()
            threads.remove(th)

        th_delete_connections = None
        th_get_topo_data = None