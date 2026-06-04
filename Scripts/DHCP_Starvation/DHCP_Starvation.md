# 🟠 Ataque 04 — DHCP Starvation: Agotamiento del Pool DHCP

> **Entorno:** PNetLab + Kali Linux Docker + Cisco IOSvL2 + Cisco IOS Router  
> **Script:** `dhcp_starvation.py` | **Herramienta:** Python 3 + Scapy

---

## ⚠️ Aviso Legal

> Uso **exclusivamente educativo** en entornos controlados y autorizados.  
> La ejecución en redes de producción sin autorización constituye un delito.

---

## 📋 Información General
 
| Campo | Detalle |
|-------|---------|
| **Asignatura** | Seguridad en Redes |
| **Entorno** | PNetLab + Kali Linux Docker + Cisco IOSvL2 |
| **Script** | `dhcp_starvation.py` |
| **Protocolo atacado** | DHCP — Dynamic Host Configuration Protocol (RFC 2131) |
| **Herramienta** | Python 3 + Scapy |
| **Impacto** | DoS — Clientes legítimos no pueden obtener configuración de red |
 
---

## 🎯 Objetivo del Laboratorio

Demostrar cómo un atacante puede agotar el pool de direcciones IP de un servidor DHCP enviando solicitudes masivas con MACs falsas, impidiendo que clientes legítimos obtengan configuración de red (ataque DoS de capa de red).

---

## 📋 Objetivo del Script

Agotar el pool de direcciones IP del servidor DHCP legítimo enviando solicitudes DHCP con cientos de MACs falsas y aleatorias, impidiendo que clientes legítimos obtengan configuración de red.
### ¿Cómo funciona?
 
El script `dhcp_starvation.py` opera en dos modos:
 
**Modo rápido (solo Discovers):**
```
Kali (MAC-falsa-1) ──► DISCOVER ──► R1  →  R1 reserva IP temporalmente
Kali (MAC-falsa-2) ──► DISCOVER ──► R1  →  R1 reserva otra IP
Kali (MAC-falsa-N) ──► DISCOVER ──► R1  →  Pool agotado
```
 
**Modo confirmado (handshake DORA completo):**
```
Kali (MAC-falsa)  ──► DISCOVER ──► R1
                  ◄── OFFER    ◄── R1  (IP asignada)
                  ──► REQUEST  ──► R1
                  ◄── ACK      ◄── R1  [IP bloqueada definitivamente]
```
 
El script genera MACs aleatorias con **OUIs de fabricantes comunes** (VMware, VirtualBox, QEMU) para mayor credibilidad. Cada solicitud incluye campos `xid` y `hostname` aleatorios.
 
---

### Parámetros del Script

| Parámetro | Descripción | Valor por defecto |
|-----------|-------------|-------------------|
| `-i` / `--interface` | Interfaz de red | Requerido |
| `-c` / `--count` | Número de solicitudes DHCP a enviar | `254` |
| `--confirm` | Completar handshake DORA (bloquea IPs definitivamente) | Desactivado |
| `--delay` | Retardo entre solicitudes (segundos) | `0.05` s |
| `--timeout` | Timeout esperando DHCP Offer en modo `--confirm` | `2` s |

### Requisitos para Utilizar la Herramienta

```bash
# Sistema operativo
Kali Linux (Docker en PNetLab)

# Dependencias
apt update && apt install python3-scapy -y

# Privilegios
sudo / root (obligatorio)

# Condiciones de red
- Kali en el mismo segmento L2 que el servidor DHCP
- Router R1 configurado con pool DHCP activo
- Sin DHCP Snooping o Port Security activos (para que el ataque funcione)
```

---

## 🌐 Topología del Ataque

```
┌──────────────────────────────────────────────────────────┐
│  Topología: DHCP Starvation                              │
│                                                          │
│   7.41.10.1                    7.41.10.50                │
│  ┌──────────┐               ┌──────────────┐             │
│  │ Router   │               │  Kali Linux  │             │
│  │   R1     │               │  (Atacante)  │             │
│  │ DHCP srv │◄──────────────│  eth2        │             │
│  │ Pool:    │  Flood DHCP   │              │             │
│  │.101-.254 │  Discovers    │ MACs aleats  │             │
│  └──────────┘               └──────────────┘             │
│       │                                                  │
│  ┌────┴──────┐                                           │
│  │  Switch   │                                           │
│  └────┬──────┘                                           │
│       │                                                  │
│  ┌────┴──────┐                                           │
│  │PC-Víctima │ ← "No DHCPOFFERS received"                │
│  │  (falla)  │   Pool agotado — sin IP disponible        │
│  └───────────┘                                           │
│                                                          │
│  RESULTADO: Pool 7.41.10.101–.254 (154 IPs) agotado      │
└──────────────────────────────────────────────────────────┘
```

### Tabla de Interfaces y Direccionamiento

| Interfaz / Nodo | Rol y Dirección IP |
|-----------------|-------------------|
| R1 — e0/0 | 7.41.10.1/24 — Gateway + DHCP Server |
| DHCP Pool | 7.41.10.101 – 7.41.10.254 (154 IPs disponibles) |
| Kali — eth2 | 7.41.10.50/24 — Atacante |
| PC-Víctima — eth1 | DHCP dinámico — falla al solicitar IP |
| Red | 7.41.10.0/24 |

---

## ⚙️ Configuración del Router R1

Idéntica a la del Ataque 03 (DHCP Spoofing). El pool es `7.41.10.101–254` (154 IPs disponibles para agotar).

