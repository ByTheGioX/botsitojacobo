# 🚀 Instalación del Bot Parapark (modo robusto)

> Hecho para arreglar el problema de "el bot no corre, solo envía una vez al día".
> Combina **modo continuo** (que funcionó bien hasta el 2 mayo) + **watchdog** (backup que lo resucita si muere).

---

## 📋 Qué vas a configurar

Dos capas de redundancia:

| Capa | Qué hace | Cuándo se activa |
|------|----------|------------------|
| **1. Modo continuo** | Python corre `while True:` con el navegador **siempre abierto** entre 10:00-23:00. Refresca WhatsApp Web entre ciclos (no lo cierra) → la sesión no se desvincula. Ciclo cada 15 min. | Al iniciar Windows |
| **2. Watchdog** | Si el log no se actualiza en 30 min, mata Python+Chrome y relanza el bot. No actúa fuera de horario. | Cada 30 min vía Task Scheduler |

Si solo configuras la capa 1, basta el 95% del tiempo. La capa 2 cubre el caso raro de crash silencioso, cuelgue de Python, o que olvides arrancar el PC.

> ⚠️ **Cambio importante (mayo 2026):** ahora el navegador **NO se cierra** entre ciclos. Esto evita que WhatsApp Web desvincule el dispositivo por reaperturas frecuentes (que era el problema del martes pasado).

---

## 🛠️ Paso 1: Copiar archivos al PC de Turitop

