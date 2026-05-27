# Análisis Funcional Detallado - Bot Parapark

## 🔍 Descripción General del Flujo

Este documento describe el funcionamiento completo del bot, módulo por módulo.

---

## 📦 Módulo 1: `booking_notifier_ts.py` (755 líneas)

### Propósito
Script básico para notificar reservas a clientes y grupo. Versión más simple (TS = Time Series).

### Flujo Principal

```
1. INICIALIZACIÓN
   ├─ Cargar constantes (días a revisar, templates)
   ├─ Inicializar navegador Chrome
   └─ Cargar cookies de sesión anterior

2. SCRAPING DE RESERVAS
   ├─ Acceder a: https://app.turitop.com/admin/company/P271/bookings
   ├─ Filtrar por fecha (hoy ± 4 días)
   ├─ Extraer datos de cada reserva:
   │  ├─ Hora (booking_time)
   │  ├─ Día (booking_day)
   │  ├─ Mes (booking_month)
   │  ├─ Año (booking_year)
   │  ├─ Lugar (booking_place) → P1, P2, P3, P4, P5, P6, P7
   │  ├─ Experiencia (#1)
   │  ├─ Familiares/Niños (#3)
   │  ├─ Estado de pago
   │  ├─ Notas
   │  └─ Link WhatsApp para cliente
   └─ Paginar hasta encontrar todas

3. ENVÍO A CLIENTES (Opcional, si send_messages_to_clients_one_day_before = 1)
   ├─ Para cada reserva:
   │  ├─ Validar que tiene link WhatsApp
   │  ├─ Verificar que no fue enviado antes
   │  ├─ Verificar hora (10:00 - 21:00)
   │  ├─ Acceder a: https://web.whatsapp.com
   │  ├─ Escribir mensaje personalizado:
   │  │  ├─ Reemplazar: {booking_time}
   │  │  ├─ Reemplazar: {goolge_maps_link}
   │  │  ├─ Reemplazar: {name_service} (español)
   │  │  └─ Reemplazar: {name_service_en} (inglés)
   │  ├─ Enviar mensaje
   │  ├─ Adjuntar imagen (maps/p7)
   │  ├─ Enviar imagen
   │  └─ Registrar en sent_messages.txt
   └─ Esperar 15 segundos entre mensajes

4. NOTIFICACIÓN AL GRUPO
   ├─ Cada hora (excepto 23:00-8:00)
   ├─ Comparar con reservas anteriores
   ├─ Detectar:
   │  ├─ *NEW* - Nuevas reservas
   │  └─ *cancel* - Canceladas
   ├─ Enviar mensaje al grupo WhatsApp
   └─ Guardar estado actual

5. FINALIZACIÓN
   └─ Cerrar navegador
```

### Datos Extraídos (Turitop)

```json
{
  "booking_time": "16:00",
  "booking_day": "25",
  "booking_day_name": "Lun",
  "booking_month": "Mar",
  "booking_year": "2026",
  "booking_date": "25 Mar 2026",
  "booking_place": "#P1",
  "experience": "10",
  "family_or_child_text": "Familia",
  "payment_status": "PAGADO",
  "notes": "Aniversario",
  "wa_link": "https://api.whatsapp.com/send/?phone=..."
}
```

### Variables Configurables

| Variable | Default | Significado |
|----------|---------|-------------|
| `days_to_check_for_booking` | 4 | Días a futuro a revisar |
| `send_messages_to_clients_one_day_before` | 0 | Enviar 1 día antes (0=no, 1=sí) |

---

## 📦 Módulo 2: `booking_notifier_keep_browser_opened.py` (1,575 líneas)

### Propósito
Versión mejorada que **mantiene el navegador abierto permanentemente**, añadiendo:
- Módulo de gestión de fotos
- Integración con IA (OpenRouter)
- Respuesta automática a mensajes

### Flujo Principal (Extends Module 1)

