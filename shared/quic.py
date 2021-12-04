import time

from mininet.link import TCLink
from mininet.log import setLogLevel, info
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch


def build():
    net = Mininet()

    info("adding controller...\n")
    net.addController(name="c0", controller=RemoteController, ip="127.0.0.1", port=6633, protocol="tcp")

    info("adding switch...\n")
    s1 = net.addSwitch("s1", cls=OVSKernelSwitch)

    info("adding host...\n")
    h1 = net.addHost("h1", ip="10.0.0.1/24")
    h2 = net.addHost("h2", ip="10.0.0.2/24")

    info("adding link...\n")
    link = {"cls": TCLink, "bw": 100}
    net.addLink(h1, s1, **link)
    net.addLink(h2, s1, **link)
    info("\n")

    net.start()

    net.pingAll()

    info("*** Starting QUIC server. Please wait... ***\n")
    h1.cmd("./bin/server -addr 0.0.0.0:4430 &")
    time.sleep(3)
    info("*** Started! ***\n")

    info("*** Send QUIC packet ***\n")
    out = h2.cmd("./bin/client -addr 10.0.0.1:4430")
    print(out)

    net.stop()


if __name__ == "__main__":
    setLogLevel("info")
    build()
