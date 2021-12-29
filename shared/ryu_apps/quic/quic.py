from ryu.base import app_manager
from ryu.controller import ofp_event, controller
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.lib.packet import ether_types, in_proto, ethernet, ipv4, packet, udp
from ryu.ofproto import ofproto_v1_3

from flow_addable import FlowAddable
from parsequic import run


class Quic(app_manager.RyuApp, FlowAddable):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    IGNORED_ETHER_TYPES = [ether_types.ETH_TYPE_LLDP, ether_types.ETH_TYPE_IPV6]

    def __init__(self, *args, **kwargs):
        super(Quic, self).__init__(*args, **kwargs)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        dp = ev.msg.datapath
        proto = dp.ofproto
        parser = dp.ofproto_parser

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(proto.OFPP_CONTROLLER, proto.OFPCML_NO_BUFFER)]
        self._add_flow(dp, 0, match, actions)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes", ev.msg.msg_len, ev.msg.total_len)

        msg = ev.msg
        dp = msg.datapath
        proto = dp.ofproto
        parser = dp.ofproto_parser
        in_port = msg.match['in_port']
        buf_id = msg.buffer_id

        pkt = packet.Packet(msg.data)
        ethertype = pkt.get_protocol(ethernet.ethernet).ethertype

        if ethertype in self.IGNORED_ETHER_TYPES:
            return

        data = None
        if buf_id == proto.OFP_NO_BUFFER:
            data = msg.data

        if ethertype == ether_types.ETH_TYPE_IP:
            self.__handle_ip(data=data, pkt=pkt, datapath=dp, in_port=in_port, buffer_id=buf_id)

        # flood packet
        out = parser.OFPPacketOut(
            datapath=dp,
            buffer_id=buf_id,
            in_port=in_port,
            actions=[parser.OFPActionOutput(proto.OFPP_FLOOD)],
            data=data,
        )
        dp.send_msg(out)

    def __handle_ip(self, data, pkt: packet.Packet, datapath: controller.Datapath, in_port: int, buffer_id: int):
        ip = pkt.get_protocol(ipv4.ipv4)
        parser = datapath.ofproto_parser

        if ip.proto == in_proto.IPPROTO_UDP:
            u = pkt.get_protocol(udp.udp)
            self.logger.info(
                "udp-packet in datapath:%s %s:%s -> %s:%s in_port:%s",
                datapath.id,
                ip.src,
                u.src_port,
                ip.dst,
                u.dst_port,
                in_port
            )
            run(pkt.rest_data, host="192.168.56.1")
