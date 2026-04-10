from pox.core import core
import pox.openflow.libopenflow_01 as of

log = core.getLogger()

# BLOCK RULE (edit this as needed)
BLOCK_SRC = "10.0.0.1"
BLOCK_DST = "10.0.0.3"


class StaticRouting(object):

    def __init__(self, connection):
        self.connection = connection
        connection.addListeners(self)
        log.info("Static Routing Switch %s connected", connection.dpid)

    def _handle_PacketIn(self, event):

        packet = event.parsed
        ip = packet.find('ipv4')

        msg = of.ofp_packet_out()
        msg.data = event.ofp
        msg.actions = []

        in_port = event.port

        # If no IP packet → flood
        if not ip:
            msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
            self.connection.send(msg)
            return

        src = str(ip.srcip)
        dst = str(ip.dstip)

        log.info("Packet: %s -> %s", src, dst)

        # 🚫 BLOCK RULE
        if src == BLOCK_SRC and dst == BLOCK_DST:
            log.info("BLOCKED TRAFFIC %s -> %s", src, dst)
            return  # drop packet

        # ✅ STATIC ROUTING RULES
        out_port = None

        if src == "10.0.0.1" and dst == "10.0.0.2":
            out_port = 2
        elif src == "10.0.0.2" and dst == "10.0.0.1":
            out_port = 1
        elif src == "10.0.0.1" and dst == "10.0.0.3":
            out_port = 3
        elif src == "10.0.0.3" and dst == "10.0.0.1":
            out_port = 1
        else:
            out_port = of.OFPP_FLOOD

        # send packet
        msg.actions.append(of.ofp_action_output(port=out_port))
        self.connection.send(msg)


def launch():
    def start_switch(event):
        StaticRouting(event.connection)

    core.openflow.addListenerByName("ConnectionUp", start_switch)
    log.info("Static Routing Controller Running")