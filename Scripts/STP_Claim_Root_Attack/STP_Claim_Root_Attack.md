# 🟣 Ataque 06 — STP Root Claim: Usurpación del Root Bridge en Spanning Tree

> **Entorno:** PNetLab + Kali Linux Docker + Cisco IOSvL2 (3 switches)  
> **Script:** `stp_root_claim.py` | **Herramienta:** Python 3 + Scapy

---

## ⚠️ Aviso Legal

> Uso **exclusivamente educativo** en entornos controlados y autorizados.  
> La ejecución en redes de producción sin autorización constituye un delito.

---

---
 
## 📋 Información General
 
| Campo | Detalle |
|-------|---------|
| **Asignatura** | Seguridad en Redes |
| **Entorno** | PNetLab + Kali Linux Docker + Cisco IOSvL2 |
| **Script** | `06_stp_root_claim.py` |
| **Protocolo atacado** | STP 802.1D / PVST+ (Cisco) |
| **Herramienta** | Python 3 + Scapy |
| **Impacto** | Control de topología L2 + DoS de 30–50 segundos |
 
---

## 🎯 Objetivo del Laboratorio

Demostrar cómo un atacante puede usurpar el rol de Root Bridge en una topología STP (Spanning Tree Protocol), forzando a toda la red a reconvergir y causando una interrupción del tráfico de 30 a 50 segundos, además de permitir posicionar a Kali como punto central por el cual fluye todo el tráfico de la red.

---
### ¿Cómo funciona?
 
El protocolo STP elige el Root Bridge basándose en el **Bridge ID más bajo** (Priority + MAC). El atacante explota esto enviando BPDUs con Priority = 0:
 
```
Estado normal:
  SW1 (Priority 4096) = Root Bridge legítimo
  SW2 y SW3 calculan rutas hacia SW1
 
  SW1 ──── trunk ──── SW2
   └─────── trunk ──── SW3 ──── trunk ──── SW2
 
Durante el ataque:
  Kali envía BPDU: "Soy el Root, Priority = 0"
  
  SW1 recibe BPDU (0 < 4096) → inicia reelección
  SW2 recibe BPDU (0 < 4096) → inicia reelección
  SW3 recibe BPDU (0 < 4096) → inicia reelección
  
  ┌─ Kali (Priority 0) = NUEVO Root Bridge (ilegítimo)
  │
  [30-50 segundos de reconvergencia STP = red caída]
```
 
El script `stp_root_claim.py` construye **BPDUs de configuración STP/PVST+** con:
- Bridge Priority: **0** (menor posible = máxima prioridad)
- Root Path Cost: **0** (afirma estar directamente conectado)
- Enviados a la dirección multicast `01:80:C2:00:00:00` cada 2 segundos
---

## 📋 Objetivo del Script

Usurpar el rol de Root Bridge en la topología STP enviando BPDUs de configuración con Bridge Priority 0 (la máxima prioridad posible), forzando a todos los switches a reconvergir con Kali como nuevo Root Bridge y causando una caída del tráfico de 30 a 50 segundos.

### Parámetros del Script

| Parámetro | Descripción | Valor por defecto |
|-----------|-------------|-------------------|
| `-i` / `--interface` | Interfaz de red | Requerido |
| `--priority` | Bridge Priority a anunciar | `0` (máxima prioridad) |
| `--hello` | Intervalo entre BPDUs (segundos) | `2` |
| `--vlan` | ID de VLAN para PVST+ Cisco | — |
| `--mac` | MAC del Bridge ID | MAC de la interfaz |
| `--duration` | Duración en segundos (`0` = continuo) | `0` |

### Requisitos para Utilizar la Herramienta

```bash
# Sistema operativo
Kali Linux (Docker en PNetLab)

# Dependencias
apt update && apt install python3-scapy -y

# Privilegios
sudo / root (obligatorio)

# Condiciones de red
- Kali conectada a un puerto de acceso VLAN 10 de SW1
- SW1 configurado como Root Bridge legítimo (priority 4096)
- STP/PVST+ habilitado en todos los switches
- Sin BPDU Guard ni Root Guard activos (para que el ataque funcione)
```

---

## 🌐 Topología del Ataque

