import datetime
import json
import os

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import set_ev_cls, MAIN_DISPATCHER
from ryu.lib.packet.packet import Packet
from ryu.ofproto import ofproto_v1_0


class L2Switch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(L2Switch, self).__init__(*args, **kwargs)

        if os.environ.get('DEBUG') == '1':
            self.debug = True
        else:
            self.debug = False

        self.datetime = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self.key = 0

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        print('PACKET_IN')

        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser

        actions = [ofp_parser.OFPActionOutput(ofp.OFPP_FLOOD)]

        data = None
        if msg.buffer_id == ofp.OFP_NO_BUFFER:
            data = msg.data
            self.__dump_packet(data)

        out = ofp_parser.OFPPacketOut(
            datapath=dp,
            buffer_id=msg.buffer_id,
            in_port=msg.in_port,
            actions=actions,
            data=data
        )
        dp.send_msg(out)

    def __dump_packet(self, data):
        packet = Packet(data)
        pretty_json = json.dumps(packet.to_jsondict(), indent=4, sort_keys=True)

        if self.debug:
            print(pretty_json)

        dump_dir = f"dump/{self.datetime}"
        os.makedirs(dump_dir, exist_ok=True)
        with open(f"{dump_dir}/{self.key}.dmp", "w") as f:
            f.write(pretty_json)

        self.key += 1
