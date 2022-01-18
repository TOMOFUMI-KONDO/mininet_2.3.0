from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import set_ev_cls, MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.lib.packet import ether_types, packet, ethernet, lldp
from ryu.ofproto import ofproto_v1_3
from flow_addable import FlowAddable


class LLDP(app_manager.RyuApp, FlowAddable):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(LLDP, self).__init__(*args, **kwargs)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        dp = ev.msg.datapath
        proto = dp.ofproto
        parser = dp.ofproto_parser

        match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_LLDP)
        actions = [parser.OFPActionOutput(proto.OFPP_CONTROLLER, proto.OFPCML_NO_BUFFER)]
        self._add_flow(dp, 65535, match, actions)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath

        if msg.buffer_id != dp.ofproto.OFP_NO_BUFFER:
            return

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        if eth is None or eth.ethertype != ether_types.ETH_TYPE_LLDP:
            return

        l = pkt.get_protocol(lldp.lldp)
        print(l.tlvs)

