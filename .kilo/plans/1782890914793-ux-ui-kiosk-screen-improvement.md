# Plan de mejora — UX/UI de la pantalla kiosko (SOPantallasADI)

## Contexto y restricciones

- App kiosko **PyQt6 solo Windows**, pantalla principal = `ui/main_window.py` (834 líneas).
- Sistema de diseño ya existe: `core/design_tokens.py` (tokens) → `core/qss_generator.py` (QSS) → `core/theme_manager.py` (singleton con listeners). El QSS se genera en vivo desde tokens; los temas legacy `.qss` son fallback.
- Restricciones duras (de AGENTS.md) a respetar:
  - **Sin comentarios en el código** salvo funcionalmente necesarios.
  - **UI en español**, identificadores en inglés.
  - No añadir `__init__.py` a `core/`/`ui/`; no tocar el modo kiosko / DirectShow / pycaw.
  - Salvapantallas **fuera de alcance** (marcado como pendiente pero no en este plan).
  - No hay tests/linter/CI: validar manualmente arrancando `python main.py` (como admin) y cambiando de tema en el panel admin.

## Problemas detectados (evidencia en código)

1. **Estilos inline en Python que duplican/se desincronizan del QSS de tokens**:
   - Tarjetas de reunión: `ui/main_window.py:586-663` (headline/subline/hint del empty state + subject/time_label) — todo inline, ignora `MeetingCard` del QSS.
   - Toasts: `ui/widgets/toast_notification.py:128-183` regenera QSS completo por nivel en cada instancia.
   - Bell de notificaciones: `ui/widgets/notification_center.py:220-228` overridea el `#NotificationBell` del QSS global.
   - Tarjeta de calendario vacío (`EmptyState`) no tiene regla QSS propia.
2. **Grid de apps fijo**: `ui/widgets/app_grid.py:182-200` — `max_cols = 5` hardcodeado, tarjetas 110×110 (`AppCard`), sin acomodar márgenes en pantallas estrechas ni evitar recorte en horizontal pequeño.
3. **Feedback táctil limitado**:
   - `AppCard.flash()` (`app_grid.py:92-101`) solo hace un cambio de propiedad QSS de 220ms; sin escala ni ripple.
   - Botón de apagado (`main_window.py:736-749`) lanza `shutdown -s -t 00` sin feedback post-confirmación.
   - `MeetingJoinButton` y `ShareScreenButton` sin estado pressed visible diferenciado (pressed solo usa `opacity` en QSS, que Qt **no anima** — es instantáneo, parece roto).
4. **Inconsistencias de motion**: `ui/animations.py` define `DURATIONS`/`EASING` pero `main_window.py` usa duraciones mágicas (800, 350, 80ms) y `room_status_badge.py` usa `motion_medium_ms*2` sin helper.
5. **Animación de entrada de la ventana** (`main_window.py:319-329`) desinstala el `QGraphicsOpacityEffect` al terminar (`setGraphicsEffect(None)`) — patrón correcto, pero no reutilizable y mezclado con la lógica de layout.
6. **`ToastContainer._relayout`** (`toast_notification.py:247-257`) recalcula posiciones a mano; al cambiar de tema los toasts vivos no se restylean (cada toast cacheó su `_apply_style` en el constructor con los tokens del momento).
7. **Badge de sala**: `room_status_badge.py` construye fuentes con `setPointSizeF(type_sm * 0.75)` — multiplicador mágico repetido en `_on_theme_changed`; el color del dot se setea vía `setStyleSheet` inline en `_apply_state` en vez de por estado QSS (`[state="..."]`).
8. **Reloj**: `clock_widget.py:31` `type_display * 0.75` — otro multiplicador mágico; la fecha usa `type_xl * 0.75`. Idealmente serían tokens propios.

## Decisiones tomadas

- **Migrar estilos inline → tokens/QSS** (no mantener inline lo dinámico): para lo que depende de datos runtime (color por nivel de toast, borde por leído/no leído), usar **variantes por objectName/property** en QSS y setear la property desde Python. Solo se mantiene inline el valor de la *property*, no el bloque QSS.
- **Grid: ajustar 5 columnas** (no responsive real): mantener 110×110 y `max_cols=5`, pero: recalcular columnas si el ancho disponible no cabe 5 (caer a 4/3 sin romper), evitar recorte, y centrar el grid cuando sobra espacio horizontal.
- **Motion centralizado**: usar `ui/animations.py` (`DURATIONS`/`EASING`) en todos los sitios; sustituir literales mágicos por tokens de `motion_*` o helpers.
- **Convenciones estrictas**: sin comentarios nuevos; strings de UI en español; sin `__init__.py` nuevos.

## Tareas (orden de ejecución)

### Fase 1 — Consolidación del sistema de estilos (base para todo lo demás)