```
┌──────────────────────────────────────────────────────────┐
│  Topología: STP Root Claim                               │
│                                                          │
│              ┌──────────────┐                            │
│              │     SW1      │  ← Root Bridge legítimo    │
│              │ Priority 4096│     (antes del ataque)     │
│              │  VTP Server  │                            │
│              └──┬───────┬───┘                            │
│            e1/0 │       │ e0/3                           │
│         trunk   │       │ trunk VLAN 10                  │
│              ┌──┴───┐ ┌─┴────┐                           │  
│              │ SW2  │ │ SW3  │                           │
│              │VTP   ├─┤ VTP  │                           │
│              │Client│ │Client│                           │
│              └──────┘ └──────┘                           │
│                   │                                      │
│              e0/0 │ Access VLAN 10                       │
│              ┌────┴──────┐                               │
│              │Kali Linux │ ← ATACANTE                    │
│              │  eth2     │   Priority 0 > Priority 4096  │
│              │192.168.   │   → Kali gana la elección     │
│              │ 10.50/24  │   → Red reconverge            │
│              └───────────┘   → DoS 30-50 segundos        │
│                                                          │
│  DESPUÉS DEL ATAQUE:                                     │
│  Root Bridge = KALI (priority 0)                         │
│  Todo el tráfico fluye a través de Kali                  │
└──────────────────────────────────────────────────────────┘
```

### Tabla de Interfaces y Configuración

| Interfaz / Nodo | Configuración |
|-----------------|---------------|
| SW1 | VTP Server · PVST priority 4096 · Root Bridge legítimo |
| SW1 — e0/0 | Access VLAN 10 (hacia Kali) |
| SW1 — e1/0 | Trunk VLAN 10 (hacia SW2) |
| SW1 — e0/3 | Trunk VLAN 10 (hacia SW3) |
| SW2 — e0/0 | Trunk VLAN 10 (hacia SW1) |
| SW2 — e0/1 | Trunk VLAN 10 (hacia SW3) |
| SW3 — e0/0 | Trunk VLAN 10 (hacia SW1) |
| SW3 — e0/1 | Trunk VLAN 10 (hacia SW2) |
| Kali — eth2 | 192.168.10.50/24 conectado a SW1 e0/0 |
| VLAN | VLAN 10 ADMIN · VTP domain: EMPRESA |

---

## ⚙️ Configuración de SW1, SW2 y SW3

```cisco
! ── SW1 (VTP Server + Root Bridge legítimo) ──
conf t
vtp domain EMPRESA
vtp mode server
vtp password cisco
vlan 10
 name ADMIN
interface e0/0
 switchport mode access
 switchport access vlan 10
 no shutdown
interface e1/0
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk allowed vlan 10
 no shutdown
interface e0/3
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk allowed vlan 10
 no shutdown
spanning-tree mode pvst
spanning-tree vlan 10 priority 4096
end

! ── SW2 (VTP Client) ──
conf t
vtp domain EMPRESA
vtp mode client
vtp password cisco
interface e0/0
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk allowed vlan 10
 no shutdown
interface e0/1
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk allowed vlan 10
 no shutdown
spanning-tree mode pvst
spanning-tree vlan 10 priority 4096
end

! ── SW3 (VTP Client) — misma configuración que SW2 ──
```

---

## 🔍 Funcionamiento del Script

El script `stp_root_claim.py` inyecta BPDUs falsas que reclaiman el rol de Root Bridge:

**Construcción del BPDU malicioso:**
```
Destino multicast STP: 01:80:C2:00:00:00
Encapsulación:         LLC (802.2) → BPDU de configuración STP

Campos clave del BPDU:
  • Root Priority:      0     ← Máxima prioridad STP posible
  • Root Path Cost:     0     ← Sin costo de camino
  • Bridge Priority:    0     ← Kali se anuncia como Root Bridge
  • Bridge MAC:         MAC de eth2 de Kali
  • Hello Time:         2s    ← Timer STP estándar
```

**Proceso de reelección STP:**
```
1. Kali envía BPDU con Priority 0 cada 2 segundos
2. SW1 recibe BPDU con Priority 0 < Priority 4096 propio
3. SW1 inicia proceso de reelección: cede el rol de Root
4. SW2 y SW3 también actualizan su Root Bridge
5. Todos los puertos recalculan estado STP (30-50 segundos de reconvergencia)
6. Kali queda como Root Bridge → tráfico fluye hacia Kali
```

**Tipo de BPDU usado:**
```
Para STP estándar (802.1D): BPDU de configuración estándar
Para PVST+ Cisco:           BPDU con encapsulación SNAP específica
                            OUI: 0x00000C, code: 0x010B
                            Tag PVST+ con VLAN ID embebido
```
---

