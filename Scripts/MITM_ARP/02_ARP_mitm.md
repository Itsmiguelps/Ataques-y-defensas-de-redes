# 🟠 Ataque 02 — ARP MitM: Man-in-the-Middle mediante Envenenamiento ARP

> **Asignatura:** Seguridad en Redes  
> **Entorno:** PNetLab + Kali Linux Docker + Cisco IOSvL2  
> **Script:** `02_arp_mitm.py` | **Herramienta:** Python 3 + Scapy

---

## ⚠️ Aviso Legal

> Uso **exclusivamente educativo** en entornos controlados y autorizados.  
> La ejecución en redes de producción sin autorización constituye un delito.

---

## 🎯 Objetivo del Laboratorio

Demostrar cómo el protocolo ARP (Address Resolution Protocol) puede ser explotado para realizar un ataque Man-in-the-Middle, interceptando el tráfico entre dos hosts de la red sin que ninguno de ellos lo detecte.

---

## 📋 Objetivo del Script

Interceptar todo el tráfico entre dos víctimas (o víctima ↔ gateway) mediante el envenenamiento de sus tablas ARP, posicionando a Kali como intermediario transparente para capturar o modificar el tráfico en tránsito.

### Parámetros del Script

| Parámetro | Descripción | Ejemplo |
|-----------|-------------|---------|
| `-t1` | IP de la víctima 1 | `192.168.1.10` |
| `-t2` | IP de la víctima 2 | `192.168.1.20` |
| `-i` / `--iface` | Interfaz de red | `eth2` |

### Requisitos para Utilizar la Herramienta

```bash
# Sistema operativo
Kali Linux (Docker en PNetLab)

# Dependencias
apt update && apt install python3-scapy -y

# Privilegios
sudo / root (obligatorio)

# Condiciones de red
- IP forwarding habilitado: echo 1 > /proc/sys/net/ipv4/ip_forward
- Kali en el mismo segmento L2 que las víctimas
- Interfaz eth2 configurada en el rango 192.168.1.0/24
```

---

## 🌐 Topología del Ataque

```
┌─────────────────────────────────────────────────────────┐
│  Topología: ARP MitM                                     │
│                                                          │
│  192.168.1.10        192.168.1.20        192.168.1.50   │
│  ┌──────────┐        ┌──────────┐        ┌──────────┐   │
│  │Víctima 1 │        │Víctima 2 │        │   Kali   │   │
│  │  eth1    │        │  eth1    │        │   eth2   │   │
│  └────┬─────┘        └────┬─────┘        └────┬─────┘   │
│       │                   │                    │         │
│       └────────────┬──────┘                    │         │
│                    │         ┌─────────────────┘         │
│               ┌────┴─────────┴────┐                      │
│               │       SW2        │                       │
│               │   (e1/1 trunk)   │                       │
│               └────────┬─────────┘                       │
│                        │ e1/0 trunk VLAN10,20            │
│               ┌────────┴─────────┐                       │
│               │       SW1        │                       │
│               │     (Core)       │                       │
│               └──────────────────┘                       │
└─────────────────────────────────────────────────────────┘

  FLUJO DEL ATAQUE:
  Víctima1 ──→ Kali ──→ Víctima2   (tráfico interceptado)
  Kali envía ARP Replies falsos a ambas víctimas
```

### Tabla de Interfaces y Direccionamiento

| Interfaz / Nodo | Rol y Dirección IP |
|-----------------|-------------------|
| SW1 — e0/0 | Trunk VLAN 10, 20 hacia SW2 |
| SW2 — e1/0 | Trunk VLAN 10, 20 (hacia SW1) |
| SW2 — e1/1 | Trunk VLAN 10, 20 (hacia Kali/víctimas) |
| Kali — eth2 | 192.168.1.50/24 (atacante — intermediario) |
| PC-Víctima 1 — eth1 | 192.168.1.10/24 |
| PC-Víctima 2 — eth1 | 192.168.1.20/24 |
| VLANs | VLAN 10 ADMIN · VLAN 20 USERS |

---

## ⚙️ Configuración de Red

```bash
# ── Kali — Interfaz de ataque ──
ip addr add 192.168.1.50/24 dev eth2
ip link set eth2 up
echo 1 > /proc/sys/net/ipv4/ip_forward   # OBLIGATORIO para reenvío de tráfico

# ── PC-Víctima 1 ──
ip addr add 192.168.1.10/24 dev eth1
ip link set eth1 up

# ── PC-Víctima 2 ──
ip addr add 192.168.1.20/24 dev eth1
ip link set eth1 up
```

