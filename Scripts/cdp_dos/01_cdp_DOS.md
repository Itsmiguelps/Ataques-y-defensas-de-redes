# 🔐 Ataque 01 — CDP DoS (Denegación de Servicio vía Cisco Discovery Protocol)

> **⚠️ AVISO LEGAL:** Este repositorio es de uso **exclusivamente educativo** en entornos de laboratorio controlados y con autorización expresa. La ejecución de estas técnicas en redes de producción sin autorización constituye un delito.

---

## 📋 Información General

| Campo | Detalle |
|-------|---------|
| **Asignatura** | Seguridad en Redes |
| **Entorno** | PNetLab + Kali Linux Docker + Cisco IOSvL2 |
| **Script** | `cdp_dos.py` |
| **Protocolo atacado** | CDP — Cisco Discovery Protocol (Capa 2) |
| **Herramienta** | Python 3 + Scapy |
| **Impacto** | Agota la tabla de vecinos CDP + alto uso de CPU |

---

## 🎯 Objetivo del Laboratorio

Demostrar, en un entorno controlado con **PNetLab** y **Kali Linux Docker**, cómo los protocolos de Capa 2 del modelo OSI pueden ser explotados por carecer de mecanismos de autenticación nativos. El laboratorio documenta el ataque, su impacto, el proceso de ejecución y la contra-medida correspondiente para mitigarlo.

---

## 🎯 Objetivo del Script

Inundar la tabla de vecinos CDP de un switch Cisco con cientos de entradas falsas mediante paquetes CDP construidos con Scapy, causando **agotamiento de CPU y memoria** del dispositivo objetivo.

### ¿Cómo funciona?

El script `cdp_dos.py` construye paquetes CDP válidos estructuralmente usando las capas:

```
Ethernet → LLC (DSAP/SSAP=0xAA) → SNAP (OUI=0x00000C, code=0x2000) → CDP Header → TLVs
```

Cada paquete contiene TLVs aleatorios:
- **DeviceID**: `ROUTER-XXXXXX` (nombre aleatorio)
- **SoftwareVersion**, **Platform**, **PortID**: valores aleatorios

Los paquetes se envían a la dirección multicast CDP `01:00:0C:CC:CC:CC`. El switch intenta aprender cada vecino nuevo, agotando su tabla CDP.

---

## ⚙️ Parámetros del Script

| Parámetro | Descripción | Ejemplo |
|-----------|-------------|---------|
| `-i` / `--interface` | Interfaz de red de salida | `eth2` |
| `-c` / `--count` | Número de paquetes CDP a enviar | `500` (default) |
| `-d` / `--delay` | Retardo en segundos entre paquetes | `0.005` (default) |
| `-v` / `--verbose` | Mostrar detalle de cada paquete enviado | (flag) |

---

## 📦 Requisitos

```bash
# Sistema operativo
Kali Linux (Docker en PNetLab) o cualquier distribución Linux

# Dependencias
apt update && apt install python3-scapy -y

# Privilegios
sudo / root (requerido para envío de paquetes raw)

# Condiciones de red
- CDP habilitado en el switch objetivo
- Kali en el mismo dominio L2 que el switch
```

---

## 🗺️ Topología de Red

```
┌─────────────────────────────────────────────────────────┐
│                    PNetLab Topologia                    │
│                                                         │
│   ┌──────────┐  Trunk VLAN10,20   ┌──────────┐          │
│   │   SW1    ├────────────────────┤   SW2    │          │
│   │ (Core)   │ e0/0 ←──→ e1/0     │ (Client) │          │
│   └──────────┘                    └────┬─────┘          │
│                                        │ e1/1           │
│                                        │                │
│                                        │                │
│                              ┌─────────┴──────────┐     │
│                              │   Kali (eth2)       │    │
│                              │   7.41.1.50/24      │    │
│                              │     [Atacante]      │    │
│                              └────────────────────-┘    │
└─────────────────────────────────────────────────────────┘
```

