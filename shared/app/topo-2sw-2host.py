"""Custom topology example

Two directly connected switches plus a host for each switch:

   host --- switch --- switch --- host

Adding the 'topos' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=mytopo' from the command line.
"""

from mininet.topo import Topo


class MyTopo(Topo):
    """Simple topology example."""

    def build(self):
        """Create custom topo."""

        # Add hosts and switches
        left_host = self.addHost('h1')
        right_host = self.addHost('h2')
        left_switch = self.addSwitch('s3')
        right_switch = self.addSwitch('s4')

        # Add links
        self.addLink(left_host, left_switch)
        self.addLink(left_switch, right_switch)
        self.addLink(right_switch, right_host)


topos = {'mytopo': (lambda: MyTopo())}
