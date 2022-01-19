from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import set_ev_cls, MAIN_DISPATCHER
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import ether_types, ethernet, packet, arp
from ryu.ofproto import ofproto_v1_0


class ArpProxy(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

    ARP_TABLE = {
        "10.0.0.1": "00:00:00:00:00:01",
        "10.0.0.2": "00:00:00:00:00:02",
        "10.0.0.3": "00:00:00:00:00:03",
        "10.0.0.4": "00:00:00:00:00:01",
    }

    def __init__(self, *args, **kwargs):
        super(ArpProxy, self).__init__(*args, **kwargs)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes", ev.msg.msg_len, ev.msg.total_len)

        msg = ev.msg
        dp = msg.datapath
        proto = dp.ofproto
        parser = dp.ofproto_parser
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        # ignore LLDP packet
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        if eth.dst[:5] == "33:33":
            self.logger.info("drop ipv6 multicast packet %s", eth.dst)
            return

        if eth.ethertype == ether_types.ETH_TYPE_ARP:
            self.logger.info("Received ARP Packet %s: %s -> %s", dp.id, eth.src, eth.dst)

            self.__process_arp(dp, eth, pkt.get_protocol(arp.arp), msg.in_port)
            return

        data = None
        if msg.buffer_id == proto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(
            datapath=dp,
            buffer_id=(msg.buffer_id),
            in_port=(msg.in_port),
            actions=[parser.OFPActionOutput(proto.OFPP_FLOOD)],
            data=data,
        )

        dp.send_msg(out)

    def __process_arp(self, datapath, eth, a, in_port):
        dst_mac = self.ARP_TABLE.get(a.dst_ip)

        if dst_mac:
            self.logger.info("Matched MAC %s", dst_mac)

            arp_resp = packet.Packet()
            arp_resp.add_protocol(ethernet.ethernet(
                ethertype=eth.ethertype,
                dst=eth.src,
                src=dst_mac
            ))
            arp_resp.add_protocol(arp.arp(
                opcode=arp.ARP_REPLY,
                src_mac=dst_mac,
                src_ip=a.dst_ip,
                dst_mac=a.src_mac,
                dst_ip=a.src_ip
            ))
            arp_resp.serialize()

            parser = datapath.ofprot_parser
            proto = datapath.ofproto

            actions = [parser.OFPActionOutput(in_port)]
            out = parser.OFPPacketOut(
                datapath=datapath,
                buffer_id=proto.OFP_NO_BUFFER,
                in_port=proto.OFPP_CONTROLLER,
                actions=actions,
                data=arp_resp
            )

            datapath.send_msg(out)

            self.logger.info("Proxied ARP Response packet")

    def __add_flow(self, datapath, in_port, mac_src, mac_dst, actions):
        parser = datapath.ofproto_parser
        proto = datapath.ofproto

        match = parser.OFPMatch(
            in_port=in_port,
            dl_src=haddr_to_bin(mac_src),
            dl_dst=haddr_to_bin(mac_dst),
        )
        mod = parser.OFPFlowMod(
            datapath=datapath,
            match=match,
            cookie=0,
            command=proto.OFPFC_ADD,
            idle_timeout=0,
            hard_timeout=0,
            flags=proto.OFPFF_SEND_FLOW_REM,
            actions=actions
        )

        datapath.send_msg(mod)