### Tabla de Interfaces y Direccionamiento

| Interfaz / Nodo | Rol y Dirección IP |
|-----------------|-------------------|
| **SW1 — e0/0** | Trunk VLAN 10, 20 hacia SW2 |
| **SW2 — e1/0** | Trunk VLAN 10, 20 (hacia SW1) |
| **SW2 — e1/1** | Trunk VLAN 10, 20 (hacia Kali / víctimas) |
| **Kali — eth2** | `7.41.1.50/24` — Atacante |
| **PC-Víctima 1 — eth1** | `7.41.1.10/24` |
| **PC-Víctima 2 — eth1** | `7.41.1.20/24` |
| **VLANs** | VLAN 10 = ADMIN · VLAN 20 = USERS |

---

## 🔧 Configuración del Entorno

### Switch SW1 y SW2 — Cisco IOS

```cisco
! ── SW1 ── Configuración completa
conf t
 vtp domain EMPRESA
 vtp mode server
 vtp password cisco
 vlan 10
  name ADMIN
 vlan 20
  name USERS
 interface e0/0
  switchport trunk encapsulation dot1q
  switchport mode trunk
  switchport trunk allowed vlan 10,20
 exit
! CDP está habilitado por defecto — verificar:
end
SW1# show cdp

! ── SW2 ── Configuración completa
conf t
 vtp domain EMPRESA
 vtp mode client
 vtp password cisco
 interface e1/0
  switchport trunk encapsulation dot1q
  switchport mode trunk
  switchport trunk allowed vlan 10,20
 exit
 interface e1/1
  switchport trunk encapsulation dot1q
  switchport mode trunk
  switchport trunk allowed vlan 10,20
 exit
```

### Kali Linux — Configuración de Red

```bash
# Configurar interfaz de ataque
ip addr add 7.41.1.50/24 dev eth2
ip link set eth2 up

# Instalar dependencias
apt update && apt install python3-scapy -y
```

---

## ▶️ Ejecución del Ataque

```bash
# Ejecución básica (1000 paquetes, delay 1ms)
sudo python3 01_cdp_dos.py -i eth2 -c 1000 -d 0.001

# Ejecución con modo verbose para ver cada paquete
sudo python3 01_cdp_dos.py -i eth2 -c 500 -d 0.005 -v
```

---

## ✅ Verificación del Ataque

```cisco
! En el switch Cisco (durante el ataque):
SW1# show cdp neighbors
! Resultado esperado: decenas/cientos de entradas ROUTER-XXXX

SW1# show processes cpu sorted
! Resultado esperado: proceso CDP con alto uso de CPU
```

---

## 🛡️ Contra-medida

Deshabilitar CDP globalmente o por interfaz (recomendado en puertos de acceso hacia usuarios).

```cisco
! Deshabilitar CDP globalmente
SW1(config)# no cdp run

! Deshabilitar CDP solo en el puerto hacia el atacante (recomendado)
SW1(config)# interface e0/0
SW1(config-if)# no cdp enable
```

### Verificación de la Contra-medida

| Comando | Resultado esperado |
|---------|-------------------|
| `SW1# show cdp` | Muestra `CDP is not enabled` |
| Repetir el ataque | El switch ya no registra vecinos falsos |
| `SW1# show processes cpu sorted` | Proceso CDP sin actividad |

---

## 📊 Tabla Resumen

| Campo | Valor |
|-------|-------|
| **Protocolo** | CDP (Cisco Discovery Protocol) |
| **Capa OSI** | Capa 2 — Enlace de Datos |
| **Impacto** | Agota tabla CDP, uso alto de CPU/memoria |
| **Contra-medida** | `no cdp run` / `no cdp enable` por interfaz |
| **Dirección Multicast** | `01:00:0C:CC:CC:CC` |

---

*Laboratorio de Seguridad en Redes · Entorno: PNetLab + Kali Linux Docker + Cisco IOSvL2*


