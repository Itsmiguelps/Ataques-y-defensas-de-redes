# 🟡 Ataque 03 — DHCP Spoofing: Servidor DHCP Falso (Rogue DHCP)
 
> **Entorno:** PNetLab + Kali Linux Docker + Cisco IOSvL2 + Cisco IOS Router  
> **Script:** `03_dhcp_spoofing.py` | **Herramienta:** Python 3 + Scapy

---

## ⚠️ Aviso Legal

> Uso **exclusivamente educativo** en entornos controlados y autorizados.  
> La ejecución en redes de producción sin autorización constituye un delito.

---

## 🎯 Objetivo del Laboratorio

Demostrar cómo un atacante puede desplegar un servidor DHCP fraudulento que responda a los clientes antes que el servidor legítimo, asignando parámetros de red maliciosos para realizar un ataque Man-in-the-Middle automático.

---

## 📋 Objetivo del Script

Implementar un servidor DHCP falso (Rogue DHCP) que responda a solicitudes de clientes antes que el servidor legítimo (Router R1), asignando como gateway la IP de Kali para realizar MitM de forma automática y redirigiendo las consultas DNS a un servidor controlado por el atacante.
### ¿Cómo funciona? — Proceso DORA
 
El script `dhcp_spoofing.py` implementa el handshake DORA completo:
 
```
Cliente           Kali (Rogue DHCP)        R1 (DHCP Legítimo)
   │                     │                         │
   │──── DISCOVER ──────►│ ◄─── DISCOVER ──────────│
   │                     │   (broadcast, todos lo ven)
   │◄─── OFFER ──────────│  [Kali responde primero]
   │   gateway=192.168.10.50 (Kali)
   │   dns=atacante
   │                     │
   │──── REQUEST ────────►│
   │◄─── ACK ─────────────│
   │                     │
   [Cliente usa Kali como gateway: MitM logrado]
```
 
1. El script **escucha DHCP Discover** en broadcast (puertos 67/68).
2. Al recibir un Discover, construye y envía un **DHCP Offer** con parámetros maliciosos.
3. Cuando el cliente responde con **DHCP Request**, el servidor falso confirma con **DHCP ACK**.
4. El cliente configura su red con los parámetros del atacante.
   
### Parámetros del Script

| Parámetro | Descripción | Ejemplo |
|-----------|-------------|---------|
| `-i` / `--interface` | Interfaz de red | `eth2` |
| `--pool` | Rango de IPs a asignar | `192.168.10.200-220` |
| `--gateway` | Gateway a anunciar (IP de Kali) | `192.168.10.50` |
| `--dns` | Servidor DNS a anunciar | `8.8.8.8` o IP atacante |
| `--netmask` | Máscara de subred | `255.255.255.0` |
| `--lease` | Tiempo de arrendamiento (segundos) | `600` |

### Requisitos para Utilizar la Herramienta

```bash
# Sistema operativo
Kali Linux (Docker en PNetLab)

# Dependencias
apt update && apt install python3-scapy -y

# Privilegios
sudo / root (obligatorio)

# Condiciones de red
- Kali en el mismo segmento L2 que los clientes DHCP
- IP forwarding habilitado para MitM transparente
- Flush previo de la interfaz (evitar conflictos)
- Router R1 configurado como servidor DHCP legítimo
```

---

## 🌐 Topología del Ataque

```
┌──────────────────────────────────────────────────────────┐
│  Topología: DHCP Spoofing                                 │
│                                                          │
│  192.168.10.1               192.168.10.50               │
│  ┌──────────┐               ┌──────────────┐            │
│  │ Router   │               │  Kali Linux  │            │
│  │   R1     │               │  (Rogue      │            │
│  │ DHCP srv │               │   DHCP)      │            │
│  │ Gateway  │               │  eth2        │            │
│  └────┬─────┘               └──────┬───────┘            │
│       │ e0/0                        │                    │
│       └──────────┬──────────────────┘                   │
│                  │                                       │
│           ┌──────┴──────┐                               │
│           │   Switch    │                               │
│           └──────┬──────┘                               │
│                  │                                       │
│           ┌──────┴──────┐                               │
│           │  PC-Víctima │                               │
│           │  (DHCP cli) │ ← recibe IP del atacante      │
│           └─────────────┘                               │
│                                                          │
│  FLUJO DORA:                                             │
│  Cliente → DISCOVER (broadcast)                          │
│  Kali   ← OFFER (primero en responder = gana)            │
│  Cliente → REQUEST (acepta oferta de Kali)               │
│  Kali   ← ACK    (confirma parámetros maliciosos)        │
└──────────────────────────────────────────────────────────┘
```

### Tabla de Interfaces y Direccionamiento

| Interfaz / Nodo | Rol y Dirección IP |
|-----------------|-------------------|
| R1 — e0/0 | 192.168.10.1/24 — Gateway + DHCP Server legítimo |
| DHCP Pool legítimo | 192.168.10.101 – 192.168.10.254 |
| Kali — eth2 | 192.168.10.50/24 — Atacante (Rogue DHCP) |
| PC-Víctima — eth1 | DHCP dinámico — obtiene IP del pool malicioso |
| Red | 192.168.10.0/24 |

---

## ⚙️ Configuración del Router R1 (Servidor DHCP Legítimo)

```ios
R1> enable
R1# configure terminal
R1(config)# interface e0/0
R1(config-if)# ip address 192.168.10.1 255.255.255.0
R1(config-if)# no shutdown
R1(config-if)# exit
R1(config)# ip dhcp excluded-address 192.168.10.1 192.168.10.100
R1(config)# ip dhcp pool POOL-LEGITIMO
R1(dhcp-config)# network 192.168.10.0 255.255.255.0
R1(dhcp-config)# default-router 192.168.10.1
R1(dhcp-config)# dns-server 8.8.8.8
R1(dhcp-config)# lease 0 2
R1(dhcp-config)# exit
R1(config)# service dhcp
```