1. **Nuevos tokens tipográficos** en `core/design_tokens.py`:
   - Añadir `type_clock` (p. ej. 90) y `type_date` (p. ej. 22) al dataclass `ThemeTokens` y a las 3 instancias (DARK/LIGHT/HIGH_CONTRAST), reemplazando los multiplicadores `* 0.75` de `clock_widget.py:31,45` y el `type_xl * 0.75` de la fecha.
   - Añadir `type_badge_label` (p. ej. 11) para el `RoomStatusBadge`, eliminando `type_sm * 0.75` de `room_status_badge.py:54,75`.
2. **Nuevos objectNames/estados en QSS** (`core/qss_generator.py`):
   - `QLabel#MeetingSubject`, `QLabel#MeetingTime`, `QLabel#MeetingJoinHint`.
   - `QFrame#EmptyState`, `QLabel#EmptyHeadline`, `QLabel#EmptySubline`, `QLabel#EmptyHint`.
   - `QFrame#MeetingCard[ongoing="true"]` con borde-izq de `room_occupied`; `[imminent="true"]` con `room_imminent`; default `meeting`.
   - `QWidget#ToastNotification[level="info|warning|error|success|meeting"]` — fondo por token (`info`/`warning`/`danger`/`success`/`meeting`) y sub-selectores `#ToastTitle/#ToastMessage/#ToastIcon/#ToastCloseButton/#ToastActionButton`.
   - `QPushButton#NotificationBell[unread="true"]` vs default — color `warning` vs `text_muted`.
   - `QFrame#RoomStatusBadge[state="free|imminent|occupied"]` y `QLabel#RoomStatusDot[state="..."]` — dot y label por estado, eliminando `setStyleSheet` inline de `_apply_state`.
3. **Refactor de widgets para usar QSS por estado**:
   - `ui/widgets/toast_notification.py`: eliminar `_apply_style` y el bloque QSS inline; setear solo `self.setProperty("level", <level>)` + `style().unpolish/polish`. Mover tamaños de fuente a tokens (`type_sm`/`type_xs` en QSS, sin `* 0.75`).
   - `ui/widgets/notification_center.py` → `NotificationBell._update_style`: reemplazar `setStyleSheet` por `setProperty("unread", unread>0)` + polish. Card de notificación: usar `#Section[unread="true"]` para el borde-izq en vez de regenerar QSS.
   - `ui/widgets/room_status_badge.py` → `_apply_state`: setear `self.setProperty("state", ...)` y `self._dot.setProperty("state", ...)` + polish; borrar los `setStyleSheet` de dot/label. Mantener la animación de pulso (opacity) intacta.
   - `ui/main_window.py` → `_on_meetings_ready`: eliminar todos los `setStyleSheet` de tarjetas (líneas ~586-663); setear objectNames y, para la tarjeta de reunión en curso, `card.setProperty("ongoing", True)`. El empty state pasa a usar `#EmptyState` y sus labels hijos.

### Fase 2 — Grid de apps: ajuste de 5 columnas sin romper

4. `ui/widgets/app_grid.py` → `_render_apps`:
   - Calcular `max_cols` dinámicamente **acotado a 5**: `min(5, max(1, ancho_disponible // (110 + spacing)))` usando `self.grid_container.width()`; si es 0 (aún no medido), asumir 5 como hasta ahora.
   - `QGridLayout.setAlignment(AlignTop | AlignHCenter)` para centrar cuando hay <5 columnas y sobra ancho.
   - Re-llamar `_render_apps` (o solo `_relayout_grid`) desde un `resizeEvent` del `AppGrid` para recalcular columnas al redimensionar la ventana — mantener las tarjetas, solo reubicar (no reconstruir) para no perder el `flash` en curso.
5. `ui/widgets/app_grid.py` → `AppCard`: mantener 110×110; solo eliminar el `setStyleSheet` inline de `name_label`/`category_label`/fallback de icono si está cubierto por QSS (verificar que `#AppButton` ya pinta texto — si no, añadir sub-labels en QSS).

### Fase 3 — Feedback táctil y motion coherente

6. `ui/widgets/app_grid.py` → `AppCard.flash()`: sustituir el cambio de propiedad por una animación de escala sutil (`scale_in` con bounce o un `QPropertyAnimation` sobre geometry) usando `ui/animations.py`; duración desde `motion_fast_ms`.
7. `ui/main_window.py` y `core/qss_generator.py` → botones de acción:
   - Reemplazar `opacity: 0.85/0.78/0.92` en `:pressed`/`:hover` (Qt no anima `opacity` en QSS — es instantáneo y se ve mal) por `background-color` hacia `accent_pressed`/`accent_hover` ya existentes. Aplicar a `ShutdownButton`, `ShareScreenButton`, `PrimaryButton`, `DangerButton`, `SuccessButton`, `CloseDialogButton`.
   - Añadir `:hover` con borde realzado a los botones que solo tienen `:pressed`.
