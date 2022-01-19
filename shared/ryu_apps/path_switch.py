from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.controller import Datapath
from ryu.controller.handler import set_ev_cls, MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.lib.packet import ether_types
from ryu.lib.packet.ether_types import ETH_TYPE_IP
from ryu.lib.packet.ethernet import ethernet
from ryu.lib.packet.packet import Packet
from ryu.ofproto.ofproto_v1_3 import OFPPR_DELETE, OFPP_CONTROLLER, OFPCML_NO_BUFFER, OFP_VERSION, OFP_NO_BUFFER, \
    OFPP_FLOOD
from ryu.ofproto.ofproto_v1_3_parser import OFPPort, OFPPortStatus, OFPMatch, OFPActionOutput, OFPPacketOut, OFPPacketIn

from flow_addable import FlowAddable


class L2Switch(app_manager.RyuApp, FlowAddable):
    OFP_VERSIONS = [OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(L2Switch, self).__init__(*args, **kwargs)
        self.mac_to_port = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        dp: Datapath = ev.msg.datapath
        actions = [OFPActionOutput(OFPP_CONTROLLER, OFPCML_NO_BUFFER)]
        self._add_flow(dp, 0, OFPMatch(), actions)

    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def port_status_handler(self, ev):
        msg: OFPPortStatus = ev.msg
        dp: Datapath = msg.datapath
        desc: OFPPort = msg.desc

        if msg.reason == OFPPR_DELETE:
            print(f"datapath:#{dp.id}")
            print(desc.to_jsondict())

            if dp.id == 4:
                pass

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg: OFPPacketIn = ev.msg
        buffer_id: int = msg.buffer_id
        if msg.buffer_id != OFP_NO_BUFFER:
            return

        data = msg.data
        pkt = Packet(data)
        eth: ethernet = pkt.get_protocol(ethernet)

        # ignore IPv6 ICMP
        if eth.ethertype == ether_types.ETH_TYPE_IPV6:
            return

        dp: Datapath = msg.datapath
        in_port: int = msg.match["in_port"]
        actions = self.__handle_eth(eth, dp, in_port, buffer_id)

        out = OFPPacketOut(
            datapath=dp,
            buffer_id=buffer_id,
            in_port=in_port,
            actions=actions,
            data=data
        )
        dp.send_msg(out)

    def __switch_path(self, datapath: Datapath, out_port: int):
        actions = [OFPActionOutput(out_port), OFPCML_NO_BUFFER]
        self._add_flow(datapath, 1, OFPMatch, actions)

    def __handle_eth(self, eth: ethernet, datapath: Datapath, in_port: int, buffer_id):
        self.mac_to_port.setdefault(datapath.id, {})

        self.logger.info(
            "packet in datapath:%s mac_src:%s mac_dst:%s in_port:%s",
            datapath.id,
            eth.src,
            eth.dst,
            in_port
        )

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[datapath.id][eth.src] = in_port

        if eth.dst in self.mac_to_port[datapath.id]:
            out_port = self.mac_to_port[datapath.id][eth.dst]
        else:
            out_port = OFPP_FLOOD

        actions = [OFPActionOutput(out_port)]

        # if out_port != OFPP_FLOOD:
        #     match = OFPMatch(eth_dst=eth.dst)
        #     self._add_flow(datapath, 100, match, actions, buffer_id)

        return actions
