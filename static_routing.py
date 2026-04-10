from pox.core import core
import pox.openflow.libopenflow_01 as of

log = core.getLogger()

H1 = "10.0.0.1"
H2 = "10.0.0.2"
H3 = "10.0.0.3"

class StaticRouting(object):
    def __init__(self, connection):
        self.connection = connection
        connection.addListeners(self)
        log.info("Switch connected")

    def install_forward_rule(self, src_ip, dst_ip):
        msg = of.ofp_flow_mod()
        msg.priority = 100
        msg.match.dl_type = 0x0800   # IPv4
        msg.match.nw_src = src_ip
        msg.match.nw_dst = dst_ip
        msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
        self.connection.send(msg)
        log.info("FLOW INSTALLED: %s -> %s ALLOW", src_ip, dst_ip)

    def install_drop_rule(self, src_ip, dst_ip):
        msg = of.ofp_flow_mod()
        msg.priority = 200
        msg.match.dl_type = 0x0800   # IPv4
        msg.match.nw_src = src_ip
        msg.match.nw_dst = dst_ip
        # no actions = drop
        self.connection.send(msg)
        log.info("FLOW INSTALLED: %s -> %s DROP", src_ip, dst_ip)

    def _handle_PacketIn(self, event):
        packet = event.parsed
        ip = packet.find('ipv4')

        # Allow ARP and non-IP by flooding
        if ip is None:
            msg = of.ofp_packet_out()
            msg.data = event.ofp
            msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
            self.connection.send(msg)
            return

        src = str(ip.srcip)
        dst = str(ip.dstip)

        log.info("PACKET IN: %s -> %s", src, dst)

        # Allow h1 <-> h2 and install flow
        if src == H1 and dst == H2:
            self.install_forward_rule(H1, H2)

            msg = of.ofp_packet_out()
            msg.data = event.ofp
            msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
            self.connection.send(msg)
            return

        if src == H2 and dst == H1:
            self.install_forward_rule(H2, H1)

            msg = of.ofp_packet_out()
            msg.data = event.ofp
            msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
            self.connection.send(msg)
            return

        # Block traffic involving h3 and install drop rule
        if src == H1 and dst == H3:
            self.install_drop_rule(H1, H3)
            log.info("BLOCKED TRAFFIC %s -> %s", src, dst)
            return

        if src == H3 and dst == H1:
            self.install_drop_rule(H3, H1)
            log.info("BLOCKED TRAFFIC %s -> %s", src, dst)
            return

        if src == H2 and dst == H3:
            self.install_drop_rule(H2, H3)
            log.info("BLOCKED TRAFFIC %s -> %s", src, dst)
            return

        if src == H3 and dst == H2:
            self.install_drop_rule(H3, H2)
            log.info("BLOCKED TRAFFIC %s -> %s", src, dst)
            return

def launch():
    def start_switch(event):
        StaticRouting(event.connection)

    core.openflow.addListenerByName("ConnectionUp", start_switch)
    log.info("Static Routing Controller Running")