```
ADEMÁS de lo anterior:

6. MÓDULO DE FOTOS
   ├─ Acceder al grupo de fotos: https://chat.whatsapp.com/J9kambMiqGYGg4GULS4LiM
   ├─ Descargar fotos recientes
   ├─ PARA CADA FOTO:
   │  ├─ Usar IA (OpenRouter) para identificar:
   │  │  ├─ Sala (4e, csi, maf, tri)
   │  │  └─ Clientes en la foto
   │  ├─ Hacer matching con clientes en Turitop
   │  ├─ Enviar foto a cliente (WhatsApp)
   │  ├─ Dejar mensaje predeterminado:
   │  │  ├─ Inglés: "Here is your escape room photo..."
   │  │  └─ Español: "Aquí tenéis vuestra foto..."
   │  └─ Aguardar respuesta
   └─ Registrar en photo_sent_messages.txt

7. GESTIÓN DE RESPUESTAS
   ├─ Monitorear respuestas de clientes
   ├─ Detectar:
   │  ├─ Respuestas positivas → Enviar template positivo
   │  ├─ Respuestas negativas → Enviar template negativo
   │  └─ Respuestas neutras → Ignore
   ├─ Guardar en pending_replies.json
   └─ Registrar conversación

8. LOOP PERMANENTE
   ├─ Ejecutar cada hora
   ├─ Mantener navegador abierto
   ├─ Actualizar estado de reservas
   └─ Procesar nuevas fotos
```

### Configuración de Fotos

```python
# Mapeo de salas → Lugares Turitop
sala_to_places = {
    '4e': ['P1'],        # 4th Element
    'csi': ['P2'],       # CSI Investigation
    'maf': ['P4'],       # Mafia Italiana
    'tri': ['P5', 'P6']  # Triángulo Bermudas 1 & 2
}
```

### Archivos de Configuración

```
data/
├── photo_group_config.txt
│  ├─ Línea 1: Nombre del grupo
│  └─ Línea 2: URL del grupo
├── openrouter_api_key.txt
│  └─ API key de OpenRouter (🚨 EXPUESTA)
├── pending_replies.json
│  └─ Respuestas pendientes de clientes
└── photo_sent_messages.txt
   └─ Registro de fotos enviadas
```

---

## 📦 Módulo 3: `test_photo_modules.py` (1,046 líneas)

### Propósito
Script de prueba **SOLO** para el módulo de fotos, sin las notificaciones de reservas.

### Flujo

```
1. Inicializar navegador
2. Acceder al grupo de fotos
3. Scrapear fotos
4. Realizar matching con IA
5. Enviar fotos a clientes
6. Esperar respuestas
7. Registrar pendientes
```

### Caso de Uso
- Pruebas del módulo de fotos
- Debug sin afectar el flujo principal
- Validar IA matching antes de producción

---

## 📦 Módulo 4: `change password etc.py` (227 líneas)

### Propósito
Herramienta de **debugging y cambios de credenciales**

### Funcionalidad
```python
wb = Browser()
wb.get("https://app.turitop.com/admin/company/P271/bookings")
breakpoint()  # Pausa para intervención manual
```

### Caso de Uso
- Reautenticar si las cookies expiraron
- Cambiar contraseñas
- Verificar que la plataforma sigue funcionando

---

## 🏗️ Arquitectura de Clases

### Clase: `Browser`

```python
class Browser:
    """Wrapper para Selenium con métodos helper"""

    def __init__(self):
        """Inicializar navegador Chrome"""
        # Descargar chromedriver automáticamente
        # Crear perfil de usuario para mantener sesión
        # Configurar opciones (tamaño, logs)

    def save_cookies(cookie_name):
        """Guardar cookies en archivo pickle"""

    def load_cookies(cookie_name):
        """Cargar cookies desde archivo pickle"""

    # Métodos de Click
    def css_click(element):
        """Click con CSS selector con reintentos"""

    def x_click(element):
        """Click con XPath con reintentos"""

    def js_click(element):
        """Click con JavaScript (elemento oculto, etc)"""

    def obj_click(obj):
        """Click en objeto WebElement"""

    # Métodos de Espera
    def elem_wait(element):
        """Esperar a que elemento aparezca"""

    def text_wait(text):
        """Esperar a que texto aparezca en página"""

    # Métodos de Lectura
    def get_text(element, parent_element=None):
        """Extraer texto con reintentos"""

    def get_attr(element, attr, parent_element=None):
        """Extraer atributo HTML"""

    @staticmethod
    def re_get_text(re_pattern, raw_text):
        """Extraer texto con regex"""

    # Métodos de Escritura
    def send_keys(element, keys, full=False, clear=False):
        """Escribir en campo con Alt+Enter para multi-línea"""

    # Métodos de Navegación
    def get(url):
        """Navegar a URL con reintentos"""

    # Debug
    def show_error(error):
        """Registrar errores si debug=True"""
```

---

