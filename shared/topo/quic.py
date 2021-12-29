import time

from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.topo import Topo


class Quic(Topo):
    def build(self):
        s1 = self.addSwitch("s1")
        h1 = self.addHost("h1", ip="10.0.0.1/24")
        h2 = self.addHost("h2", ip="10.0.0.2/24")

        self.addLink(h1, s1)
        self.addLink(h2, s1)


if __name__ == "__main__":
    setLogLevel("info")

    net = Mininet(
        topo=Quic(),
        controller=RemoteController("c0", port=6633)
    )

    net.start()

    hosts = net.hosts
    h0 = hosts[0]
    h1 = hosts[1]

    h0.cmd("./bin/server &")
    print(h1.cmd(f"./bin/client -addr {h0.IP()}:44300"))

    net.stop()