## ⚙️ Configuración de Red en Kali

```bash
# Flush de la interfaz (evitar conflictos de IP)
ip addr flush dev eth2

# Asignar IP estática al atacante
ip addr add 192.168.10.50/24 dev eth2
ip link set eth2 up

# Ruta por defecto hacia el gateway legítimo
ip route add default via 192.168.10.1

# Habilitar IP forwarding (MitM transparente)
echo 1 > /proc/sys/net/ipv4/ip_forward
sudo sysctl -w net.ipv4.ip_forward=1
```

---

## 🔍 Funcionamiento del Script

El script `03_dhcp_spoofing.py` implementa el protocolo DHCP completo (handshake DORA) con parámetros maliciosos:

**Paso 1 — Escucha pasiva:**
```
Kali escucha paquetes DHCP Discover en broadcast (puerto UDP 67/68)
```

**Paso 2 — DHCP Offer malicioso:**
```
Al recibir un Discover, Kali construye y envía un DHCP Offer con:
  • IP asignada:  del pool falso (ej: 192.168.10.200)
  • Gateway:      192.168.10.50 (IP de Kali) ← MitM automático
  • DNS:          IP controlada por el atacante
  • Netmask:      255.255.255.0
  • Lease time:   600 segundos
```

**Paso 3 — DHCP Request y ACK:**
```
Cliente envía DHCP Request aceptando la oferta de Kali
Kali responde con DHCP ACK confirmando todos los parámetros
El handshake DORA queda completo
```

**Resultado:** El cliente configura su red con parámetros del atacante. Todo su tráfico pasa por Kali (gateway falso).

---

## 🚀 Ejecución del Ataque

```bash
# Preparar la interfaz de ataque
ip addr flush dev eth2
ip addr add 192.168.10.50/24 dev eth2
ip link set eth2 up
echo 1 > /proc/sys/net/ipv4/ip_forward

# Lanzar el servidor DHCP falso
sudo python3 03_dhcp_spoofing.py \
  -i eth2 \
  --pool 192.168.10.200-220 \
  --gateway 192.168.10.50 \
  --dns 8.8.8.8 \
  --netmask 255.255.255.0

# En PC-Víctima — renovar DHCP para obtener IP del atacante
sudo dhclient -r eth1    # liberar IP actual
sudo dhclient -v eth1    # solicitar nueva IP
```

### Verificación del Ataque

```bash
# En la víctima — verificar configuración de red recibida
ip addr show eth1
# Esperado: inet 192.168.10.200/24  (IP del pool del atacante)

ip route show
# Esperado: default via 192.168.10.50  (gateway = Kali)

# En R1 — verificar que el pool legítimo NO fue usado
show ip dhcp binding
show ip dhcp pool
# Esperado: sin nuevas asignaciones del pool legítimo
```

---

## 🖼️ Capturas de Pantalla

| Captura | Descripción |
|---------|-------------|
| `screenshots/01_topologia.png` | Vista de la topología en PNetLab |
| `screenshots/02_r1_dhcp_config.png` | Configuración DHCP en Router R1 |
| `screenshots/03_ataque_inicio.png` | Servidor Rogue DHCP activo en Kali |
| `screenshots/04_victima_ip_atacante.png` | Víctima con IP y gateway del atacante |
| `screenshots/05_r1_sin_binding.png` | R1 sin asignaciones (pool no usado) |
| `screenshots/06_contramedia_dhcp_snooping.png` | DHCP Snooping configurado |

---

## 🛡️ Contra-medida

### DHCP Snooping

```ios
! Habilitar DHCP Snooping globalmente
SW(config)# ip dhcp snooping
SW(config)# ip dhcp snooping vlan 1
SW(config)# no ip dhcp snooping information option

! Puerto hacia Router R1 como trusted (único que puede servir DHCP)
SW(config)# interface e0/3
SW(config-if)# ip dhcp snooping trust

! Todos los demás puertos quedan como untrusted (comportamiento por defecto)
! → Los paquetes DHCP Offer/ACK desde puertos untrusted son descartados
```

### Verificación de la Contra-medida

```ios
! Confirmar que DHCP Snooping está activo
SW# show ip dhcp snooping
SW# show ip dhcp snooping binding

! Repetir el ataque con DHCP Snooping activo
! Resultado esperado: el DHCP Offer de Kali es descartado por el switch
! La víctima recibe IP únicamente del servidor legítimo R1
```

**Por qué funciona:** DHCP Snooping clasifica los puertos en *trusted* y *untrusted*. Solo los puertos trusted pueden enviar DHCP Offers/ACK. Cualquier Offer desde un puerto untrusted (como el de Kali) es descartado silenciosamente.

---

## 📹 Video de Demostración

> **Archivo:** `video/03_dhcp_spoofing.mp4`  

El video debe incluir:
- ✅ Topología visible con nombre y matrícula del estudiante
- ✅ Hora y fecha visibles en pantalla
- ✅ Cara y voz del presentador
- ✅ Handshake DORA visible (Discover → Offer → Request → ACK)
- ✅ Víctima con gateway = IP de Kali
- ✅ Demostración de DHCP Snooping como contra-medida

---

---
 
*Laboratorio de Seguridad en Redes · Entorno: PNetLab + Kali Linux Docker + Cisco IOSvL2*
