# SOPantallasADI — Sistema de Kiosco para Salas de Reuniones

Aplicación de interfaz táctil (kiosko) para pantallas de salas de reuniones corporativas. Lanzador de aplicaciones, calendario Microsoft 365, screensaver premium, notificaciones y panel de administración.

![Python](https://img.shields.io/badge/Python-3.8+-blue) ![PyQt6](https://img.shields.io/badge/PyQt6-6.11-green) ![Windows](https://img.shields.io/badge/Platform-Windows-lightgrey)

---

## 📑 Tabla de contenidos

1. [Características principales](#-características-principales)
2. [Stack tecnológico](#-stack-tecnológico)
3. [Requisitos previos](#-requisitos-previos)
4. [Instalación y configuración](#-instalación-y-configuración)
5. [Uso de la aplicación](#-uso-de-la-aplicación)
6. [Flujos principales](#-flujos-principales)
7. [Panel de administración](#-panel-de-administración)
8. [Estructura del proyecto](#-estructura-del-proyecto)
9. [Seguridad](#-seguridad)
10. [Build / Distribución](#-build--distribución)
11. [Solución de problemas](#-solución-de-problemas)

---

## 🚀 Características principales

### Modo kiosco
- **Bloqueo de teclas nativo Windows API** (`WH_KEYBOARD_LL`) — sin librerías externas
- Bloquea: `Win`, `Alt+Tab`, `Ctrl+Esc`, `Alt+F4`, `Shift+F10`, `F11`
- Funciona en hilo dedicado (no bloquea la UI)
- Watchdog con auto-reinicio ante cuelgues (heartbeat cada 30s)
- Captura global de excepciones con reinicio automático

### Lanzador de aplicaciones
- Grid adaptativo (2/3/4 columnas según cantidad)
- Extracción automática de iconos desde ejecutables
- Detección de procesos ya en ejecución (no duplica)
- Trae la app al frente si ya está abierta
- Filtro por categorías (Comunicación, Productividad, etc.)
- Botón "Aplicaciones Abiertas" con diálogo de gestión
- "Finalizar Reunión" cierra todos los procesos lanzados

### Compartir pantalla (HDMI Input)
- Card "Compartir pantalla" en el grid de apps (cuando está habilitada)
- Captura en vivo del puerto HDMI de entrada de la pantalla interactiva
- **OpenCV + DirectShow** con timeouts por operación (no se cuelga con drivers rotos)
- **Ventana flotante** arrastrable, redimensionable, con botón X cerrar
- Doble click en la barra superior → toggle fullscreen
- Estado visible: 🟢 Señal activa / 🟡 Sin señal / 🔴 Error
- Resolución configurable: 1920×1080, 1280×720, 640×480
- FPS configurable: 15, 30, 60
- Sesiones registradas en auditoría (`HDMI_SESSION_START` / `_END` con duración)

### Integración Microsoft 365 / Outlook
- **Microsoft Graph API** con MSAL
- Dos modos de autenticación:
  - **Client Secret** (recomendado para salas) — acceso app-only
  - **Device Flow** (público) — login interactivo del usuario
- Cache de tokens persistente (`token_cache.bin`)
- Calendario de la sala o del usuario autenticado
- Parseo correcto de timezones con `zoneinfo`

### Notificaciones
- **Toasts animados** (5 niveles: info, warning, error, success, meeting)
- **Historial interno** persistente en JSON
- **Sonidos configurables** (WAV/MP3) con `winsound` + `QtMultimedia` fallback

### Alertas de reuniones
- Aviso **5 minutos antes** de cada reunión de Teams
- Aviso cuando **comienza** una reunión
- Acción directa "Unirse" desde la notificación

### Screensaver premium
- Activación por inactividad (5 min por defecto, configurable)
- **Quotes corporativas** rotativas (24 disponibles, editables vía `assets/quotes.json`)
- **Fondo de video MP4** opcional con loop infinito (fallback a gradiente animado)
- **Partículas flotantes** con render custom
- **Eventos del día** (Navidad, Año Nuevo, etc.) editables en `assets/events.json`
- Reloj y fecha en grande
- Pulso en "Toca la pantalla para continuar"

### Temas visuales
- **3 temas**: Oscuro, Claro, Alto Contraste
- Cambio en vivo desde el panel admin
- Selector visual con preview de colores
- Persistencia en `config.json` y variable de entorno

### Sistema de auditoría
- **SQLite** (`sopantallas_audit.db`) con 4 tablas:
  - Lanzamientos de apps
  - Eventos de reuniones
  - Sesión (start, end, screensaver, kiosk_exit)
  - Notificaciones
- **Dashboard** con KPIs (5 tarjetas) y tablas de uso
- **Exportación CSV** con reporte completo
- Limpieza automática de datos antiguos (90 días por defecto)

### Logging centralizado
- **Rotativo** (`logs/sopantallas.log`, 5MB × 5 backups)
- Salida dual: archivo + consola
- Formato con timestamp, nivel, módulo

### Cache offline
- Reuniones cacheadas en `cache/meetings_cache.json` (válido 6h)
- Si falla Graph API → sirve cache automáticamente

---

## 🛠️ Stack tecnológico

| Categoría | Tecnología |
|-----------|-----------|
| **Lenguaje** | Python 3.8+ |
| **GUI** | PyQt6 6.11 |
| **API Microsoft** | msal 1.36, requests 2.33 |
| **Audio** | winsound, QtMultimedia |
| **Procesos** | psutil 7.2 |
| **Auth kiosco** | Windows API nativo (ctypes) |
| **Persistencia** | SQLite 3, JSON |
| **Config** | python-dotenv |
| **Captura video** | opencv-python 4.10 (DirectShow) |
| **Build** | PyInstaller 6.20 |

---

## 📋 Requisitos previos

- **SO**: Windows 10/11
- **Python**: 3.8 o superior
- **Permisos de Administrador** (necesarios para el bloqueo de teclas nativo)
- **App en Microsoft Entra ID** (solo si quieres calendario M365)
  - Permisos: `Calendars.Read`, `Calendars.Read.Shared` (modo usuario) o `.default` (modo app)

---

## ⚙️ Instalación y configuración

### 1. Clonar e instalar dependencias

```bash
git clone https://github.com/JuanitoJJ/SOPantallasADI.git
cd SOPantallasADI
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env` con tus datos:

```ini
# Contraseña del panel admin
ADMIN_PASSWORD=tu_password_seguro

# Azure AD (Microsoft Entra ID)
CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
TENANT_ID=common  # o tu tenant ID

# Opcional: para modo "app-only" (recomendado para salas)
CLIENT_SECRET=tu_client_secret

# Opcional: email del buzón de sala
ROOM_EMAIL=sala.reuniones@tuempresa.com

# Opcional: tema (dark/light/high_contrast)
THEME=dark
```

> **Nota**: Cualquier variable de `.env` tiene prioridad sobre `config.json`.

### 3. Ejecutar

```bash
python main.py
```

> ⚠️ Ejecutar como **Administrador** para que el bloqueo de teclas funcione.

---

## 🎯 Uso de la aplicación

### Pantalla principal

La pantalla principal muestra:
- **Izquierda**: nombre corporativo, reloj grande, fecha, grid de apps, controles
- **Derecha**: reuniones de hoy (si calendario está habilitado)
- **Esquina inferior derecha**: botón "Admin"

### Acciones del usuario

| Acción | Resultado |
|--------|-----------|
| Tocar una app | La lanza o la trae al frente |
| Botón "Aplicaciones Abiertas" | Diálogo con apps en ejecución |
| Botón "Finalizar Reunión" | Cierra todas las apps lanzadas (con confirmación) |
| Tocar notificación "Unirse" | Abre la URL de Teams en navegador |
| Sin tocar 5 min | Activa screensaver |
| Tocar screensaver | Vuelve a la app |

### Diálogo de admin (PIN)

Botón "Admin" → pide PIN → si OK, abre panel de configuración.

---

## 🔄 Flujos principales

### Flujo de inicio

```
python main.py
   └─► QApplication
       ├─► Carga tema desde config (dark/light/high_contrast)
       ├─► Inicia CrashHandler (captura excepciones no manejadas)
       ├─► Inicia Watchdog (heartbeat cada 30s)
       ├─► Inicia KioskManager (bloqueo de teclas en hilo)
       ├─► ConfigManager() — carga config.json + .env
       ├─► Si calendar_enabled: CalendarManager (MSAL)
       ├─► MainWindow — construye UI
       ├─► QTimer 1s — actualiza reloj
       ├─► QTimer 60s — refresca calendario
       ├─► QTimer 60s — detecta reuniones próximas (alertas)
       └─► InactivityManager — screensaver tras 5 min
```

### Flujo de lanzamiento de app

```
Click en AppButton
   └─► AppGrid._launch(app, card)
       ├─► card.flash() — feedback visual (220ms)
       └─► core.app_launcher.launch_application(app_info)
           ├─► ¿Ya está corriendo? → bring_app_to_front()
           └─► Si no → subprocess.Popen() + guarda en _launched_processes
               └─► core.audit.log_app_launched() — registra en SQLite
```

### Flujo de alerta de reunión

```
QTimer 60s en MainWindow
   └─► check_meeting_alerts()
       └─► MeetingAlertWorker (QThread)
           └─► calendar_manager.get_upcoming_alerts(minutes=5)
               └─► Microsoft Graph /me/calendarView
                   └─► Por cada reunión próxima:
                       ├─► notification_manager.notify(level=MEETING, ...)
                       │   └─► ToastContainer muestra toast animado
                       │   └─► Sonido (si habilitado)
                       └─► audit.log_meeting_alert()
```

### Flujo de screensaver

```
InactivityManager (timer 5 min sin eventos)
   └─► ScreensaverOverlay.show_animated()
       ├─► Fade-in 700ms
       ├─► Video background (loop) o gradiente animado
       ├─► Partículas overlay (50 partículas)
       ├─► Reloj + fecha (actualización cada 1s)
       ├─► Quote (rotación cada 12s)
       └─► Si hay evento del día → banner animado
       │
       └─► Cualquier touch/key/mouse
           └─► Fade-out 350ms
               └─► inactivity.reset() (reinicia timer)
```

### Flujo de tema

```
Admin → Apariencia → Combo "Tema" o "Vista Previa..."
   └─► theme_manager.set_theme(theme_id)
       └─► theme_manager.load_stylesheet(theme_id)
           └─► QApplication.setStyleSheet(qss)
               └─► Afecta a toda la app en vivo
       └─► Click "Guardar Apariencia"
           └─► config_manager.set_theme(theme_id)
               └─► Persiste en config.json
```

### Flujo de auditoría

```
Eventos en la app
   └─► core.audit.log_*(...)
       └─► core.database.log_*(...)
           └─► SQLite INSERT (con timestamp)

Admin → Auditoría → Combo "Período" (1/7/30/90 días)
   └─► UsageDashboardWidget.refresh()
       ├─► 5 StatCard (KPIs)
       ├─► Tabla "Uso de Aplicaciones" (con errores en rojo)
       └─► Tabla "Historial Reciente" (50 eventos, color por acción)

Click "Exportar CSV"
   └─► audit.export_csv(path, days=30)
       └─► Genera reporte con secciones:
           - Resumen general
           - Uso de aplicaciones
           - Estadísticas de reuniones
           - Historial de lanzamientos
           - Historial de reuniones
           - Eventos de sesión
           - Notificaciones
```

### Flujo de "Compartir pantalla" (HDMI)

```
[ Pantalla principal ]
   └─► Tocar card "Compartir pantalla" (al final del grid)
       └─► MainWindow._open_hdmi_viewer()
           ├─► Verifica is_hdmi_enabled() y dispositivo configurado
           └─► HDMIViewerWindow(device_index, w, h, fps)
               ├─► HDMICaptureManager.instance().start()
               │   ├─► _open_capture() con timeout 3s
               │   │   └─► Si falla → emit STATE_ERROR (no se cuelga)
               │   └─► _reader_loop() en thread daemon
               │       ├─► cap.read() con timeout por frame
               │       ├─► Detecta "sin señal" (>2s sin frames)
               │       └─► Emite frame_ready(QImage) al hilo UI
               ├─► QLabel scaledContents muestra pixmaps
               ├─► Footer: 🟢/🟡/🔴 estado en vivo
               └─► Usuario puede arrastrar/redimensionar/duplicar click
                   (doble click en barra → toggle fullscreen)

Click X (o "Finalizar Reunión")
   └─► HDMIViewerWindow.closeEvent()
       ├─► audit.log_hdmi_session_end(duration)
       ├─► Manager.stop() → join(2s timeout) → cap.release()
       └─► Vuelve a MainWindow
```

---

## 🔐 Panel de administración

5 pestañas accesibles solo con PIN:

### 1. 📦 Aplicaciones
- Lista de apps con reordenar (▲/▼) y eliminar
- Formulario para añadir: nombre, ruta EXE, examinar
- Icono extraído automáticamente del ejecutable

### 2. 📅 Calendario
- Habilitar/deshabilitar calendario
- Client ID, Client Secret, Tenant ID, Email de sala
- Vincular cuenta Microsoft (Device Flow)
- Estado de la cuenta (vinculado/expirado/error)
- Desvincular cuenta

### 3. 🎨 Apariencia
- **Vista previa en vivo** de la pantalla principal
- Selector de tema visual con preview
- Galería de wallpapers (añadir/eliminar/seleccionar)
- Configuración de carpeta e intervalo del carrusel

### 4. ⚙ General
- Nombre corporativo
- Timeout de inactividad
- Minutos de alerta antes de reunión
- Sonido de notificaciones (activar / ruta personalizada)

### 5. 📊 Auditoría
- Selector de período (1/7/30/90 días)
- 5 KPIs: lanzamientos, reuniones, alertas, joins, notificaciones
- Tabla de uso de aplicaciones
- Tabla de historial reciente (50 eventos)
- **Exportar CSV** con reporte completo
- Limpieza de datos antiguos

### 6. 🖥️ Pantalla Externa
- Switch para habilitar la card "Compartir pantalla" en la app
- Combo con dispositivos de captura DirectShow detectados
- Selector de resolución (1920×1080, 1280×720, 640×480)
- Selector de FPS (15, 30, 60)
- Botón "Probar 5 segundos" que abre el viewer temporalmente
- Label de estado con conteo de dispositivos

---

## 📁 Estructura del proyecto

```
SOPantallasADI/
├── main.py                          # Entry point
├── requirements.txt                 # Dependencias
├── README.md
├── AGENTS.md
├── .env / .env.example              # Variables sensibles
├── config.json                      # Config runtime
├── .gitignore
│
├── core/                            # Lógica de negocio
│   ├── path_utils.py                # Soporte PyInstaller
│   ├── config_manager.py            # config.json + .env
│   ├── logger.py                    # Logging rotativo
│   ├── system_hooks.py              # Kiosk Windows API
│   ├── watchdog.py                  # Auto-reinicio
│   ├── database.py                  # SQLite (auditoría)
│   ├── audit.py                     # Capa de auditoría
│   ├── calendar_manager.py          # Microsoft Graph
│   ├── calendar_cache.py            # Cache offline
│   ├── notification_manager.py      # Notificaciones + historial
│   ├── sound_player.py              # Sonidos
│   ├── theme_manager.py             # Temas visuales
│   ├── app_launcher.py              # Lanzar/cerrar apps
│   ├── app_categories.py            # Categorías de apps
│   ├── volume_manager.py            # Audio Windows
│   ├── hdmi_capture.py              # Captura HDMI (OpenCV + DirectShow)
│   └── icon_utils.py                # Extraer iconos de .exe
│
├── ui/                              # Interfaz
│   ├── main_window.py               # Pantalla principal
│   ├── admin_panel.py               # Panel admin (6 tabs)
│   ├── running_apps_dialog.py       # Apps abiertas
│   ├── touch_dialogs.py             # Diálogos táctiles
│   ├── screensaver.py               # Screensaver premium
│   ├── screensaver_quotes.py        # Manager de quotes
│   ├── screensaver_events.py        # Manager de eventos
│   ├── screensaver_particles.py     # Partículas
│   ├── screensaver_video.py         # Fondo video
│   ├── hdmi_viewer_window.py        # Ventana flotante HDMI
│   ├── theme_selector.py            # Selector de tema
│   ├── animations.py                # Helpers de animación
│   ├── admin_widgets/               # Widgets del admin
│   │   ├── admin_preview.py
│   │   ├── wallpaper_gallery.py
│   │   └── usage_dashboard.py
│   ├── widgets/                     # Widgets principales
│   │   ├── clock_widget.py
│   │   ├── volume_control.py
│   │   ├── app_grid.py
│   │   ├── toast_notification.py
│   │   ├── notification_center.py
│   │   └── hdmi_input.py            # Card "Compartir pantalla"
│   └── styles/themes/               # Temas QSS
│       ├── dark.qss
│       ├── light.qss
│       └── high_contrast.qss
│
└── assets/                          # Recursos
    ├── icons/                       # Iconos de apps
    ├── wallpapers/                  # Fondos del carrusel
    ├── quotes.json                  # Quotes corporativas
    └── events.json                  # Eventos/aniversarios
```

---

## 🔒 Seguridad

- **Variables sensibles en `.env`** (nunca en `config.json` plano)
- **`.gitignore` configurado** para evitar fugas (`.env`, `token_cache.bin`, `*.db`)
- **Bloqueo nativo** de teclas del sistema (no usa librerías sospechosas)
- **PIN admin** almacenado con prioridad a variable de entorno
- **MSAL** maneja tokens con caché encriptado
- **Watchdog** previene estados inseguros (auto-reinicio)
- **SQLite local** (no expone datos en red)

> ⚠️ **NUNCA** subas `.env`, `token_cache.bin`, `sopantallas_audit.db` o `config.json` a repositorios públicos.

---

## 📦 Build / Distribución

### Crear ejecutable con PyInstaller

```bash
pyinstaller --noconfirm --windowed --name SOPantallas --icon assets/icons/chrome.png ^
  --add-data "ui/styles;ui/styles" ^
  --add-data "assets;assets" ^
  --collect-submodules PyQt6 ^
  main.py
```

El ejecutable queda en `dist/SOPantallas/SOPantallas.exe`.

Para crear `SOPantallas.spec` con configuración persistente:

```python
# SOPantallas.spec
a = Analysis(['main.py'],
             datas=[('ui/styles', 'ui/styles'), ('assets', 'assets')],
             hiddenimports=[],
             )
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [])
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, name='SOPantallas')
```

```bash
pyinstaller SOPantallas.spec
```

---

## 🔧 Solución de problemas

### El bloqueo de teclas no funciona
- **Causa**: Falta de permisos de administrador
- **Solución**: Ejecutar como Administrador

### No se muestra el calendario
- Verificar `calendar_enabled: true` en `config.json`
- Comprobar `CLIENT_ID` y `TENANT_ID` en `.env`
- Re-vincular cuenta desde Admin → Calendario

### Token expirado
- Aparece aviso "Sesión caducada"
- Solución: Admin → Calendario → "Iniciar Vinculación" (Device Flow)

### La app crashea al iniciar
- Revisar `logs/sopantallas.log` para detalles
- Verificar que el tema en config existe (dark/light/high_contrast)
- Limpiar `config.json` y volver a configurar

### Wallpapers no rotan
- Verificar que la carpeta existe y tiene imágenes
- Formatos soportados: `.png .jpg .jpeg .bmp .webp`
- Comprobar `wallpaper_folder` y `wallpaper_interval_seconds` en config

### Volver a Windows desde el admin
- Admin → botón rojo "Cerrar Kiosco y Volver a Windows"
- Acción registrada en `audit.log_kiosk_exit()`

---

## 📜 Licencia

Proyecto interno para la gestión de salas de reuniones corporativas.

---

**Desarrollado para la gestión eficiente de entornos colaborativos.**

---

## 📎 Anexo: Configuración HDMI

`config.json` (creado al guardar desde Admin → Pantalla Externa):

```json
{
  "hdmi_input": {
    "enabled": true,
    "device_index": 0,
    "width": 1920,
    "height": 1080,
    "fps": 30
  }
}
```

**Verificación en la sala**:
1. Conecta el cable HDMI al puerto de entrada de la pantalla
2. En Windows, abre **Administrador de dispositivos** → busca en "Cámaras" o "Dispositivos de captura"
3. Si aparece, el sistema lo detectará al pulsar "Refrescar" en Admin → Pantalla Externa
4. Si no aparece, necesitas una **tarjeta capturadora HDMI-USB externa** (ej: AVerMedia, Elgato)

**Solución de problemas**:

| Problema | Causa | Solución |
|----------|-------|----------|
| Card "Compartir pantalla" no aparece | `hdmi_input.enabled = false` en config | Admin → Pantalla Externa → marcar checkbox |
| "No se detectaron dispositivos" | Driver no instalado o pantalla no expone HDMI-in como captura | Verificar en Admin. de dispositivos de Windows |
| Viewer se abre pero muestra "Sin señal" | Cable HDMI no conectado o portátil no enviando señal | Conectar portátil y verificar salida de video |
| Viewer se cierra solo al cabo de un rato | Driver de captura inestable | Probar otra resolución/FPS o cambiar capturadora |