---

## 🔍 Funcionamiento del Script

El script `02_arp_mitm.py` implementa el ataque en dos fases continuas:

**Fase 1 — Envenenamiento ARP (periódico, cada 1 segundo):**

```
Kali → Víctima 1: "La IP de Víctima2 (192.168.1.20) tiene la MAC de Kali"
Kali → Víctima 2: "La IP de Víctima1 (192.168.1.10) tiene la MAC de Kali"
```

Ambas víctimas actualizan su caché ARP con la MAC de Kali. Todo su tráfico mutuo pasa ahora por Kali.

**Fase 2 — Reenvío transparente:**

```
Víctima1 → Kali (creyendo que es Víctima2) → Kali reenvía → Víctima2
```

El IP forwarding habilitado permite que Kali retransmita el tráfico, haciendo el ataque invisible para las víctimas.

**Fase 3 — Restauración (al presionar Ctrl+C):**

El script envía ARP Replies correctos con las MACs originales de cada host, restaurando las tablas ARP y dejando la red en estado normal.

---

## 🚀 Ejecución del Ataque

```bash
# Configurar interfaz y habilitar IP forwarding
ip addr add 192.168.1.50/24 dev eth2
ip link set eth2 up
echo 1 > /proc/sys/net/ipv4/ip_forward

# Ejecutar ataque MitM entre Víctima 1 y Víctima 2
sudo python3 02_arp_mitm.py -t1 192.168.1.10 -t2 192.168.1.20 -i eth2

# En una segunda terminal — verificar que el ARP está envenenado
arp -n
# Resultado esperado: la MAC de 192.168.1.20 debe ser la MAC de Kali
```

### Verificación del Ataque

```bash
# En cualquier víctima (durante el ataque)
arp -n
# Resultado esperado:
# 192.168.1.20  ether  AA:BB:CC:DD:EE:FF  (← MAC de Kali)

# Ver tráfico interceptado en Kali
tcpdump -i eth2 -n host 192.168.1.10
# Resultado esperado: paquetes de y hacia Víctima 1 visibles en Kali
```

---

## 🖼️ Capturas de Pantalla

| Captura | Descripción |
|---------|-------------|
| `screenshots/01_topologia.png` | Vista de la topología en PNetLab |
| `screenshots/02_arp_antes.png` | Tabla ARP limpia en víctimas (antes del ataque) |
| `screenshots/03_ataque_ejecucion.png` | Ejecución del script en Kali |
| `screenshots/04_arp_envenenado.png` | Tabla ARP con MAC de Kali |
| `screenshots/05_tcpdump.png` | Tráfico interceptado capturado con tcpdump |
| `screenshots/06_contramedia.png` | Configuración DAI en el switch |

---

## 🛡️ Contra-medida

### Dynamic ARP Inspection (DAI) + Port Security

```ios
! ── Habilitar DAI en VLAN 1 ──
SW(config)# ip arp inspection vlan 1

! Puerto de uplink (hacia router/otros switches) como trusted
SW(config)# interface e1/0
SW(config-if)# ip arp inspection trust

! Port Security en puertos de acceso hacia usuarios
SW(config)# interface range e0/0 - 2
SW(config-if-range)# switchport mode access
SW(config-if-range)# switchport port-security
SW(config-if-range)# switchport port-security maximum 1
SW(config-if-range)# switchport port-security violation shutdown
```

### Verificación de la Contra-medida

```ios
! Verificar DAI activo
SW# show ip arp inspection vlan 1

! Repetir el ataque con DAI activo
! Resultado esperado: paquetes ARP falsos descartados automáticamente

! Ver estadísticas de paquetes inspeccionados/descartados
SW# show ip arp inspection statistics vlan 1
```

**Por qué funciona:** DAI valida cada paquete ARP contra la tabla de DHCP Snooping Binding. Si la MAC+IP del paquete ARP no coincide con un binding legítimo, el paquete es descartado silenciosamente.

---

## 📹 Video de Demostración

> **Archivo:** `video/02_arp_mitm`  

El video debe incluir:
- ✅ Topología visible con nombre y matrícula del estudiante
- ✅ Hora y fecha visibles en pantalla
- ✅ Cara y voz del presentador
- ✅ Tabla ARP antes y después del ataque
- ✅ Tráfico interceptado visible en tcpdump
- ✅ Demostración de la contra-medida (DAI)

---

*← [Ataque anterior: 01 — CDP DoS](#) | [Volver al repositorio principal](#) | Siguiente: [03 — DHCP Spoofing →](#)*
