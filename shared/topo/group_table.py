from mininet.topo import Topo


class GroupTableTopo(Topo):
    def build(self):
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        sniffer = self.addHost('sniffer')

        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')

        self.addLink(h1, s2)
        self.addLink(s2, s1)
        self.addLink(h2, s3)
        self.addLink(s3, s1)
        self.addLink(s1, sniffer)


topos = {'group_table_topo': (lambda: GroupTableTopo())}