```cisco
R1> enable
R1# configure terminal
R1(config)# interface e0/0
R1(config-if)# ip address 7.41.10.1 255.255.255.0
R1(config-if)# no shutdown
R1(config-if)# exit
R1(config)# ip dhcp excluded-address 7.41.10.1 7.41.10.100
R1(config)# ip dhcp pool POOL-LEGITIMO
R1(dhcp-config)# network 7.41.10.0 255.255.255.0
R1(dhcp-config)# default-router 7.41.10.1
R1(dhcp-config)# dns-server 8.8.8.8
R1(dhcp-config)# lease 0 2
R1(dhcp-config)# exit
R1(config)# service dhcp
```

---

## 🔍 Funcionamiento del Script

El script `dhcp_starvation.py` genera solicitudes DHCP masivas con identidades falsas:

**Generación de MACs falsas:**
```
MACs aleatorias con OUIs de fabricantes comunes:
  • VMware:     00:50:56:XX:XX:XX
  • VirtualBox: 08:00:27:XX:XX:XX
  • QEMU:       52:54:00:XX:XX:XX
```

**Por cada MAC generada, el script construye:**
```
DHCP Discover con:
  • src MAC: MAC aleatoria generada
  • xid:     Transaction ID aleatorio
  • hostname: nombre de host aleatorio
```

**Modos de operación:**

| Modo | Comportamiento | Impacto |
|------|---------------|---------|
| **Básico** (sin `--confirm`) | Solo envía Discovers a alta velocidad | Satura el servidor, impacto temporal |
| **Confirmado** (`--confirm`) | Espera Offer y responde con Request+ACK | Bloquea IPs definitivamente hasta expirar el lease |

---

## 🚀 Ejecución del Ataque

```bash
# Configurar interfaz
ip addr add 7.41.10.50/24 dev eth2
ip link set eth2 up

# Instalar dependencias
apt update && apt install python3-scapy -y

# Modo rápido — solo envía DHCP Discovers (154 paquetes para agotar el pool)
sudo python3 0dhcp_starvation.py -i eth2 -c 254

# Modo confirmado — completa handshake DORA y bloquea IPs definitivamente
sudo python3 dhcp_starvation.py -i eth2 -c 500 --confirm --delay 0.1

# Verificar en R1 que el pool se agotó
show ip dhcp pool
show ip dhcp binding

# Intentar obtener IP desde la víctima (debe fallar)
sudo dhclient -r eth1
sudo dhclient -v eth1
# Esperado: "No DHCPOFFERS received"
```

### Verificación del Ataque

```ios
! En Router R1 — verificar agotamiento del pool
R1# show ip dhcp pool
! Resultado esperado: Available addresses = 0 (agotado)

R1# show ip dhcp binding
! Resultado esperado: 154 líneas de asignaciones con MACs falsas

R1# show ip dhcp conflict
! Posibles conflictos detectados por el servidor
```

```bash
# En PC-Víctima — confirmar que no puede obtener IP
sudo dhclient -v eth1
# Resultado esperado:
# DHCPDISCOVER on eth1 to 255.255.255.255 port 67 interval 3
# No DHCPOFFERS received.
```

---

---

## 🛡️ Contra-medida

### Port Security — Limitar MACs por Puerto

```ios
! Limitar número de MACs únicas permitidas por puerto
SW(config)# interface e0/0
SW(config-if)# switchport mode access
SW(config-if)# switchport port-security
SW(config-if)# switchport port-security maximum 2
SW(config-if)# switchport port-security violation shutdown
```

**Efecto:** El switch solo permite un máximo de 2 MACs distintas por puerto. Si Kali intenta registrar una tercera MAC, el puerto entra en estado `err-disabled`, deteniendo el ataque.

### Complemento: DHCP Snooping con Rate Limiting

```ios
! Limitar tasa de paquetes DHCP por puerto
SW(config)# interface e0/0
SW(config-if)# ip dhcp snooping limit rate 10
! Máximo 10 paquetes DHCP por segundo por puerto
! Superar este límite desactiva el puerto automáticamente
```

### Verificación de la Contra-medida

```ios
! Verificar Port Security
SW# show port-security interface e0/0
! Campo "Security Violation Count" incrementa con el ataque
! Puerto debe pasar a err-disabled si se supera el máximo

! Repetir el ataque con la contra-medida activa
! Resultado esperado: puerto deshabilitado después de pocas solicitudes
SW# show interface e0/0 status
! Resultado esperado: "err-disabled"
```
---
 
## 📊 Tabla Resumen
 
| Campo | Valor |
|-------|-------|
| **Protocolo** | DHCP (RFC 2131) |
| **Capa OSI** | Capa 2/3 — Enlace / Red |
| **Impacto** | DoS: clientes sin IP, sin conectividad de red |
| **Contra-medida** | `port-security maximum 2` + `violation shutdown` |
| **IPs en pool objetivo** | 154 (7.41.10.101 – 7.41.10.254) |
 
---
---

## 📹 Video de Demostración

> **Archivo:** `video/demo_04_dhcp_starvation.mp4`  

El video debe incluir:
- ✅ Topología visible con nombre y matrícula del estudiante
- ✅ Hora y fecha visibles en pantalla
- ✅ Cara y voz del presentador
- ✅ Pool DHCP disponible antes del ataque
- ✅ Ejecución del script con MACs aleatorias
- ✅ Pool agotado (`available addresses = 0`)
- ✅ Víctima sin poder obtener IP

---

*Laboratorio de Seguridad en Redes · Entorno: PNetLab + Kali Linux Docker + Cisco IOSvL2*
