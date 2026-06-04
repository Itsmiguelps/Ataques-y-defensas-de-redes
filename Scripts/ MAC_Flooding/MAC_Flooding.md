# 🔵 Ataque 05 — MAC Flooding: Desbordamiento de la Tabla CAM del Switch

> **Entorno:** PNetLab + Kali Linux Docker + Cisco IOSvL2  
> **Script:** `mac_flooding.py` | **Herramienta:** Python 3 + Scapy

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
| **Script** | `05_mac_flooding.py` |
| **Protocolo atacado** | Ethernet 802.3 — Tabla CAM del Switch |
| **Herramienta** | Python 3 + Scapy |
| **Impacto** | Switch en modo hub → sniffing de toda la red |
 
---
## 🎯 Objetivo del Laboratorio

Demostrar cómo el desbordamiento de la tabla CAM (Content Addressable Memory) de un switch Cisco provoca que el dispositivo deje de funcionar como switch inteligente y pase a comportarse como un hub, reenviando todas las tramas a todos los puertos y exponiendo el tráfico de la red.

---
### ¿Cómo funciona?
 
```
Tabla CAM normal (switch inteligente):
┌────────────────────────────────────────┐
│ MAC              │ Puerto │ VLAN       │
│──────────────────┼────────┼────────────│
│ AA:BB:CC:DD:EE:01│ e0/0   │ 10         │
│ AA:BB:CC:DD:EE:02│ e0/1   │ 10         │
│ ...              │ ...    │ ...        │
│ [capacidad: ~8192 entradas]            │
└────────────────────────────────────────┘
 
Después del ataque (tabla CAM desbordada):
┌────────────────────────────────────────┐
│ Tabla llena → Switch no sabe a dónde  │
│ enviar frames → Modo FLOODING a todos │
│ los puertos (comportamiento de hub)   │
└────────────────────────────────────────┘
```
 
El script `05_mac_flooding.py`:
1. Genera tramas Ethernet con **MACs de origen y destino completamente aleatorias**.
2. Opcionalmente añade **tag 802.1Q** para ataques en VLANs específicas.
3. Envía las tramas en **lotes de 100 mediante múltiples hilos paralelos** para maximizar la tasa.
4. La tabla CAM (~8192 entradas) se llena rápidamente y el switch comienza **flooding unicast desconocido**.
---
## 📋 Objetivo del Script

Desbordar la tabla CAM del switch con miles de MACs falsas, forzándolo a comportarse como un hub y hacer flooding de frames a todos los puertos, permitiendo la captura del tráfico de toda la red desde un único punto.

### Parámetros del Script

| Parámetro | Descripción | Valor por defecto |
|-----------|-------------|-------------------|
| `-i` / `--interface` | Interfaz de red | Requerido |
| `-c` / `--count` | Número de tramas a enviar | `50000` |
| `--continuous` | Modo continuo hasta Ctrl+C | Desactivado |
| `--threads` | Hilos paralelos (máximo 4) | `1` |
| `--delay` | Delay en microsegundos entre tramas | `0` |
| `--vlan` | ID de VLAN para añadir tag 802.1Q | Sin tag |

### Requisitos para Utilizar la Herramienta

```bash
# Sistema operativo
Kali Linux (Docker en PNetLab)

# Dependencias
apt update && apt install python3-scapy -y

# Privilegios
sudo / root (obligatorio)

# Condiciones de red
- Kali conectada al switch objetivo (misma VLAN)
- Sin Port Security activo en el puerto de Kali
- Capacidad CAM del switch objetivo: ~8192 entradas (IOSvL2)
```

---

## 🌐 Topología del Ataque

```
┌──────────────────────────────────────────────────────────┐
│  Topología: MAC Flooding                                 │
│                                                          │
│  ┌──────────────────────────────────────┐                │
│  │         Switch Cisco IOSvL2          │                │
│  │                                      │                │
│  │  CAM Table: 8192 entradas máx.      │                 │
│  │  [████████████████████] 100% LLENA  │                 │
│  │                                      │                │
│  │  e0/0          e0/1          e0/2   │                 │
│  └────┬────────────┬─────────────┬─────┘                 │
│       │            │              │                      │
│  ┌────┴───┐   ┌────┴───┐   ┌─────┴──┐                    │
│  │  Kali  │   │Víctima │   │Router/ │                    │
│  │ eth2   │   │        │   │ Otros  │                    │
│  │Atacante│   │        │   │ hosts  │                    │
│  └────────┘   └────────┘   └────────┘                    │
│                                                          │
│  ESTADO NORMAL:  Switch aprende MACs → reenvío           │
│                  unicast inteligente                     │
│                                                          │
│  BAJO ATAQUE:    CAM llena → flooding a TODOS            │
│                  los puertos → Kali ve TODO              │
└──────────────────────────────────────────────────────────┘
```

### Tabla de Interfaces y Direccionamiento

