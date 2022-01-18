from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import RemoteController


def build():
    net = Mininet()

    net.addController(name="c0", controller=RemoteController, port=6633)

    s1 = net.addSwitch("S1")
    h1 = net.addHost("h1", ip="10.0.0.1/24")
    h2 = net.addHost("h2", ip="10.0.0.2/24")

    net.addLink(h1, s1)
    net.addLink(h2, s1)

    net.start()
    net.pingAll()
    net.stop()


if __name__ == "__main__":
    setLogLevel("info")
    build()
