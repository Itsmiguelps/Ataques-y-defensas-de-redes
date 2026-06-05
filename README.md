<div align="center">

```
█████╗ ████████╗█████╗  ██████╗ ██╗   ██╗███████╗███████╗    ██╗   ██╗
██╔══██╗╚══██╔══╝██╔══██╗██╔═══██╗██║   ██║██╔════╝██╔════╝    ╚██╗ ██╔╝
███████║   ██║   ███████║██║   ██║██║   ██║█████╗  ███████╗     ╚████╔╝ 
██╔══██║   ██║   ██╔══██║██║   ██║██║   ██║██╔══╝  ╚════██║      ╚██╔╝  
██║  ██║   ██║   ██║  ██║╚██████╔╝╚██████╔╝███████╗███████║       ██║   
╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚══════╝╚══════╝       ╚═╝   

 ██████╗  ██████╗ ███╗   ██╗████████╗██████╗  █████╗ ███╗   ███╗███████╗██████╗ ██╗██████╗  █████╗ ███████╗
██╔════╝ ██╔═══██╗████╗  ██║╚══██╔══╝██╔══██╗██╔══██╗████╗ ████║██╔════╝██╔══██╗██║██╔══██╗██╔══██╗██╔════╝
██║      ██║   ██║██╔██╗ ██║   ██║   ██████╔╝███████║██╔████╔██║█████╗  ██║  ██║██║██║  ██║███████║███████╗
██║      ██║   ██║██║╚██╗██║   ██║   ██╔══██╗██╔══██║██║╚██╔╝██║██╔══╝  ██║  ██║██║██║  ██║██╔══██║╚════██║
╚██████╗ ╚██████╔╝██║ ╚████║   ██║   ██║  ██║██║  ██║██║ ╚═╝ ██║███████╗██████╔╝██║██████╔╝██║  ██║███████║
 ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚═════╝ ╚═╝╚═════╝ ╚═╝  ╚═╝╚══════╝
```
# Ataques-y-defensas-de-redes
Repositorio académico que contiene prácticas de seguridad en redes, incluyendo ARP Spoofing, DHCP Spoofing, DHCP Starvation, MAC Flooding, STP Root Attack y sus respectivas contramedidas en entornos controlados.