| Interfaz / Nodo | Rol |
|-----------------|-----|
| Kali — eth2 | 192.168.10.50/24 — Atacante |
| PC-Víctima | 192.168.10.100/24 |
| Switch — e0/0 | Puerto de acceso hacia Kali |
| Objetivo | Tabla CAM del switch (~8192 entradas) |

---

## 🔍 Funcionamiento del Script

El script `05_mac_flooding.py` explota la capacidad finita de la tabla CAM:

**Generación de tramas:**
```
Crea tramas Ethernet con:
  • MAC origen:  completamente aleatoria (6 bytes aleatorios)
  • MAC destino: completamente aleatoria (6 bytes aleatorios)
  • Tag 802.1Q:  opcional (parámetro --vlan)
  • Payload:     datos aleatorios
```

**Envío masivo optimizado:**
```
• Tramas enviadas en lotes de 100
• Múltiples hilos paralelos (hasta 4 threads)
• Sin delay por defecto → máxima velocidad posible
• Switch intenta aprender cada MAC nueva
```

**Efecto en el switch:**
```
Ciclo de vida de la tabla CAM:
  1. Tabla tiene espacio → aprende MACs nuevas
  2. Tabla llena (8192 entradas) → no puede aprender más
  3. Entradas viejas expiran → se reemplazan por nuevas falsas
  4. MACs legítimas nunca logran mantenerse en la tabla
  5. Switch hace flooding de todo el tráfico unicast desconocido
  6. Kali captura el tráfico de TODA la red
```

---

## 🚀 Ejecución del Ataque

```bash
# Configurar interfaz
ip addr add 192.168.10.50/24 dev eth2
ip link set eth2 up

# Ataque básico — 100,000 tramas
sudo python3 05_mac_flooding.py -i eth2 -c 100000

# Modo continuo con 4 hilos — mayor impacto y sostenido
sudo python3 05_mac_flooding.py -i eth2 --continuous --threads 4

# Con tag VLAN 10 (para topologías con trunk)
sudo python3 05_mac_flooding.py -i eth2 -c 50000 --vlan 10
```

### Verificación del Ataque (en el Switch)

```ios
! Verificar que la tabla CAM está llena
SW# show mac address-table count
! Resultado esperado:
! Dynamic Address Count: 8192  (capacidad máxima alcanzada)

! Ver las MACs aprendidas
SW# show mac address-table dynamic
! Resultado esperado: miles de MACs aleatorias, todas en e0/0

! Ver estado de Port Security
SW# show port-security interface e0/0
```

```bash
# Verificar modo hub — capturar tráfico ajeno en Kali
tcpdump -i eth2 not ether src <MAC-de-Kali>
# Si se ven pings/tráfico entre otros hosts → switch en modo hub ✓
```

---

---

## 🛡️ Contra-medida

### Port Security con MAC Sticky

```ios
! Configurar Port Security con aprendizaje sticky en el puerto del atacante
SW(config)# interface e0/0
SW(config-if)# switchport mode access
SW(config-if)# switchport port-security

! Solo se permiten 2 MACs únicas por puerto
SW(config-if)# switchport port-security maximum 2

! Modo sticky: aprende y fija las MACs actuales como seguras
SW(config-if)# switchport port-security mac-address sticky

! Si se supera el máximo → shutdown del puerto
SW(config-if)# switchport port-security violation shutdown
```

### Verificación de la Contra-medida

```ios
! Ver estado de Port Security
SW# show port-security interface e0/0
! Campos relevantes:
!   Port Security: Enabled
!   Port Status: Secure-up (OK) → err-disabled (bajo ataque)
!   Maximum MAC Addresses: 2
!   Security Violation Count: X  (incrementa con el ataque)

! Repetir el ataque con Port Security activo
! Resultado esperado: puerto pasa a err-disabled inmediatamente

SW# show interface e0/0 status
! Resultado esperado: "err-disabled"

! Para restaurar el puerto (después de verificar)
SW(config)# interface e0/0
SW(config-if)# shutdown
SW(config-if)# no shutdown
```

**Por qué funciona:** Con `maximum 2`, el switch solo acepta 2 MACs únicas por puerto. Al llegar la tercera MAC diferente desde Kali, el puerto es deshabilitado automáticamente (err-disabled), cortando el ataque de raíz.

---

## 📹 Video de Demostración

> **Archivo:** `video/mac_flooding.mp4`  

El video debe incluir:
- ✅ Topología visible con nombre y matrícula del estudiante
- ✅ Hora y fecha visibles en pantalla
- ✅ Cara y voz del presentador
- ✅ Tabla CAM antes y después del flooding
- ✅ tcpdump mostrando tráfico ajeno capturado
- ✅ Demostración de Port Security como contra-medida

---

---
*Laboratorio de Seguridad en Redes · Entorno: PNetLab + Kali Linux Docker + Cisco IOSvL2*
