from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import set_ev_cls, CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.lib.packet import ether_types, ethernet, packet
from ryu.ofproto import ofproto_v1_3


class GroupTableSwitch(app_manager.RyuApp):
    LB_WEIGHT_1 = 100
    LB_WEIGHT_2 = 100 - LB_WEIGHT_1

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(GroupTableSwitch, self).__init__(*args, **kwargs)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.__add_flow(datapath, 0, match, actions)

        if datapath.id in [1, 4]:
            self.__send_group_mod(datapath)

            actions = [parser.OFPActionGroup(group_id=50)]
            match = parser.OFPMatch(in_port=3)
            self.__add_flow(datapath, 10, match, actions)

            actions = [parser.OFPActionGroup(group_id=51)]
            match = parser.OFPMatch(in_port=3)
            self.__add_flow(datapath, 10, match, actions)

        else:
            actions = [parser.OFPActionOutput(2)]
            match = parser.OFPMatch(in_port=1)
            self.__add_flow(datapath, 10, match, actions)

            actions = [parser.OFPActionOutput(1)]
            match = parser.OFPMatch(in_port=2)
            self.__add_flow(datapath, 10, match, actions)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes", ev.msg.msg_len, ev.msg.total_len)

        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        buffer_id = msg.buffer_id

        data = None
        if buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        pkt = packet.Packet(data)
        eth = pkt.get_protocol(ethernet.ethernet)

        # ignore LLDP packet
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        if eth.dst[:5] == "33:33":
            self.logger.info("drop ipv6 multicast packet %s", eth.dst)
            return

        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=buffer_id,
            in_port=in_port,
            actions=[parser.OFPActionOutput(ofproto.OFPP_FLOOD)],
            data=data
        )
        datapath.send_msg(out)

    def __send_group_mod(self, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        watch_port = ofproto.OFPP_ANY
        watch_group = ofproto.OFPQ_ALL

        action_output_port1 = [parser.OFPActionOutput(1)]
        action_output_port2 = [parser.OFPActionOutput(2)]

        buckets = [
            parser.OFPBucket(self.LB_WEIGHT_1, watch_port, watch_group, actions=action_output_port1),
            parser.OFPBucket(self.LB_WEIGHT_2, watch_port, watch_group, actions=action_output_port2)
        ]
        req = parser.OFPGroupMod(datapath, ofproto.OFPGC_ADD, ofproto.OFPGT_SELECT, 50, buckets)
        datapath.send_msg(req)

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
                instructions=inst
            )

        datapath.send_msg(mod)
