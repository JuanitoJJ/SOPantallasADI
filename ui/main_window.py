import os
import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QGridLayout,
                             QPushButton, QLabel, QFrame, QSpacerItem, QSizePolicy,
                             QSlider, QHBoxLayout, QMessageBox, QGraphicsOpacityEffect,
                             QGraphicsDropShadowEffect)

from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QUrl, QThread, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QColor, QImage
from core.config_manager import ConfigManager
from core.app_launcher import launch_application, close_all_launched_apps
from core.volume_manager import set_system_volume, get_current_volume
from core.logger import get_logger
from core.notification_manager import notification_manager, NotificationLevel
from core.theme_manager import theme_manager
from core import audit
from ui.admin_panel import AdminPanelDialog
from ui.touch_dialogs import TouchConfirmDialog, TouchAdminLoginDialog
from ui.widgets import apply_text_outline
from ui.widgets.clock_widget import ClockWidget
from ui.widgets.room_status_badge import RoomStatusBadge
from ui.widgets.volume_control import VolumeControl
from ui.widgets.app_grid import AppGrid
from ui.widgets.toast_notification import ToastContainer
from ui.widgets.notification_center import NotificationBell
from ui.hdmi_viewer_window import HDMIViewerWindow
from core.calendar_manager import CalendarManager
from core.path_utils import get_resource_path
from datetime import datetime, timezone


logger = get_logger("ui.main_window")


class CalendarFetchWorker(QThread):
    """Worker que obtiene las reuniones del calendario en un hilo de fondo."""
    meetings_ready = pyqtSignal(list, str)

    def __init__(self, calendar_manager):
        super().__init__()
        self.calendar_manager = calendar_manager

    def run(self):
        meetings, status = self.calendar_manager.get_upcoming_meetings()
        self.meetings_ready.emit(meetings, status)


