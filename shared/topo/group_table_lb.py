from mininet.topo import Topo
from mininet.log import setLogLevel
from mininet.node import RemoteController
from mininet.net import Mininet
from mininet.cli import CLI


class GroupTableLbTopo(Topo):
    def build(self):
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')

        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')

        self.addLink(s1, h1, 3, 1)
        self.addLink(s1, s2, 1, 1)
        self.addLink(s1, s3, 2, 1)
        self.addLink(s4, h2, 3, 1)
        self.addLink(s4, s2, 1, 2)
        self.addLink(s4, s3, 2, 2)


if __name__ == "__main__":
    setLogLevel("info")

    net = Mininet(
        topo=GroupTableLbTopo(),
        controller=RemoteController("c1", ip="127.0.0.1")
    )
   
    net.start()
    CLI(net)
    net.stop()
