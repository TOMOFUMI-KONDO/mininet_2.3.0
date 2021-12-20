from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.lib.packet import ether_types, in_proto, ethernet, ipv4, packet
from ryu.ofproto import ofproto_v1_3

from parsequic import run


class Quic(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    IGNORED_ETHER_TYPES = [ether_types.ETH_TYPE_LLDP, ether_types.ETH_TYPE_IPV6]

    def __init__(self, *args, **kwargs):
        super(Quic, self).__init__(*args, **kwargs)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.__add_flow(datapath, 0, match, actions)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes", ev.msg.msg_len, ev.msg.total_len)

        msg = ev.msg
        dp = msg.datapath
        ofproto = dp.ofproto
        parser = dp.ofproto_parser
        in_port = msg.match['in_port']
        buffer_id = msg.buffer_id

        pkt = packet.Packet(msg.data)
        run(pkt.rest_data, host="192.168.56.1")
        ethertype = pkt.get_protocol(ethernet.ethernet).ethertype

        if ethertype in self.IGNORED_ETHER_TYPES:
            return

        # if ethertype == ether_types.ETH_TYPE_IP:
        #     self.__handle_ip(pkt=pkt, datapath=dp, in_port=in_port)

        data = None
        if buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(
            datapath=dp,
            buffer_id=buffer_id,
            in_port=in_port,
            actions=[parser.OFPActionOutput(ofproto.OFPP_FLOOD)],
            data=data,
        )
        dp.send_msg(out)

    def __handle_ip(self, pkt: packet.Packet, datapath, in_port: int):
        ip = pkt.get_protocol(ipv4.ipv4)

        # install a flow to avoid packet_in next time
        if ip.proto == in_proto.IPPROTO_UDP:
            self.logger.info(
                "ip-packet in datapath:%s ip_src:%s ip_dst:%s in_port:%s protocol:%s",
                datapath.id,
                ip.src,
                ip.dst,
                in_port,
                ip.proto,
            )

    def __add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

        if buffer_id:
            mod = parser.OFPFlowMod(
                datapath=datapath,
                buffer_id=buffer_id,
                priority=priority,
                match=match,
                instructions=inst,
            )
        else:
            mod = parser.OFPFlowMod(
                datapath=datapath,
                priority=priority,
                match=match,
                instructions=inst,
            )

        datapath.send_msg(mod)