class MeetingAlertWorker(QThread):
    """Worker que detecta reuniones próximas para alertar."""
    meeting_alert = pyqtSignal(dict)
    meeting_started = pyqtSignal(dict)

    def __init__(self, calendar_manager, alert_minutes: int = 5):
        super().__init__()
        self.calendar_manager = calendar_manager
        self.alert_minutes = alert_minutes
        self._stopped = False

    def stop(self):
        self._stopped = True

    def run(self):
        if self._stopped:
            return
        try:
            alerts = self.calendar_manager.get_upcoming_alerts(self.alert_minutes)
            for alert in alerts:
                if not self._stopped:
                    self.meeting_alert.emit(alert)
            ongoing = self.calendar_manager.get_ongoing_meetings()
            for mtg in ongoing:
                if not self._stopped:
                    self.meeting_started.emit(mtg)
        except Exception as exc:
            logger.warning("Error en worker de alertas: %s", exc)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.tokens = theme_manager.current_tokens()

        self.calendar_manager = None
        if self.config_manager.config.get("calendar_enabled"):
            client_id = self.config_manager.get_client_id()
            tenant_id = self.config_manager.get_tenant_id()
            room_email = self.config_manager.get_room_email()
            client_secret = self.config_manager.get_client_secret()
            if client_id:
                self.calendar_manager = CalendarManager(client_id, tenant_id, room_email, client_secret)

        self._alerted_meetings: set = set()
        self._ongoing_announced: set = set()
        self._hdmi_viewer: HDMIViewerWindow = None
        self.cal_title = None

        self.init_ui()

        self.toast_container = ToastContainer(self)
        self.toast_container.setGeometry(0, 0, self.width(), self.height())

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)

        if self.calendar_manager:
            self.cal_timer = QTimer(self)
            self.cal_timer.timeout.connect(self.update_calendar)
            self.cal_timer.start(1 * 60 * 1000)
            self.update_calendar()

            alert_settings = self.config_manager.get_notification_settings()
            self.alert_timer = QTimer(self)
            self.alert_timer.timeout.connect(self.check_meeting_alerts)
            self.alert_timer.start(60 * 1000)
            self.check_meeting_alerts()

        corporate_name = self.config_manager.config.get("corporate_name", "SISTEMA CORPORATIVO")

        self.wallpaper_index = 0
        self.wallpaper_timer = QTimer(self)
        self.wallpaper_timer.timeout.connect(self.next_wallpaper)
        self.setup_wallpaper_carousel()

        notification_manager.add_listener(self._on_new_notification)

        # Log de inicio de sesión
        audit.log_session_start(
            f"corporate_name={corporate_name}, theme={self.config_manager.get_theme()}"
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'toast_container'):
            self.toast_container.setGeometry(0, 0, self.width(), self.height())
            self.toast_container._relayout()

    def _on_new_notification(self, notification):
        if notification is not None:
            audit.log_notification(
                notification.level,
                notification.title,
                notification.message,
            )

    def check_meeting_alerts(self):
        if not self.calendar_manager:
            return
        if hasattr(self, '_alert_worker') and self._alert_worker.isRunning():
            return
        alert_settings = self.config_manager.get_notification_settings()
        minutes = alert_settings.get("alert_minutes_before", 5)
        self._alert_worker = MeetingAlertWorker(self.calendar_manager, minutes)
        self._alert_worker.meeting_alert.connect(self._on_meeting_alert)
        self._alert_worker.meeting_started.connect(self._on_meeting_started)
        self._alert_worker.start()

    def _on_meeting_alert(self, alert: dict):
        mtg_id = alert.get("id", "")
        if mtg_id in self._alerted_meetings:
            return
        self._alerted_meetings.add(mtg_id)
        subject = alert.get("subject", "Sin título")
        minutes = alert.get("minutes_until", 0)
        join_url = alert.get("join_url", "")
        time_str = alert.get("start_dt").strftime("%H:%M") if alert.get("start_dt") else ""
        message = f"Comienza a las {time_str} ({minutes} min)"
        action_cb = None
        action_label = ""
        if join_url:
            action_cb = lambda url=join_url, i=mtg_id, s=subject, t=alert.get("start_dt"): self._join_meeting(url, i, s, t)
            action_label = "Unirse"
        notification_manager.notify(
            level=NotificationLevel.MEETING,
            title=f"📅 {subject}",
            message=message,
            action_callback=action_cb,
            action_label=action_label,
        )
        audit.log_meeting_alert(
            mtg_id, subject,
            start_time=time_str,
            minutes_until=minutes,
        )

    def _on_meeting_started(self, mtg: dict):
        mtg_id = mtg.get("id", "")
        if mtg_id in self._ongoing_announced:
            return
        self._ongoing_announced.add(mtg_id)
        subject = mtg.get("subject", "Sin título")
        join_url = mtg.get("join_url", "")
        action_cb = None
        action_label = ""
        if join_url:
            action_cb = lambda url=join_url, i=mtg_id, s=subject, t=mtg.get("start_dt"): self._join_meeting(url, i, s, t)
            action_label = "Unirse ahora"
        notification_manager.notify(
            level=NotificationLevel.WARNING,
            title=f"🔔 Reunión en curso: {subject}",
            message="La reunión ha comenzado",
            action_callback=action_cb,
            action_label=action_label,
        )
        time_str = mtg.get("start_dt").strftime("%H:%M") if mtg.get("start_dt") else None
        audit.log_meeting_started(mtg_id, subject, start_time=time_str)

    def _join_meeting(self, url: str, event_id: str = "", subject: str = "", start_time=None):
        """Une al usuario a una reunión y registra el evento."""
        QDesktopServices.openUrl(QUrl(url))
        time_str = start_time.strftime("%H:%M") if start_time else None
        audit.log_meeting_joined(event_id, subject, start_time=time_str)

    def setup_wallpaper_carousel(self):
        settings = self.config_manager.get_wallpaper_settings()
        folder = settings["folder"]
        interval = settings["interval"]

        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        
        self.wallpaper_files = [
            os.path.join(folder, f) for f in os.listdir(folder)
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp'))
        ]
        
        if self.wallpaper_files:
            self.next_wallpaper()
            if len(self.wallpaper_files) > 1:
                self.wallpaper_timer.start(interval * 1000)
        else:
            self.central_widget.setStyleSheet(
                f"#MainLauncher {{ background-color: {self.tokens.surface_base}; }}"
            )

    def next_wallpaper(self):
        if not self.wallpaper_files:
            return
            
        file_path = self.wallpaper_files[self.wallpaper_index]
        # Usar barras normales para QSS en Windows
        qss_path = file_path.replace("\\", "/")
        
        self.central_widget.setStyleSheet(f"""
            #MainLauncher {{
                background-image: url("{qss_path}");
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
        """)
        
        # Calcular brillo de la imagen
        is_light_bg = False
        try:
            image = QImage(file_path)
            if not image.isNull():
                scaled = image.scaled(1, 1, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.FastTransformation)
                color = QColor(scaled.pixel(0, 0))
                brightness = 0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()
                is_light_bg = (brightness > 130)
        except Exception as exc:
            logger.warning("Error calculando brillo del wallpaper: %s", exc)

        # Ajustar contraste del texto de los títulos
        self.adjust_text_contrast(is_light_bg)
        
        self.wallpaper_index = (self.wallpaper_index + 1) % len(self.wallpaper_files)

    def adjust_text_contrast(self, is_light_bg: bool):
        t = self.tokens
        text_color = t.text_primary
        date_color = t.text_secondary
        shadow_color = t.surface_inverse
        cal_title_color = t.meeting
        signature_color = t.text_muted

        def apply_style(label, color, shadow_col):
            if label is None:
                return
            label.setStyleSheet(f"color: {color};")
            effect = label.graphicsEffect()
            if isinstance(effect, QGraphicsDropShadowEffect):
                effect.setColor(QColor(shadow_col))
                effect.setBlurRadius(4 if is_light_bg else 2)

        if hasattr(self, 'header'):
            apply_style(self.header, text_color, shadow_color)
        if hasattr(self, 'clock_widget'):
            apply_style(self.clock_widget.clock_label, text_color, shadow_color)
            apply_style(self.clock_widget.date_label, date_color, shadow_color)
        if hasattr(self, 'signature'):
            apply_style(self.signature, signature_color, shadow_color)
        if hasattr(self, 'cal_title') and self.cal_title is not None:
            self.cal_title.setStyleSheet(
                f"font-family: \"{t.font_family_body}\"; "
                f"font-size: {t.type_lg}px; "
                f"font-weight: {t.weight_bold}; "
                f"color: {cal_title_color}; "
                f"margin-top: {t.space_4}px;"
            )
            effect = self.cal_title.graphicsEffect()
            if isinstance(effect, QGraphicsDropShadowEffect):
                effect.setColor(QColor(shadow_color))
                effect.setBlurRadius(4 if is_light_bg else 2)

    def init_ui(self):
        # Configuración de ventana
        self.setWindowTitle("Sistema Interactivo Sala de Reuniones")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.showFullScreen()

        # Widget central
        self.central_widget = QWidget()
        self.central_widget.setObjectName("MainLauncher")
        self.setCentralWidget(self.central_widget)

        # Efecto de Opacidad para Animación de Entrada
        self.opacity_effect = QGraphicsOpacityEffect(self.central_widget)
        self.central_widget.setGraphicsEffect(self.opacity_effect)

        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(800)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation.start()
        self.animation.finished.connect(lambda: self.central_widget.setGraphicsEffect(None))

        # Layout horizontal principal (Apps a la izquierda, Calendario a la derecha)
        self.content_layout = QHBoxLayout(self.central_widget)
        self.content_layout.setContentsMargins(60, 40, 60, 40)
        self.content_layout.setSpacing(40)

        # --- LADO IZQUIERDO: APPS Y CONTROLES ---
        left_panel = QVBoxLayout()
        self.content_layout.addLayout(left_panel, 3)

        # Cabecera con nombre + campana de notificaciones
        header_row = QHBoxLayout()
        self.header = QLabel(self.config_manager.config.get("corporate_name", "SALA DE REUNIONES"))
        self.header.setObjectName("HeaderLabel")
        self.header.setAlignment(Qt.AlignmentFlag.AlignLeft)
        apply_text_outline(self.header)
        header_row.addWidget(self.header, 1)

        self.notification_bell = NotificationBell(self)
        header_row.addWidget(self.notification_bell, 0, Qt.AlignmentFlag.AlignRight)

        left_panel.addLayout(header_row)

        # Widget de Reloj + Fecha (extraído)
        self.clock_widget = ClockWidget(self, show_date=True)
        self.clock_widget.update()
        left_panel.addWidget(self.clock_widget)

        # Espaciador
        left_panel.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Contenedor de Apps (Grid extraído)
        self.apps_container = QWidget()
        self.grid_layout = QGridLayout(self.apps_container)
        self.grid_layout.setSpacing(30)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        left_panel.addWidget(self.apps_container, 5)

        self.refresh_apps()

        left_panel.addStretch()

        # --- SECCIÓN DE CONTROLES INFERIORES ---
        controls_layout = QHBoxLayout()

        # Control de Volumen (extraído)
        self.volume_control = VolumeControl(self)
        controls_layout.addWidget(self.volume_control)
        self.volume_slider = self.volume_control.slider

        controls_layout.addStretch()

        # Botón "Compartir pantalla" (HDMI Input)
        # Separado del grid de apps para que las apps del sistema y esta
        # función especial estén visual y conceptualmente diferenciadas.
        self.share_screen_btn = QPushButton("🖥  Compartir pantalla")
        self.share_screen_btn.setObjectName("ShareScreenButton")
        self.share_screen_btn.setMinimumHeight(60)
        self.share_screen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.share_screen_btn.clicked.connect(self._open_hdmi_viewer)
        self.share_screen_btn.setVisible(self.config_manager.is_hdmi_enabled())
        controls_layout.addWidget(self.share_screen_btn)

        controls_layout.addSpacing(15)

        self.shutdown_btn = QPushButton("Apagar Equipo")
        self.shutdown_btn.setObjectName("ShutdownButton")
        self.shutdown_btn.setMinimumHeight(60)
        self.shutdown_btn.clicked.connect(self.shutdown_pc)
        controls_layout.addWidget(self.shutdown_btn)

        left_panel.addLayout(controls_layout)

        # --- LADO DERECHO: CALENDARIO ---
        # El panel derecho se construye en _setup_calendar_panel() para poder
        # llamarlo sin recrear toda la UI cuando se activa el calendario.
        self.right_panel_widget = None
        if self.calendar_manager:
            self._setup_calendar_panel()

        # Botón Admin (esquina inferior derecha) — tamaño mínimo táctil 80×44px
        self.admin_btn = QPushButton("Admin")
        self.admin_btn.setObjectName("AdminButton")
        self.admin_btn.clicked.connect(self.open_admin_panel)

        footer_layout = QHBoxLayout()

        self.signature = QLabel("Programado por Juan Jarque")
        self.signature.setObjectName("SignatureLabel")
        apply_text_outline(self.signature)
        self.signature.setStyleSheet(
            f"color: {self.tokens.text_muted}; "
            f"font-size: {self.tokens.type_xs}px; "
            f"font-style: italic; "
            f"letter-spacing: 1px;"
        )
        footer_layout.addWidget(self.signature)

        footer_layout.addStretch()
        footer_layout.addWidget(self.admin_btn)
        left_panel.addLayout(footer_layout)

    def _setup_calendar_panel(self):
        if self.right_panel_widget is not None:
            self.content_layout.removeWidget(self.right_panel_widget)
            self.right_panel_widget.deleteLater()

        self.right_panel_widget = QWidget()
        right_panel = QVBoxLayout(self.right_panel_widget)
        right_panel.setContentsMargins(0, 0, 0, 0)
        right_panel.setSpacing(self.tokens.space_4)

        cal_title_row = QHBoxLayout()
        cal_title_row.setSpacing(self.tokens.space_3)

        self.cal_title = QLabel("REUNIONES DE HOY")
        self.cal_title.setObjectName("CalendarTitle")
        self.cal_title.setStyleSheet(
            f"font-family: \"{self.tokens.font_family_display}\"; "
            f"font-size: {self.tokens.type_lg}px; "
            f"font-weight: {self.tokens.weight_bold}; "
            f"color: {self.tokens.meeting}; "
            f"letter-spacing: 2px; "
            f"margin-top: {self.tokens.space_4}px;"
        )
        apply_text_outline(self.cal_title)
        cal_title_row.addWidget(self.cal_title)
        cal_title_row.addStretch()

        self.room_status_badge = RoomStatusBadge(self.calendar_manager, parent=self)
        cal_title_row.addWidget(self.room_status_badge, 0, Qt.AlignmentFlag.AlignVCenter)

        right_panel.addLayout(cal_title_row)

        self.meetings_container = QVBoxLayout()
        self.meetings_container.setSpacing(self.tokens.space_3)
        right_panel.addLayout(self.meetings_container)
        right_panel.addStretch()

        self.content_layout.addWidget(self.right_panel_widget, 1)

    def update_time(self):
        if hasattr(self, 'clock_widget'):
            self.clock_widget.update()

    def update_calendar(self):
        """Lanza la petición de reuniones en un hilo de fondo para no bloquear la UI."""
        if not self.calendar_manager:
            return
        # Evitar lanzar un nuevo worker si el anterior aún está corriendo
        if hasattr(self, '_cal_worker') and self._cal_worker.isRunning():
            return
        self._cal_worker = CalendarFetchWorker(self.calendar_manager)
        self._cal_worker.meetings_ready.connect(self._on_meetings_ready)
        self._cal_worker.start()
    def _on_meetings_ready(self, raw_meetings, status):
        """Recibe los datos del worker y actualiza la UI en el hilo principal."""
        if not hasattr(self, 'meetings_container'):
            return

        # Limpiar tarjetas anteriores
        for i in reversed(range(self.meetings_container.count())):
            item = self.meetings_container.itemAt(i)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.setParent(None)

        # Mostrar aviso si el token ha expirado o hay error de autenticación
        if status in ("expired", "unauthenticated"):
            warn = QLabel("⚠ Sesión caducada — Accede al panel Admin para re-autenticar.")
            warn.setWordWrap(True)
            warn.setStyleSheet(
                f"color: {self.tokens.warning}; "
                f"font-size: {self.tokens.type_sm}px; "
                f"font-style: italic; "
                f"margin-top: {self.tokens.space_2}px;"
            )
            self.meetings_container.addWidget(warn)
            return
        if status == "forbidden":
            warn = QLabel("⚠ Error de permisos (403). Revisa la configuración del email de sala en Admin.")
            warn.setWordWrap(True)
            warn.setStyleSheet(
                f"color: {self.tokens.danger}; "
                f"font-size: {self.tokens.type_sm}px; "
                f"font-style: italic; "
                f"margin-top: {self.tokens.space_2}px;"
            )
            self.meetings_container.addWidget(warn)
            return
        if status == "error":
            warn = QLabel("⚠ No se pudo conectar con el calendario.")
            warn.setWordWrap(True)
            warn.setStyleSheet(
                f"color: {self.tokens.danger}; "
                f"font-size: {self.tokens.type_sm}px; "
                f"font-style: italic; "
                f"margin-top: {self.tokens.space_2}px;"
            )
            self.meetings_container.addWidget(warn)
            return

        # Graph devuelve start.dateTime en la timezone del evento (start.timeZone).
        # No asumimos UTC: usamos la hora tal como viene para mostrarla,
        # y filtramos por el día local del sistema operativo.
        today = datetime.now().date()
        meetings = []

        for mtg in raw_meetings:
            try:
                # Recortar microsegundos si los hay: "2024-05-18T10:00:00.0000000" → "2024-05-18T10:00:00"
                start_raw = mtg['start']['dateTime'].split('.')[0]
                start_tz_name = mtg['start'].get('timeZone', '')

                start_naive = datetime.strptime(start_raw, "%Y-%m-%dT%H:%M:%S")

                # Intentar convertir usando la timezone del evento si está disponible
                try:
                    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
                    tz = ZoneInfo(start_tz_name) if start_tz_name else None
                    start_dt = start_naive.replace(tzinfo=tz).astimezone() if tz else start_naive
                except Exception:
                    # Si la timezone no es IANA (p.ej. "Romance Standard Time"),
                    # usar la hora tal como viene (que Graph ya ajusta al rango pedido)
                    start_dt = start_naive

                if start_dt.date() == today:
                    mtg['_start_local'] = start_dt
                    
                    # Parsear también la hora de fin de la reunión
                    try:
                        end_raw = mtg['end']['dateTime'].split('.')[0]
                        end_tz_name = mtg['end'].get('timeZone', '')
                        end_naive = datetime.strptime(end_raw, "%Y-%m-%dT%H:%M:%S")
                        try:
                            from zoneinfo import ZoneInfo
                            tz_end = ZoneInfo(end_tz_name) if end_tz_name else None
                            end_dt = end_naive.replace(tzinfo=tz_end).astimezone() if tz_end else end_naive
                        except Exception:
                            end_dt = end_naive
                        mtg['_end_local'] = end_dt
                    except Exception:
                        mtg['_end_local'] = None

                    meetings.append(mtg)
            except Exception as e:
                logger.warning("Error procesando fecha de reunión: %s", e)

        if not meetings:
            empty_container = QFrame()
            empty_container.setObjectName("EmptyState")
            empty_layout = QVBoxLayout(empty_container)
            empty_layout.setContentsMargins(0, self.tokens.space_5, 0, 0)
            empty_layout.setSpacing(self.tokens.space_2)

            headline = QLabel("Sala libre")
            headline.setStyleSheet(
                f"color: {self.tokens.room_free}; "
                f"font-family: \"{self.tokens.font_family_display}\"; "
                f"font-size: {self.tokens.type_2xl}px; "
                f"font-weight: {self.tokens.weight_bold};"
            )
            empty_layout.addWidget(headline)

            subline = QLabel("Sin reuniones programadas para hoy.")
            subline.setStyleSheet(
                f"color: {self.tokens.text_secondary}; "
                f"font-size: {self.tokens.type_md}px;"
            )
            empty_layout.addWidget(subline)

            hint = QLabel("Reserva una reunión desde Outlook para que aparezca aquí.")
            hint.setWordWrap(True)
            hint.setStyleSheet(
                f"color: {self.tokens.text_muted}; "
                f"font-size: {self.tokens.type_sm}px; "
                f"font-style: italic;"
            )
            empty_layout.addWidget(hint)

            self.meetings_container.addWidget(empty_container)
            return

        for idx, mtg in enumerate(meetings[:5]):
            card = QFrame()
            card.setObjectName("MeetingCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(
                self.tokens.space_3, self.tokens.space_3,
                self.tokens.space_3, self.tokens.space_3
            )
            card_layout.setSpacing(self.tokens.space_1)

            subject_text = mtg.get('subject', 'Sin Título')
            subject = QLabel(subject_text)
            subject.setStyleSheet(
                f"color: {self.tokens.text_primary}; "
                f"font-family: \"{self.tokens.font_family_display}\"; "
                f"font-weight: {self.tokens.weight_semibold}; "
                f"font-size: {self.tokens.type_md}px;"
            )
            subject.setWordWrap(True)

            try:
                start_dt_local = mtg.get('_start_local')
                if start_dt_local is None:
                    start_raw = mtg['start']['dateTime'].split('.')[0]
                    start_dt_local = datetime.strptime(start_raw, "%Y-%m-%dT%H:%M:%S")

                end_dt_local = mtg.get('_end_local')
                if end_dt_local is None and 'end' in mtg:
                    try:
                        end_raw = mtg['end']['dateTime'].split('.')[0]
                        end_dt_local = datetime.strptime(end_raw, "%Y-%m-%dT%H:%M:%S")
                    except Exception:
                        end_dt_local = None

                if end_dt_local:
                    time_text = f"{start_dt_local.strftime('%H:%M')} – {end_dt_local.strftime('%H:%M')}"
                else:
                    time_text = start_dt_local.strftime("%H:%M")

                time_label = QLabel(time_text)
                time_label.setStyleSheet(
                    f"color: {self.tokens.text_secondary}; "
                    f"font-family: \"{self.tokens.font_family_mono}\"; "
                    f"font-size: {self.tokens.type_sm}px;"
                )
            except Exception:
                time_label = QLabel("Hora no disponible")
                time_label.setStyleSheet(
                    f"color: {self.tokens.text_muted}; "
                    f"font-size: {self.tokens.type_sm}px;"
                )

            card_layout.addWidget(subject)
            card_layout.addWidget(time_label)

            teams_url = mtg.get('onlineMeetingUrl') or (mtg.get('onlineMeeting') or {}).get('joinUrl')
            if teams_url:
                join_btn = QPushButton("Unirse a la reunión")
                join_btn.setObjectName("MeetingJoinButton")
                join_btn.setMinimumHeight(40)
                join_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                join_btn.clicked.connect(lambda checked, url=teams_url: QDesktopServices.openUrl(QUrl(url)))
                card_layout.addWidget(join_btn)

            self.meetings_container.addWidget(card)

            self._animate_card_in(card, delay_ms=idx * 80)

    def _animate_card_in(self, widget, delay_ms: int = 0):
        """Aplica un fade-in suave a un widget con un retraso opcional."""
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        effect.setOpacity(0.0)

        def start_anim():
            anim = QPropertyAnimation(effect, b"opacity")
            anim.setDuration(350)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            anim.finished.connect(lambda: widget.setGraphicsEffect(None))
            anim.start()
            # Guardar referencia para evitar GC prematuro
            widget._card_anim = anim

        if delay_ms > 0:
            QTimer.singleShot(delay_ms, start_anim)
        else:
            start_anim()

    def refresh_apps(self):
        # Limpiar grid
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            widget = item.widget() if item is not None else None
            if widget is not None:
                self.grid_layout.removeWidget(widget)
                widget.setParent(None)
                widget.deleteLater()

        apps = self.config_manager.get_apps()
        self.app_grid = AppGrid(
            apps,
            parent=self.apps_container,
            on_launch=self._on_launch_error,
        )
        self.grid_layout.addWidget(self.app_grid, 0, 0)

        # Mantener la visibilidad del botón "Compartir pantalla" sincronizada
        # con la configuración del admin.
        if hasattr(self, 'share_screen_btn'):
            self.share_screen_btn.setVisible(self.config_manager.is_hdmi_enabled())

    def _on_launch_error(self, error: str, app_info: dict):
        msg = QMessageBox(self)
        msg.setWindowTitle("Error al abrir aplicación")
        msg.setText(error)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        for b in msg.buttons():
            b.setMinimumSize(120, 50)
        msg.exec()

    def shutdown_pc(self):
        dlg = TouchConfirmDialog(
            title="Apagar Equipo",
            message="¿Confirmas que quieres apagar el equipo?",
            confirm_text="Apagar",
            cancel_text="Cancelar",
            danger=True,
            parent=self,
        )
        if dlg.exec():
            close_all_launched_apps()
            self._close_hdmi_viewer()
            import subprocess
            subprocess.Popen("shutdown -s -t 00", shell=True)

    def _open_hdmi_viewer(self):
        """Abre la ventana flotante del viewer HDMI."""
        if not self.config_manager.is_hdmi_enabled():
            notification_manager.notify(
                level=NotificationLevel.WARNING,
                title="HDMI no configurado",
                message="Activa 'Compartir pantalla' en el panel Admin.",
            )
            return

        if self._hdmi_viewer is not None and self._hdmi_viewer.isVisible():
            self._hdmi_viewer.activateWindow()
            self._hdmi_viewer.raise_()
            return

        cfg = self.config_manager.get_hdmi_input()
        try:
            self._hdmi_viewer = HDMIViewerWindow(
                device_index=cfg["device_index"],
                width=cfg["width"],
                height=cfg["height"],
                fps=cfg["fps"],
                parent=None,
            )
            self._hdmi_viewer.closed.connect(self._on_hdmi_viewer_closed)
            self._hdmi_viewer.show()
        except Exception as exc:
            logger.error("Error abriendo viewer HDMI: %s", exc, exc_info=True)
            notification_manager.notify(
                level=NotificationLevel.ERROR,
                title="Error al abrir Compartir pantalla",
                message=str(exc),
            )

    def _on_hdmi_viewer_closed(self):
        self._hdmi_viewer = None

    def _close_hdmi_viewer(self):
        """Cierra el viewer HDMI si está abierto (usado en Finalizar Reunión)."""
        if self._hdmi_viewer is not None:
            try:
                self._hdmi_viewer.force_stop()
            except Exception:
                pass
            self._hdmi_viewer = None

    def open_admin_panel(self):
        login = TouchAdminLoginDialog(self.config_manager.get_admin_password(), self)
        if login.exec():
            # Pasar el calendar_manager real para que la autenticación
            # ocurra en la misma instancia, no en una temporal descartable
            panel = AdminPanelDialog(self.config_manager, self,
                                     calendar_manager=self.calendar_manager)
            panel.exec()

            # Si el calendario acaba de activarse (o se re-vinculó), reconstruir
            if self.config_manager.config.get("calendar_enabled"):
                client_id = self.config_manager.get_client_id()
                tenant_id = self.config_manager.get_tenant_id()
                room_email = self.config_manager.get_room_email()
                if client_id:
                    # Reutilizar el calendar_manager si el panel lo actualizó,
                    # o crear uno nuevo si aún no existe
                    if panel.calendar_manager is not None:
                        self.calendar_manager = panel.calendar_manager
                    elif self.calendar_manager is None:
                        self.calendar_manager = CalendarManager(
                            client_id, tenant_id, room_email
                        )
                    if self.right_panel_widget is None:
                        self._setup_calendar_panel()
                    if not hasattr(self, 'cal_timer'):
                        self.cal_timer = QTimer(self)
                        self.cal_timer.timeout.connect(self.update_calendar)
                        self.cal_timer.start(1 * 60 * 1000)
                    self.update_calendar()

            self.refresh_apps()

    def keyPressEvent(self, a0):  # type: ignore[override]
        if a0 is not None and a0.key() == Qt.Key.Key_Escape:
            a0.ignore()
        else:
            super().keyPressEvent(a0)