## 🔄 Flujos de Datos Detallados

### Flujo 1: Scraping → Cliente

```
Turitop Booking
    ↓
extract_booking_data()
    ↓
Validar link WhatsApp
    ↓
¿Fue enviado antes?
    │
    ├─ Sí → Skip
    └─ No ↓

¿Está en horario (10-21)?
    │
    ├─ No → Skip
    └─ Sí ↓

Cargar template (P7 o estándar)
    ↓
Reemplazar variables
    ├─ {booking_time} → "16:00"
    ├─ {goolge_maps_link} → URL maps
    ├─ {name_service} → "Cuarto Elemento"
    └─ {name_service_en} → "4th Element"
    ↓
Abrir WhatsApp Web
    ↓
Escribir mensaje
    ↓
Enviar
    ↓
Adjuntar imagen
    ↓
Esperar confirmación
    ↓
Registrar en sent_messages.txt
    ↓
Esperar 15s
```

### Flujo 2: Scraping → Grupo

```
Todas las reservas (Turitop)
    ↓
Filtrar por estado = PAGADO
    ↓
Excluir P7 (Parapark Studio)
    ↓
Para cada reserva, crear string:
"Lun 25 Mar###16:00 4e Ex(10) (*familia*) PAGADO (Aniversario)"
    ↓
Comparar con lista anterior
    ↓
Detectar:
├─ *NEW* → Nueva reserva
└─ *cancel* → Cancelada
    ↓
Agrupar por fecha
    ↓
Ordenar por hora
    ↓
Enviar mensaje al grupo
    ↓
Guardar lista actual
```

### Flujo 3: Fotos → Cliente

```
Grupo WhatsApp (fotos)
    ↓
Descargar fotos recientes
    ↓
Para cada foto:
    ├─ Convertir a base64
    ├─ Enviar a OpenRouter API
    │  └─ Prompt: "¿Qué sala es? ¿Quiénes están?"
    ├─ Recibir identificación:
    │  ├─ Sala: "4e" / "csi" / "maf" / "tri"
    │  └─ Clientes: Lista de nombres
    ├─ Buscar en Turitop:
    │  └─ WHERE sala = X AND fecha = HOY
    ├─ Encontrar cliente en reserva
    ├─ Obtener número WhatsApp
    ├─ Enviar foto + mensaje
    │  └─ Template: photo_thank_you_template.txt
    ├─ Guardar en photo_sent_messages.txt
    └─ Aguardar respuesta (pending_replies.json)
```

---

## 📊 Interacciones con Servicios Externos

### 1. **Turitop (Booking Platform)**

```
Endpoint: https://app.turitop.com/admin/company/P271/bookings

Requiere:
- Cookies de sesión (guardadas en archivo)
- Credenciales de login

Datos obtenidos:
- Lista de reservas (HTML scraping)
- Información del cliente
- Estado de pago
- Notas

Métodos:
- GET /bookings → Lista
- GET /bookings/list/page/{N} → Paginación
```

### 2. **WhatsApp Web**

```
Endpoint: https://web.whatsapp.com

Requiere:
- Navegador Chrome
- Cookies de sesión
- Escaneo QR en primer login

Métodos:
- Enviar mensajes privados
- Enviar mensajes a grupos
- Adjuntar imágenes/archivos
- Acceder a grupo con link de invitación
```

### 3. **OpenRouter API (IA)**

```
Endpoint: https://api.openrouter.ai/api/v1/chat/completions

Requiere:
- API Key: sk-or-v1-...

Métodos:
- Vision: Identificar sala en foto
- OCR: Leer nombres en foto
- Descripción: Generar captions

Costo: Por token (especificar en producción)
```

---

## ⏱️ Horarios y Triggers

### Envío a Clientes
```
- Se ejecuta cada vez que se corre el script
- Respeta horario: 10:00 - 21:00
- Se salta si ya fue enviado
- Espera 15 segundos entre mensajes
```

### Notificación a Grupo
```
- Se ejecuta cada hora (si cdo.hour != [23,0,1,2,3,4,5,6,7,8])
- En horario de silencio (8 PM - 9 AM): solo borra cambios del día anterior
- Agrupa por fecha
```

### Módulo de Fotos
```
- Se ejecuta continuamente (si navegador abierto)
- Descarga fotos recientes
- Procesa con IA
- Guarda respuestas pendientes
```

---

## 📋 Mapeo de Lugares

