# AGENTS.md — SOPantallasADI

SOPantallasADI es una **app kiosko PyQt6 solo para Windows** para salas de reuniones (calendario M365, lanzador de apps, captura HDMI, salvapantallas, panel admin). Python 3.8+, entrypoint único `main.py`.

## Restricciones duras (verificar antes de sugerir cambios)

- **Solo Windows.** `core/system_hooks.py` usa `WH_KEYBOARD_LL` vía ctypes; `core/volume_manager.py` usa `pycaw`; `core/hdmi_capture.py` usa DirectShow. Nada de esto funciona en Linux/macOS.
- **Debe ejecutarse como Administrador.** El bloqueo nativo de teclas (Win/Alt+Tab/Ctrl+Esc/Alt+F4/F11) degrada silenciosamente a un warning logueado si no hay admin — la app igualmente arranca. Ver `main.py:48-52`.
- **`.env` tiene prioridad sobre `config.json`.** Cualquier variable de entorno gana sobre el fichero. Ambos los lee `core/config_manager.py`.
- **Los `path` de apps en `config.json` pueden contener variables de entorno de Windows** (p. ej. `%LocalAppData%`). La expansión ocurre al arrancar — no hardcodear rutas absolutas al editar.
- **`core/` y `ui/` son namespace packages** **sin `__init__.py`** (verificado: los imports en `main.py` y en todo el código usan `from core.X import …`). No añadir `__init__.py` a la ligera — cambia el comportamiento de imports.

## Comandos

```bash
# Ejecutar (dev)
python main.py                    # debe estar elevado en Windows

# Build (usar el spec commiteado, NO el comando inline de pyinstaller del README.md)
pyinstaller SOPantallas.spec      # salida: dist/SOPantallas/SOPantallas.exe

# Instalar dependencias
pip install -r requirements.txt
```

En este repo **no hay test suite, ni linter, ni typecheck, ni CI**. No invocar `pytest`/`ruff`/`mypy` — no están configurados y no funcionarán.

## Ficheros runtime (todos en .gitignore — se crean al primer arranque)

- `sopantallas_audit.db` — auditoría SQLite (`core/database.py` inicializa el schema)
- `token_cache.bin` — caché de tokens MSAL (se regenera al re-autenticar)
- `logs/sopantallas.log` — rotativo, 5MB × 5 (`core/logger.py`)
- `cache/meetings_cache.json` — caché offline de reuniones (6h)
- `notification_history.json` — historial de toasts
- `.watchdog_alive` — sentinel de heartbeat (`core/watchdog.py`)
- `.env`, `config.json` — creados desde defaults / `.env.example` (este último no está commiteado — copiar a mano)

> **No commitear nunca** `.env`, `config.json`, `token_cache.bin`, `*.db`, `logs/`, `cache/`. El `config.json` y `.env` commiteados que ves en el working tree son artefactos de dev local y deben borrarse antes de cualquier push público (ver también el aviso en `README.md:477`).

## Mapa de arquitectura (dónde mirar primero)

| Concern | Fichero |
|---|---|
| Secuencia de boot / wiring | `main.py` |
| Capa de config (json + env) | `core/config_manager.py` |
| Rutas de recursos PyInstaller-aware | `core/path_utils.py` |
| Bloqueo de teclas (modo kiosko) | `core/system_hooks.py` |
| Auto-reinicio + heartbeat | `core/watchdog.py`, `core/logger.py` |
| Schema SQLite + auditoría | `core/database.py`, `core/audit.py` |
| MSAL / Graph | `core/calendar_manager.py`, `core/calendar_cache.py` |
| Captura HDMI (OpenCV/DirectShow) | `core/hdmi_capture.py`, `ui/hdmi_viewer_window.py` |
| Tokens de diseño (color/tipo/spacing/radios) | `core/design_tokens.py` |
| Generación de QSS desde tokens | `core/qss_generator.py` |
| Tema/QSS | `core/theme_manager.py`, `ui/styles/themes/*.qss` *(legacy fallback)* |
| Salvapantallas | *(eliminado en 2.0; commit 2127202 — pendiente de reimplementar)* |
| Panel admin (6 pestañas) | `ui/admin_panel.py` + `ui/admin_widgets/` |
| Badge de estado de sala (signature) | `ui/widgets/room_status_badge.py` |

## Notas de estilo / flujo de trabajo

- **Sin comentarios en el código** salvo que sean funcionalmente necesarios (convención del proyecto — ver la regla de AGENTS arriba).
- Strings de UI en español (`"Sala de reuniones"`, etc.) y README en español — mantener la UI en español, mantener los identificadores de código en inglés.
- Los temas QSS se cargan en vivo desde disco y se aplican vía `QApplication.setStyleSheet`; cambiar de tema no requiere reinicio.
- Al cambiar assets empaquetados (iconos, wallpapers, quotes, events, QSS), recuerda que el spec empaqueta `ui/styles` y `assets` vía `--add-data` — rebuilderar con `pyinstaller SOPantallas.spec` para distribuir los cambios.


