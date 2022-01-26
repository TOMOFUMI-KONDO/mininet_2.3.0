from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.topo import Topo

"""
Topology is like below.

         --- s2 ---
        |          |
h1 --- s1          s4 --- h2
        |          |
         --- s3 ---
"""


class PathSwitchTopo(Topo):
    def build(self):
        s1 = self.addSwitch("s1", dpid="1")
        s2 = self.addSwitch("s2", dpid="2")
        s3 = self.addSwitch("s3", dpid="3")
        s4 = self.addSwitch("s4", dpid="4")

        h1 = self.addHost("h1", ip="10.0.0.1/24", mac="00:00:00:00:00:01")
        h2 = self.addHost("h2", ip="10.0.0.2/24", mac="00:00:00:00:00:02")

        self.addLink(s1, h1)
        self.addLink(s1, s2)
        self.addLink(s1, s3)
        self.addLink(s4, h2)
        self.addLink(s4, s2)
        self.addLink(s4, s3)


topos = {"path_switch_topo": lambda: PathSwitchTopo()}

if __name__ == "__main__":
    setLogLevel("info")

    net = Mininet(
        topo=PathSwitchTopo(),
        controller=RemoteController("c1", ip="127.0.0.1")
    )
    net.start()
    CLI(net)
    net.stop()
