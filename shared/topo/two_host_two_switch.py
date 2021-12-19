from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.topo import Topo


class TwoHostTwoSwitchTopo(Topo):

    def build(self):
        s1 = self.addSwitch("s1")
        s2 = self.addSwitch("s2")

        h1 = self.addHost("h1", ip="10.0.0.1/24")
        h2 = self.addHost("h2", ip="10.0.0.2/24")

        self.addLink(h1, s1)
        self.addLink(h1, s2)
        self.addLink(h2, s1)
        self.addLink(h2, s2)


if __name__ == "__main__":
    setLogLevel("info")

    net = Mininet(
        topo=TwoHostTwoSwitchTopo(),
        controller=RemoteController("c1", ip="127.0.0.1")
    )

    net.start()
    CLI(net)
