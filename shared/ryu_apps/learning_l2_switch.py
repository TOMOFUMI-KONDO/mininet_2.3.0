import json

from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_0
from ryu.controller import ofp_event
from ryu.controller.handler import set_ev_cls, MAIN_DISPATCHER
from ryu.lib.packet.packet import Packet
from ryu.lib.packet.ethernet import ethernet
from ryu.lib.mac import haddr_to_bin


class LearningL2Switch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(LearningL2Switch, self).__init__(*args, **kwargs)
        self.mac_to_port = {}

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg

        dp = msg.datapath
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        in_port = msg.in_port

        packet = Packet(msg.data)
        eth = packet.get_protocol(ethernet)
        mac_src = eth.src
        mac_dst = eth.dst

        print(f"PACKET_IN mac_src:{mac_src} mac_dst:{mac_dst} in_port:{in_port}")

        if mac_src not in self.mac_to_port:
            self.mac_to_port[mac_src] = msg.in_port
            print(f"Updated mac_to_port\n{self.mac_to_port}")

        if mac_dst in self.mac_to_port:
            out_port = self.mac_to_port[mac_dst]
        else:
            out_port = ofp.OFPP_FLOOD

        actions = [ofp_parser.OFPActionOutput(out_port)]

        if out_port != ofp.OFPP_FLOOD:
            self.__add_flow(dp, in_port, mac_src, mac_dst, actions)

        data = None
        if msg.buffer_id == ofp.OFP_NO_BUFFER:
            data = msg.data

        out = ofp_parser.OFPPacketOut(
            datapath=dp,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=data,
        )

        dp.send_msg(out)

    def __add_flow(self, datapath, in_port, mac_src, mac_dst, actions):
        ofp_parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        match = ofp_parser.OFPMatch(
            in_port=in_port,
            dl_src=haddr_to_bin(mac_src),
            dl_dst=haddr_to_bin(mac_dst),
        )
        mod = ofp_parser.OFPFlowMod(
            datapath=datapath,
            match=match,
            cookie=0,
            command=ofproto.OFPFC_ADD,
            idle_timeout=0,
            hard_timeout=0,
            flags=ofproto.OFPFF_SEND_FLOW_REM,
            actions=actions
        )
        datapath.send_msg(mod)
