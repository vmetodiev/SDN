#
# ARP Handler for virtual MAC provisioning
#

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

import json
import ast
import requests
from webob import Response

######################################################
# REST API
#
#
# get the GlobalTables.mac_to_ip {} as JSON
# GET arpoverrider/mactoip
#
#
######################################################

# Globals "container"
class GlobalData(object):
    mac_to_ip = {}                    # Format: {<dpid>: {'<mac_address>': '<ip_address>', ...} <dpid>:... }

# Globals
GlobalTables = GlobalData()


class ArpOverriderCommunicator(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(ArpOverriderCommunicator, self).__init__(req, link, data, **config)
        self.dpset = data['dpset']
        self.waiters = data['waiters']

    def get_mac_to_ip_table(self, req, **_kwargs):
        mac_to_ip_table = GlobalTables.mac_to_ip
        body = json.dumps(mac_to_ip_table)
        return Response(content_type='application/json', body=body)


class ArpOverrider(app_manager.RyuApp):
    _CONTEXTS = {
        'dpset': dpset.DPSet,
        'wsgi': WSGIApplication
    }

    def __init__(self, *args, **kwargs):
        super(ArpOverrider, self).__init__(*args, **kwargs)
        self.dpset = kwargs['dpset']
        wsgi = kwargs['wsgi']
        self.waiters = {}
        self.data = {}
        self.data['dpset'] = self.dpset
        self.data['waiters'] = self.waiters
        mapper = wsgi.mapper

        wsgi.registory['ArpOverriderCommunicator'] = self.data
        path = '/arpoverrider'

        uri = path + '/mactoip'
        mapper.connect('arpoverrider', uri,
                       controller=ArpOverriderCommunicator, action='get_mac_to_ip_table',
                       conditions=dict(method=['GET']))


    def _send_packet(self, datapath, port, pkt):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        pkt.serialize()
        self.logger.info("Packet-out %s" % (pkt,))
        data = pkt.data
        actions = [parser.OFPActionOutput(port=port)]
        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=ofproto.OFPP_CONTROLLER,
                                  actions=actions,
                                  data=data)
        datapath.send_msg(out)


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        pkt_arp = pkt.get_protocol(arp.arp)
        if pkt_arp:
            self._handle_arp_overrider(datapath, in_port, pkt_ethernet, pkt_arp)


    def _handle_arp_overrider(self, datapath, port, pkt_ethernet, pkt_arp):
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

        #Generate response
        pkt = packet.Packet()
        pkt.add_protocol(ethernet.ethernet(ethertype = pkt_ethernet.ethertype,
                                           dst = pkt_ethernet.src,
                                           src = GlobalTables.hw_addr))

        pkt.add_protocol(arp.arp(opcode = arp.ARP_REPLY,
                                 src_mac = '02:00:00:00:00:01',
                                 src_ip = pkt_arp.dst_ip,
                                 dst_mac = pkt_arp.src_mac,
                                 dst_ip = pkt_arp.src_ip))

        self.logger.info("INFO: Sending ARPOverrider response")
        self._send_packet(datapath, port, pkt)

    def _relocate_host_from_table(self, table, key_arg):
        #Check if an entry for that pair exists, is so, remove it (host has just migrated)
        for element in table:
	        for key,value in table[element].iteritems():
			    if key == key_arg:
				    table[element].pop(key)
				    break

    def learn_mac_to_ip(self, dpid, mac, ipv4_src):
        self._relocate_host_from_table(GlobalTables.mac_to_ip, mac)

        #Learn the mac_to_ip association
        GlobalTables.mac_to_ip.setdefault(dpid, {})
        GlobalTables.mac_to_ip[dpid][mac] = ipv4_src