8. `ui/main_window.py` → `shutdown_pc`: tras `dlg.exec()` confirmativo, mostrar toast de `NotificationLevel.INFO` «Apagando equipo…» antes del `subprocess.Popen`, para feedback inmediato.
9. Centralizar duraciones mágicas: reemplazar `800`/`350`/`80`ms de `main_window.py:324,689,679` y `idx*80`/`idx*60` por `DURATIONS["slow"]`/`["normal"]`/`["fast"]` y `staggered_fade_in` de `ui/animations.py`.

### Fase 4 — Toasts y notificaciones vivos al cambiar tema

10. `ui/widgets/toast_notification.py` → `ToastNotification`: registrar `theme_manager.register_listener(self._on_theme_changed)` que haga `unpolish/polish` (ya no hay QSS inline que regenerar tras la Fase 1, solo repintar). Garantiza que un toast abierto sobrevive a un cambio de tema en el panel admin.
11. `ui/widgets/notification_center.py` → `NotificationCenterDialog`: ya escucha tema implícitamente vía tokens en `refresh`; tras Fase 1 basta con `refresh()` en `_on_theme_changed` si no lo hace ya.

## Archivos afectados

- `core/design_tokens.py` (nuevos campos en dataclass + 3 temas)
- `core/qss_generator.py` (nuevas reglas, corrección `:pressed` opacity)
- `ui/main_window.py` (eliminar estilos inline de tarjetas/empty state; motion centralizado; toast de apagado)
- `ui/widgets/app_grid.py` (columnas dinámicas ≤5, centrado, flash animado)
- `ui/widgets/clock_widget.py` (tokens de fuente nuevos)
- `ui/widgets/room_status_badge.py` (estados por QSS)
- `ui/widgets/toast_notification.py` (QSS por level-property, listener de tema)
- `ui/widgets/notification_center.py` (bell por unread-property, card por unread-property)

## Validación (manual, sin tests)

1. `python main.py` como admin en una sala real (o pantalla 1080p y otra 1366×768).
2. En el panel admin, alternar entre **Oscuro / Claro / Alto Contraste** y verificar:
   - Tarjetas de reunión, empty state, toasts (abrir varios), badge de sala y bell cambian de color **sin reinicio** y sin artefactos.
   - Abrir un toast y, estando visible, cambiar de tema: el toast se repinta al nuevo tema.
3. Grid de apps: con una categoría que tenga ≥6 apps, redimensionar la ventana a lo ancho y confirmar que las columnas caen de 5→4→3 sin recortar tarjetas y quedan centradas.
4. Pulsar una app: el `flash` ahora escala suavemente (no solo cambia color).
5. Pulsar `ShareScreenButton` y `ShutdownButton`: el estado pressed se nota (cambio de fondo, no parpadeo de opacity).
6. Confirmar apagar-equipo muestra toast «Apagando equipo…» antes de apagar (o cancelar el shutdown para probar).
7. `pyinstaller SOPantallas.spec` una vez para confirmar que los assets/tokens empaquetados siguen resolviéndose (no se añaden assets nuevos en este plan).

## Riesgos

- **`QGridLayout` + `resizeEvent`**: reconstruir el grid en cada resize puede causar parpadeo o perder el `flash` en curso. Mitigación: separar `_relayout_grid` (solo `removeWidget`/`addWidget` de tarjetas existentes, sin `deleteLater`) de `_render_apps` (construye tarjetas).
- **`setProperty` + `polish`**: si un widget ya tiene un `QGraphicsEffect` (p. ej. outline en labels), el repolish no lo pierde, pero el orden importa — probar el badge de sala que combina `QGraphicsOpacityEffect` en el dot con estados QSS.
- **Tokens nuevos**: añadir campos al `dataclass(frozen=True)` es seguro (todos se instancian), pero olvidar uno en HIGH_CONTRAST romperá el arranque — validar los 3 temas en el paso 2.
- **`opacity` en QSS `:pressed`**: la eliminación cambia la sensación visual de los botones de acción; confirmar que `accent_pressed` da suficiente contraste en los 3 temas (especialmente Alto Contraste, donde `accent_pressed=#CCAA00` sobre fondo negro sigue OK).

## Fuera de alcance (explícito)

- Salvapantallas (reimplementación pendiente).
- Responsive real del grid (orientación vertical, tarjetas escalables).
- Nuevas funcionalidades (reservar sala en caliente, QR, multi-idioma).
- Refactors de `core/` no listados, tests, linter, typecheck.
- Cambios en modo kiosko, HDMI, calendario/MSAL, watchdog, auditoría.