## 🚀 Ejecución del Ataque

```bash
# Configurar interfaz de Kali
ip addr add 7.41.10.50/24 dev eth2
ip link set eth2 up

# STP estándar (802.1D) — modo básico
sudo python3 stp_root_claim.py -i eth2

# PVST+ Cisco — con prioridad 0 en VLAN 10 y hello timer de 1s
sudo python3 stp_root_claim.py -i eth2 --priority 0 --hello 1 --vlan 10

```

### Verificación del Ataque (en el Switch, esperar ~30 segundos)

```cisco
! En SW1 — verificar quién es el Root Bridge ahora
SW1# show spanning-tree vlan 10

! Resultado esperado DURANTE el ataque:
! Root ID  Priority  0               ← PRIORIDAD 0 = KALI
!          Address   AA:BB:CC:DD:EE:FF  ← MAC de Kali (eth2)
!          Port      e0/0            ← puerto hacia Kali

! Ver mensajes de cambio de topología en logs
SW1# show log | include TOPO
! Esperado: %SPANTREE-5-TOPOTRAP o %SPANTREE-5-ROOTCHANGE

! Ver cambios de topología (contador)
SW1# show spanning-tree detail | include topology
```

---
---

## 🛡️ Contra-medida

### BPDU Guard + Root Guard

```cisco
! En la interfaz hacia Kali (e0/0 de SW1)
SW1(config)# interface e0/0

! Root Guard — descarta BPDUs que reclaimen ser Root con menor prioridad
SW1(config-if)# spanning-tree guard root

! PortFast — acelera el estado del puerto (para puertos de acceso)
SW1(config-if)# spanning-tree portfast

! BPDU Guard — desactiva el puerto si recibe CUALQUIER BPDU
SW1(config-if)# spanning-tree bpduguard enable
```

### Diferencia entre Root Guard y BPDU Guard

| Mecanismo | Acción | Cuándo usar |
|-----------|--------|-------------|
| **Root Guard** | Descarta BPDUs con prioridad menor; bloquea el puerto en `root-inconsistent` | Puertos donde nunca debería llegar un Root Bridge externo |
| **BPDU Guard** | Desactiva el puerto (`err-disabled`) si recibe CUALQUIER BPDU | Puertos de acceso hacia usuarios finales (con PortFast) |

### Verificación de la Contra-medida

```cisco
! Repetir el ataque con BPDU Guard activo
! Resultado esperado: puerto e0/0 pasa a err-disabled inmediatamente

SW1# show spanning-tree vlan 10
! Root Bridge sigue siendo SW1 (priority 4096) ✓

SW1# show log
! Mensaje: %SPANTREE-2-BLOCK_BPDUGUARD: Received BPDU on port
!          GigabitEthernet0/0 with BPDU Guard enabled. Disabling port.

SW1# show interface e0/0 status
! Resultado: err-disabled

! Para restaurar (después de eliminar la amenaza)
SW1(config)# interface e0/0
SW1(config-if)# shutdown
SW1(config-if)# no shutdown
```
---
---
 
## 📊 Tabla Resumen
 
| Campo | Valor |
|-------|-------|
| **Protocolo** | STP 802.1D / PVST+ |
| **Capa OSI** | Capa 2 — Enlace de Datos |
| **Impacto** | Control de topología L2 + DoS 30–50 segundos |
| **Contra-medida** | `bpduguard enable` + `guard root` |
| **Dirección Multicast** | `01:80:C2:00:00:00` |
| **Priority del atacante** | 0 (menor posible) vs. 4096 del switch legítimo |
 
---

## 📹 Video de Demostración

> **Archivo:** `video/demo_06_stp_root_claim.mp4`  

El video debe incluir:
- ✅ Topología visible con nombre y matrícula del estudiante (3 switches visibles)
- ✅ Hora y fecha visibles en pantalla
- ✅ Cara y voz del presentador
- ✅ `show spanning-tree` con SW1 como Root antes del ataque
- ✅ Ejecución del script con BPDUs de prioridad 0
- ✅ `show spanning-tree` con Kali como Root Bridge después del ataque
- ✅ Logs de reconvergencia STP en switches
- ✅ BPDU Guard como contra-medida (puerto en err-disabled)

---

*Laboratorio de Seguridad en Redes · Entorno: PNetLab + Kali Linux Docker + Cisco IOSvL2*