![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Scapy](https://img.shields.io/badge/Scapy-Latest-009688?style=for-the-badge&logo=python&logoColor=white)
![Kali](https://img.shields.io/badge/Kali_Linux-Docker-557C94?style=for-the-badge&logo=kalilinux&logoColor=white)
![Cisco](https://img.shields.io/badge/Cisco_IOSvL2-PNetLab-1BA0D7?style=for-the-badge&logo=cisco&logoColor=white)
![Status](https://img.shields.io/badge/Status-Educativo-orange?style=for-the-badge)

<br>

> **Asignatura:** Seguridad en Redes &nbsp;|&nbsp; **Entorno:** PNetLab + Kali Linux Docker + Cisco IOSvL2

</div>

---

## ⚠️ Disclaimer

> **Este laboratorio es de uso exclusivamente educativo** en entornos controlados y con autorización expresa.
> La ejecución de estas técnicas en redes de producción sin autorización constituye un delito tipificado por la ley.
> Todos los scripts están diseñados para entornos de laboratorio aislados.

---

## 🎯 Objetivo General

Este repositorio documenta seis ataques sobre protocolos de **Capa 2 del modelo OSI**, ejecutados con scripts Python usando la librería **Scapy** en un entorno virtualizado con **PNetLab**, **Kali Linux Docker** y **switches Cisco IOSvL2**.

Cada ataque está organizado en su propio repositorio independiente, con documentación técnica completa, capturas de pantalla, scripts comentados y video de demostración.

### Objetivos Específicos

- Comprender cómo los protocolos de Capa 2 (CDP, ARP, DHCP, STP, Ethernet) son explotables por carecer de autenticación nativa
- Implementar y ejecutar los seis ataques en el entorno de laboratorio
- Verificar el impacto en dispositivos Cisco reales (IOSvL2)
- Aplicar y validar contramedidas de mitigación en Cisco IOS
- Documentar evidencia técnica de cada ataque y su solución

---

## 🗂️ Repositorios de Ataques

| # | Ataque | Protocolo | Capa | Impacto | Repositorio |
|:-:|--------|:---------:|:----:|---------|:-----------:|
| 01 | 🔴 **CDP DoS** | CDP | L2 Cisco | Alta CPU · tabla CDP agotada | [📁 Ver repo](#) |
| 02 | 🟠 **ARP MitM** | ARP (RFC 826) | L2/L3 | Intercepción total del tráfico | [📁 Ver repo](#) |
| 03 | 🟡 **DHCP Spoofing** | DHCP (RFC 2131) | L2/L3 | MitM automático + DNS malicioso | [📁 Ver repo](#) |
| 04 | 🟠 **DHCP Starvation** | DHCP (RFC 2131) | L2/L3 | DoS: clientes sin dirección IP | [📁 Ver repo](#) |
| 05 | 🔵 **MAC Flooding** | Ethernet 802.3 | L2 | Switch en modo hub · sniffing total | [📁 Ver repo](#) |
| 06 | 🟣 **STP Root Claim** | STP 802.1D / PVST+ | L2 | Control de topología · DoS 30–50 s | [📁 Ver repo](#) |

---

## 🌐 Topología del Laboratorio

### Vista General en PNetLab

```
                         ┌─────────────────────────────────────────┐
                         │            PNetLab — Lab Capa 2          │
                         └─────────────────────────────────────────┘

  7.41.10.1                                            Kali Linux Docker
  ┌──────────┐          trunk VLAN10,20       ┌──────────────────────────┐
  │ Router   │───────────────────────────────│         SW1               │
  │   R1     │  e0/0                         │     (Core / VTP Server)   │
  │ DHCP GW  │                               │      STP Root Bridge      │
  └──────────┘                               │      Priority: 4096       │
                                              └─────────┬──────┬────────┘
                                              e1/0 trunk│      │e0/3 trunk
                                              VLAN 10   │      │ VLAN 10
                                         ┌──────────────┘      └──────────────┐
                                         │                                     │
                                    ┌────┴─────┐                         ┌─────┴────┐
                                    │   SW2    │─────────────────────────│   SW3    │
                                    │VTP Client│  trunk VLAN 10          │VTP Client│
                                    │Pri: 4096 │                         │Pri: 4096 │
                                    └────┬─────┘                         └──────────┘
                                    e1/1 │ trunk VLAN 10,20
                               ┌─────────┴──────────────────┐
                               │                            │
                          ┌────┴───────┐             ┌──────┴──────┐
                          │Kali Linux  │             │ PC-Víctimas │
                          │  Docker    │             │  eth1       │
                          │  eth2=atk  │             │.10 / .20    │
                          │ 10.50/24   │             │ / .100/24   │
                          └────────────┘             └─────────────┘
```

### Tabla de Direccionamiento General

| Nodo | Interfaz | Dirección IP | Rol |
|------|:--------:|:------------:|-----|
| Router R1 | e0/0 | `7.41.10.1/24` | Gateway + Servidor DHCP |
| Kali Linux | eth1 | DHCP dinámico | Internet (descarga de paquetes) |
| Kali Linux | eth2 | `7.41.10.50/24` o `7.41.1.50/24` | Interfaz de ataque |
| PC-Víctima 1 | eth1 | `7.41.1.10/24` | Objetivo (ARP MitM) |
| PC-Víctima 2 | eth1 | `7.41.1.20/24` | Objetivo (ARP MitM) |
| PC-Víctima | eth1 | `7.41.10.100/24` | Objetivo (DHCP / MAC / STP) |
| SW1 | — | — | VTP Server · STP Root · Priority 4096 |
| SW2, SW3 | — | — | VTP Client · Priority 4096 |

### VLANs Configuradas

| VLAN ID | Nombre | Uso en el Laboratorio |
|:-------:|--------|----------------------|
| **10** | ADMIN | Red de administración, ataques STP, CDP, DHCP, MAC |
| **20** | USERS | Red de usuarios (ARP MitM) |

---

## 🔬 Descripción de Cada Ataque

### 🔴 01 · CDP DoS — Denegación de Servicio vía Cisco Discovery Protocol

**Protocolo objetivo:** CDP (Cisco Discovery Protocol)

Inunda la tabla de vecinos CDP de un switch Cisco con cientos de entradas falsas construidas con Scapy. Cada paquete lleva TLVs aleatorios (`DeviceID: ROUTER-XXXXXX`) y se envía a la dirección multicast CDP `01:00:0C:CC:CC:CC`, causando agotamiento de CPU y memoria.

```bash
sudo python3 01_cdp_dos.py -i eth2 -c 1000 -d 0.001
```

| Parámetro | Descripción | Default |
|-----------|-------------|:-------:|
| `-i` | Interfaz de salida | — |
| `-c` | Número de paquetes | `500` |
| `-d` | Delay entre paquetes (s) | `0.005` |
| `-v` | Verbose | off |

**Contramedida:** `no cdp run` global · `no cdp enable` por interfaz

---

### 🟠 02 · ARP MitM — Man-in-the-Middle por Envenenamiento ARP

**Protocolo objetivo:** ARP (RFC 826)

Envía ARP Replies no solicitados (Gratuitous ARP) a dos víctimas cada segundo: le dice a cada una que la IP de la otra tiene la MAC de Kali. Con IP forwarding activo, Kali reenvía el tráfico de forma transparente. Al detener el ataque (Ctrl+C), restaura las tablas ARP originales.

```bash
sudo python3 02_arp_mitm.py -t1 7.41.1.10 -t2 7.41.1.20 -i eth2
```

| Parámetro | Descripción |
|-----------|-------------|
| `-t1` | IP de la Víctima 1 |
| `-t2` | IP de la Víctima 2 |
| `-i` | Interfaz de ataque |

**Contramedida:** `ip arp inspection vlan 1` (DAI) · `port-security maximum 1`

---

### 🟡 03 · DHCP Spoofing — Servidor DHCP Falso (Rogue DHCP)

**Protocolo objetivo:** DHCP (RFC 2131)

Implementa un servidor DHCP fraudulento que responde al handshake DORA completo antes que el servidor legítimo. Asigna como gateway la IP de Kali y un DNS controlado por el atacante, logrando MitM automático sobre todos los clientes que renueven su IP.

```bash
sudo python3 03_dhcp_spoofing.py -i eth2 \
  --pool 7.41.10.200-220 \
  --gateway 7.41.10.50 \
  --dns 8.8.8.8
```

| Parámetro | Descripción | Default |
|-----------|-------------|:-------:|
| `--pool` | Rango de IPs falsas | — |
| `--gateway` | Gateway anunciado (Kali) | — |
| `--dns` | DNS anunciado | — |
| `--lease` | Lease time (s) | `600` |

**Contramedida:** `ip dhcp snooping` · `ip dhcp snooping trust` en uplink

---

### 🟠 04 · DHCP Starvation — Agotamiento del Pool DHCP

**Protocolo objetivo:** DHCP (RFC 2131)

Genera MACs aleatorias con OUIs de fabricantes reales (VMware, VirtualBox, QEMU) y envía DHCP Discovers masivos. En modo `--confirm`, completa el handshake DORA con cada MAC falsa, bloqueando definitivamente todas las IPs del pool hasta que expire el lease.

```bash
sudo python3 04_dhcp_starvation.py -i eth2 -c 500 --confirm --delay 0.1
```

| Parámetro | Descripción | Default |
|-----------|-------------|:-------:|
| `-c` | Número de solicitudes | `254` |
| `--confirm` | Completar handshake DORA | off |
| `--delay` | Delay entre requests (s) | `0.05` |
| `--timeout` | Timeout por Offer (s) | `2` |

**Contramedida:** `switchport port-security maximum 2` · `violation shutdown`

---

### 🔵 05 · MAC Flooding — Desbordamiento de la Tabla CAM

**Protocolo objetivo:** Ethernet 802.3

Genera tramas Ethernet con MACs de origen y destino completamente aleatorias en lotes de 100, usando múltiples hilos paralelos. La tabla CAM del switch (~8192 entradas) se satura rápidamente: el switch no puede aprender MACs legítimas y pasa a hacer flooding unicast a todos los puertos.

```bash
sudo python3 05_mac_flooding.py -i eth2 --continuous --threads 4
sudo python3 05_mac_flooding.py -i eth2 -c 50000 --vlan 10
```

| Parámetro | Descripción | Default |
|-----------|-------------|:-------:|
| `-c` | Tramas a enviar | `50000` |
| `--continuous` | Modo continuo | off |
| `--threads` | Hilos paralelos (máx. 4) | `1` |
| `--vlan` | Tag 802.1Q opcional | — |

**Contramedida:** `port-security maximum 2` · `mac-address sticky` · `violation shutdown`

---

### 🟣 06 · STP Root Claim — Usurpación del Root Bridge

**Protocolo objetivo:** STP 802.1D / PVST+ Cisco

Envía BPDUs de configuración STP/PVST+ con `Bridge Priority = 0` y `Root Path Cost = 0` cada 2 segundos a la dirección multicast `01:80:C2:00:00:00`. Los switches, al recibir una prioridad menor a la propia (4096 > 0), inician la reelección del Root Bridge, reconvergiendo con Kali como nuevo Root y causando un DoS de 30–50 segundos.

```bash
sudo python3 06_stp_root_claim.py -i eth2 --priority 0 --hello 1 --vlan 10
```

| Parámetro | Descripción | Default |
|-----------|-------------|:-------:|
| `--priority` | Bridge Priority anunciada | `0` |
| `--hello` | Intervalo entre BPDUs (s) | `2` |
| `--vlan` | VLAN para PVST+ Cisco | — |
| `--duration` | Duración (0 = continuo) | `0` |

**Contramedida:** `spanning-tree bpduguard enable` · `spanning-tree guard root`

---

## 📊 Resumen de Ataques y Contramedidas

| Ataque | Protocolo | Impacto Principal | Contramedida Cisco IOS |
|--------|:---------:|-------------------|------------------------|
| 🔴 CDP DoS | CDP | Alta CPU · vecinos falsos | `no cdp run` / `no cdp enable` |
| 🟠 ARP MitM | ARP | Intercepción de tráfico | `ip arp inspection vlan` + DAI |
| 🟡 DHCP Spoofing | DHCP | MitM + DNS malicioso | `ip dhcp snooping` + trust en uplink |
| 🟠 DHCP Starvation | DHCP | DoS: sin IPs disponibles | `port-security maximum 2` |
| 🔵 MAC Flooding | Ethernet | Switch en modo hub | `port-security` + `mac sticky` |
| 🟣 STP Root Claim | STP/PVST+ | DoS 30–50 s · control topología | `bpduguard` + `guard root` |

---


## 🛠️ Configuración General de Kali Linux Docker

```bash
# ── Instalación de dependencias (ejecutar una sola vez) ──
apt update && apt install python3-scapy -y
apt update && apt install openssh-server -y
service ssh start

# ── Configuración de interfaz de ataque (eth2) ──
ip addr flush dev eth2
ip addr add 7.41.10.50/24 dev eth2      # Red DHCP/MAC/STP
# ip addr add 7.41.1.50/24 dev eth2     # Red ARP MitM
ip link set eth2 up

# ── Configuración de internet (eth1) ──
ip link set eth1 up
dhclient eth1

# ── IP Forwarding (obligatorio para ARP MitM y DHCP Spoofing) ──
echo 1 > /proc/sys/net/ipv4/ip_forward
sudo sysctl -w net.ipv4.ip_forward=1

# ── Gateway (necesario para DHCP Spoofing) ──
ip route add default via 7.41.10.1
```

---

## 📦 Requisitos Generales

```
Plataforma de virtualización  →  PNetLab
Máquina atacante              →  Kali Linux Docker
Switches                      →  Cisco IOSvL2
Router                        →  Cisco IOS (R1)
Lenguaje                      →  Python 3
Librería de red               →  python3-scapy
Privilegios requeridos        →  root (sudo obligatorio en todos los scripts)
```

---

---
 
## 📊 Resumen de Ataques y Contra-medidas
 
| Ataque | Protocolo | Capa OSI | Impacto | Contra-medida principal |
|---|---|---|---|---|
| **CDP DoS** | CDP (Cisco) | L2 | Agota tabla CDP, CPU/RAM alta | `no cdp run` · `no cdp enable` |
| **ARP MitM** | ARP RFC 826 | L2 | Intercepta todo el tráfico | `ip arp inspection vlan` + `port-security max 1` |
| **DHCP Spoofing** | DHCP RFC 2131 | L2/L3 | MitM automático + DNS malicioso | `ip dhcp snooping` + `trust` en uplink |
| **DHCP Starvation** | DHCP RFC 2131 | L2/L3 | DoS: pool agotado, clientes sin IP | `port-security max 2` + `violation shutdown` |
| **MAC Flooding** | Ethernet 802.3 | L2 | Switch en modo hub → sniffing total | `port-security` + `mac-address sticky` |
| **STP Root Claim** | STP 802.1D/PVST+ | L2 | Control de topología L2, DoS 30–50 s | `bpduguard enable` + `spanning-tree guard root` |
 
---

## 📁 Estructura de Cada Repositorio

```text
Network-Attacks-and-Defenses/
│
├── README.md
│
├── docs/
│   └── Documentacion tecnica.pdf
│
├── scripts/
│   ├── cdp_dos/
│   │   ├── cdp_dos.py
│   │   └── README.md
│   │
│   ├── arp_spoofing/
│   │   ├── arp_spoofing.py
│   │   └── README.md
│   │
│   ├── dhcp_spoofing/
│   │   ├── dhcp_spoofing.py
│   │   └── README.md
│   │
│   ├── dhcp_starvation/
│   │   ├── dhcp_starvation.py
│   │   └── README.md
│   │
│   ├── mac_flooding/
│   │   ├── mac_flooding.py
│   │   └── README.md
│   │
│   └── stp_root_attack/
│       ├── stp_root_attack.py
│       └── README.md
└── 
```
---
 
## 🎥 D Video
 
📹 El proceso completo del laboratorio fue grabado y documentado:
 
> **[Ver Videos →](https://www.youtube.com/playlist?list=PL7fyKcoaUM3-yGXB4a5rSAdiru8yLqHr9)**
 
---
---
 
## 🛠️ Stack Tecnológico
 
| Componente | Tecnología |
|---|---|
| Hipervisor | PNetLab (compatible con EVE-NG) |
| Atacante | Kali Linux Docker |
| Switches | Cisco IOSvL2 |
| Router | Cisco IOS |
| Lenguaje | Python 3 |
| Librería de red | Scapy (`python3-scapy`) |
| Protocolo VTP | Dominio: `EMPRESA` · Modo: Server / Client |
| Protocolo STP | PVST+ (Per-VLAN Spanning Tree Protocol) |
 
---
---

## 📄 Licencia y Uso

Este material es de uso **exclusivamente académico**. No se autoriza su uso en entornos de producción o redes sin autorización expresa. Todo el contenido fue desarrollado en un entorno de laboratorio aislado con fines educativos dentro de la asignatura de Seguridad en Redes.

---

<div align="center">

**Seguridad en Redes · Laboratorio de Ataques Capa 2**

*PNetLab · Kali Linux Docker · Cisco IOSvL2 · Python 3 · Scapy*

*Proyecto académico — ITLA 2025 | Seguridad Informática*

</div>