Copia estos archivos NUEVOS a `C:\Users\Turitop\Desktop\bot\`:

- `run_modo_continuo.bat` ✨ nuevo
- `watchdog.bat` ✨ nuevo
- `INSTRUCCIONES_INSTALACION.md` (este archivo, para referencia)

Y **reemplaza** estos dos (les apliqué el fix de cierre limpio del navegador):

- `test_photo_modules.py`
- `booking_notifier_keep_browser_opened.py`

---

## 🛠️ Paso 2: Desactivar la configuración vieja

La tarea programada actual que dispara `run_ciclo_completo.bat` es la que está fallando.
**No la borres aún**, solo desactívala:

1. Pulsa `Win + R`, escribe `taskschd.msc`, Enter.
2. Busca la tarea programada que ejecuta `run_ciclo_completo.bat` (probablemente se llama algo como "Bot Parapark" o similar).
3. Click derecho → **Disable** (Deshabilitar).
4. **No la borres** — la vamos a reemplazar con el watchdog en el Paso 4.

---

## 🛠️ Paso 3: Autoarranque del modo continuo

Esto hace que el bot arranque solo cuando enciendes el PC y se quede corriendo todo el día.

1. Pulsa `Win + R`, escribe `shell:startup`, Enter.
2. Se abre la carpeta `Inicio` de Windows.
3. **Arrastra `run_modo_continuo.bat`** desde `C:\Users\Turitop\Desktop\bot\` a esa carpeta, pero **manteniendo `Alt` pulsado** — esto crea un **acceso directo**, no copia el archivo.
   - Alternativa: click derecho en `run_modo_continuo.bat` → "Crear acceso directo" → mueve el acceso directo a la carpeta `Inicio`.

**Prueba:** reinicia el PC. En unos segundos debería aparecer una ventana negra titulada "BotParaparkContinuo" que abre Chrome con WhatsApp Web.

**Importante:** si WhatsApp pide QR, **escanéalo desde el móvil** la primera vez. Después la sesión se queda guardada en `C:\Users\Turitop\Desktop\browser_cache` y no debería pedirlo otra vez.

---

## 🛠️ Paso 4: Watchdog (backup) en Task Scheduler

Esto resucita el bot si por alguna razón muere y no se reinicia solo.

1. Abre Task Scheduler (`Win + R` → `taskschd.msc`).
2. **Action → Create Basic Task...** (o "Crear tarea básica" en español).
3. **Name:** `Bot Parapark Watchdog`
4. **Trigger:** Daily, hora inicial 09:00, recurrencia cada 1 día.
5. Pulsa siguiente hasta llegar al final, pero **antes de Finish**, marca *"Open the Properties dialog for this task when I click Finish"*.
6. Pulsa Finish. Se abre la ventana de propiedades.
7. Pestaña **Triggers** → selecciona el trigger → **Edit** →
   - Marca **"Repeat task every:"** y elige `30 minutes`
   - **"for a duration of:"** elige `Indefinitely`
   - OK
8. Pestaña **Actions** → selecciona la acción → **Edit** →
   - **Program/script:** `C:\Users\Turitop\Desktop\bot\watchdog.bat`
   - **Start in:** `C:\Users\Turitop\Desktop\bot\`
   - OK
9. Pestaña **Conditions** → desmarca las restrictivas:
   - [ ] Start the task only if the computer is on AC power  ← DESMARCAR
   - [ ] Stop if the computer switches to battery power  ← DESMARCAR
   - [ ] Start only if computer is idle  ← DESMARCAR
   - [x] Wake the computer to run this task  ← MARCAR (para que dispare aunque el PC esté en suspensión)
10. Pestaña **Settings**:
   - ☑ Allow task to be run on demand
   - ☑ If the task fails, restart every: `1 minute`, **3 times**
   - ☑ If the running task does not end when requested, force it to stop
   - **If the task is already running, then the following rule applies:** `Do not start a new instance`
11. OK. Tu contraseña de Windows si te la pide.

**Prueba:** click derecho en la tarea → **Run**. Mira `data/log/` — debería aparecer un log de hoy en pocos segundos si el bot no estaba ya corriendo.

---

## 🔍 Cómo verificar que está funcionando

### Verificación rápida (cualquier momento)
1. Abre `C:\Users\Turitop\Desktop\bot\data\log\`
2. Mira el archivo `YYYY-MM-DD.log` de hoy.
3. **Debe tener una entrada nueva cada 15 minutos.** Algo así:
   ```
   [2026-05-11 22:13:25] POSITIVO | Fotos nuevas: 0 | Envios OK: 0 ...
   [2026-05-11 22:28:31] POSITIVO | Fotos nuevas: 0 | Envios OK: 0 ...
   [2026-05-11 22:43:27] POSITIVO | Fotos nuevas: 0 | Envios OK: 0 ...
   ```

### Si NO ves entradas cada 15 min
- Abre Task Manager y verifica que existe **`python.exe`** corriendo
- Mira si hay una ventana minimizada llamada "BotParaparkContinuo"
- Si nada de eso → el bot murió. El watchdog tardará máximo 30 min en resucitarlo, o haz doble-click manual en `run_modo_continuo.bat`

### Si aparece la pantalla del QR de WhatsApp
- Escanéalo desde el móvil (Configuración → Dispositivos vinculados → Vincular dispositivo).
- Una vez vinculado, déjalo así. La próxima vez que arranque el bot ya no pedirá QR.

---

## 🚨 Bandera de WhatsApp desvinculado

Añadí un detector: cuando el bot ve QR y no consigue conectar, **crea el archivo `data/wa_disconnect.flag`** con la fecha y hora.

**Pequeña costumbre nueva:** una vez al día mira si existe ese archivo. Si existe, alguien tiene que escanear el QR. Si no existe, todo bien.

Para automatizar el aviso en el futuro podríamos hacer que se envíe un mensaje al grupo de fotos cuando aparece la bandera. Pero eso requiere que el bot esté conectado, así que es algo paradójico. La mejor solución sería un cron desde otro sitio (móvil, otro PC, servidor) que verifique el archivo y te mande email/Telegram.

---

## ❓ Resumen ejecutivo

**Antes:**
- Task Scheduler dispara `run_ciclo_completo.bat` *cuando le da la gana*
- 1-7 ciclos al día en lugar de los ~50 que debería haber
- Mensajes se envían en lotes a horas raras (22:17 anoche)
- Respuestas de hoy no procesadas

**Después (con esta configuración):**
- PC enciende → bot arranca solo
- Bot corre con `while 1:` ciclo cada 15 min, todo el día
- Si crashea, se reinicia solo en 30s
- Si muere y no se reinicia, watchdog lo resucita en ≤30 min
- Mensajes y respuestas procesadas con latencia máxima de ~15 min

---

## 🆘 Si algo va mal

Mándame el log del día más reciente (`data/log/YYYY-MM-DD.log`) y la salida de:

```
tasklist | findstr python.exe
tasklist | findstr chrome.exe
```

Con eso veo en qué punto se quedó atascado.
