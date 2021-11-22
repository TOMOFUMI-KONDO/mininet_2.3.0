from mininet.link import TCLink
from mininet.log import setLogLevel, info
from mininet.net import Mininet
from mininet.node import Controller, OVSKernelSwitch


def build():
    net = Mininet()

    info("*** Adding controller ***\n")
    c0 = net.addController(name="c0", protocol="tcp", ip="192.168.56.1", port=6633)
    info("done\n")

    info("*** Adding switch ***\n")
    s1 = net.addSwitch("s1", cls=OVSKernelSwitch)
    info("done\n")

    info("*** Adding host ***\n")
    h1 = net.addHost("h1", ip="10.0.0.1/24")
    h2 = net.addHost("h2", ip="10.0.0.2/24")
    info("done\n")

    info("*** Adding link ***\n")
    link = {"cls": TCLink, "bw": 100}
    net.addLink(h1, s1, **link)
    net.addLink(h2, s1, **link)
    info("\ndone\n")

    net.start()

    info("*** ping h1-h2 ***\n")
    net.ping([h1, h2])

    net.stop()


if __name__ == "__main__":
    setLogLevel("info")
    build()