```python
places = {
    "P1": "4e",          # 4th Element
    "P2": "Csi",         # C.S.I Investigation
    "P3": "9p",          # 9 Pistas
    "P4": "Maf",         # Mafia Italiana
    "P5": "Tri1",        # Triángulo Bermudas 1
    "P6": "Tri2"         # Triángulo Bermudas 2
    # P7 no se incluye en notificaciones (Parapark Studio - fotos)
}
```

---

## 🔐 Autenticación y Cookies

### Turitop
```
Método: Cookie-based (mantiene sesión)
Storage: {cookie_name}.pkl (pickle, sin encripción ⚠️)
Reinicio: Si expira, requiere login manual
```

### WhatsApp
```
Método: QR-based en primer acceso
Storage: Perfil Chrome en Desktop/browser_cache
Persistencia: Automática entre ejecuciones
```

---

## 📝 Templates y Configuración

### Templates de Mensajes

**Client Message (General)**
```
Archivo: data/client_message_template.txt
Variables:
  {booking_time} → Hora de reserva
  {goolge_maps_link} → Link de ubicación [sic - typo]
  {name_service} → Nombre en español
  {name_service_en} → Nombre en inglés
```

**Client Message (P7)**
```
Archivo: data/client_message_template p7.txt
(Contenido similar pero para studio de fotos)
```

**Photo Thank You**
```
Archivo: data/photo_thank_you_template.txt
Contenido: Agradecimiento por experiencia
Respuestas esperadas:
  - Positiva → Enviar review template positivo
  - Negativa → Enviar review template negativo
```

---

## 🚀 Ejecución y Mantenimiento

### Flujo Típico de Ejecución

```
1. Usuario ejecuta: python booking_notifier_keep_browser_opened.py
2. Bot inicia navegador Chrome
3. Carga cookies guardadas (login automático)
4. Accede a Turitop
5. Scraping de reservas (próximos 4 días)
6. Envío de confirmaciones a clientes (si aplica)
7. Sincronización con grupo de colegas
8. Inicia loop de monitoreo de fotos
9. Mantiene abierto indefinidamente (o hasta crash)
10. Usuario puede pausar con Ctrl+C
```

### Mantenimiento Manual Requerido

```
✓ Cada 7 días:
  - Revisar que bot sigue corriendo
  - Verificar logs si hay errores

✓ Cada 30 días:
  - Limpiar archivos de datos antiguos
  - Rotar logs

✓ Si cookies expiran:
  - Ejecutar "change password etc.py"
  - Login manual en navegador
  - Bot guardará nuevas cookies

✓ Si Turitop cambia HTML:
  - Actualizar CSS selectors
  - Revisar regex patterns
```

---

## 🎯 Casos de Uso Típicos

### Caso 1: Confirmación Pre-Evento
```
Evento: 25/03/2026 16:00 - 4th Element
Trigger: 24/03/2026 cualquier hora (si configurado)
Acción: Envío de recordatorio + mapa + fotos

Cliente recibe:
"Hola! Tu experiencia es mañana a las 16:00 en Cuarto Elemento
[mapa] [foto]"
```

### Caso 2: Notificación de Nueva Reserva
```
Evento: Nueva reserva en Turitop
Acción: Notificación automática en grupo de colegas

Colegas reciben:
"Lun 25 Mar
*NEW* 16:00 4e Ex(10) (*familia*) PAGADO (Aniversario)"
```

### Caso 3: Envío de Fotos
```
Evento: Fotos subidas al grupo después de evento
Acción: IA identifica sala + clientes → envío individual

Cliente recibe:
[Foto grupal]
"Aquí tenéis vuestra foto! 📸"
+ Template de agradecimiento
```

---

## ⚠️ Puntos Críticos de Falla

1. **Expira cookie Turitop**
   - Síntoma: Error 401 en scraping
   - Solución: Ejecutar "change password etc.py"

2. **WhatsApp cambia HTML**
   - Síntoma: Mensajes no se envían
   - Solución: Actualizar selectors CSS

3. **API OpenRouter alcanza límite**
   - Síntoma: Errores 429 en IA
   - Solución: Revisar API key y límites

4. **Disco lleno (archivos de datos)**
   - Síntoma: Error al escribir logs
   - Solución: Limpiar archivos antiguos

5. **Navegador se crashea**
   - Síntoma: Bot detiene
   - Solución: Reiniciar manualmente

---

**Fin del análisis funcional**
