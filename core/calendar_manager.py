import msal
import requests
import os
from datetime import datetime, timedelta, timezone
from core.logger import get_logger
from core.calendar_cache import MeetingsCache

CACHE_FILE = "token_cache.bin"
GRAPH_URL = "https://graph.microsoft.com/v1.0"

logger = get_logger("core.calendar_manager")

# Códigos de error de Graph API
_TOKEN_EXPIRED_CODE = 401
_PERMISSION_DENIED_CODE = 403


class CalendarManager:
    def __init__(self, client_id, tenant_id="common", room_email="", client_secret=None):
        self.client_id = client_id
        self.tenant_id = tenant_id
        self.room_email = room_email
        self.client_secret = client_secret
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"
        
        # En modo Aplicación usamos /.default, en modo Usuario scopes específicos
        self.scopes = ["https://graph.microsoft.com/.default"] if client_secret else [
            "User.Read", "Calendars.Read", "Calendars.Read.Shared", "openid", "profile", "offline_access"
        ]

        self.auth_status = "unauthenticated"
        self.cache = msal.SerializableTokenCache()
        self.meetings_cache = MeetingsCache()

        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r") as f:
                    self.cache.deserialize(f.read())
                if self.cache.serialize() != "{}":
                    self.auth_status = "ok"
            except: pass

        if self.client_secret:
            self.app = msal.ConfidentialClientApplication(
                self.client_id,
                authority=self.authority,
                client_credential=self.client_secret,
                token_cache=self.cache
            )
            self.auth_status = "ok"
        else:
            self.app = msal.PublicClientApplication(
                self.client_id,
                authority=self.authority,
                token_cache=self.cache
            )

    def save_cache(self):
        if self.cache.has_state_changed:
            try:
                with open(CACHE_FILE, "w") as f:
                    f.write(self.cache.serialize())
            except Exception as e:
                logger.error("Error guardando caché de token: %s", e)

    def logout(self):
        """Elimina las cuentas y limpia el cache."""
        if not self.client_secret:
            for account in self.app.get_accounts():
                self.app.remove_account(account)
        self.cache = msal.SerializableTokenCache()
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
        self.auth_status = "unauthenticated"

    def get_token(self):
        """Obtiene token de acceso."""
        if self.client_secret:
            result = self.app.acquire_token_for_client(scopes=self.scopes)
            if "access_token" in result:
                self.auth_status = "ok"
                return result["access_token"]
            self.auth_status = "error"
            return None

        accounts = self.app.get_accounts()
        if accounts:
            try:
                result = self.app.acquire_token_silent(self.scopes, account=accounts[0])
                if result and "access_token" in result:
                    self.save_cache()
                    self.auth_status = "ok"
                    return result["access_token"]
            except Exception as e:
                logger.error("Error renovando token: %s", e)

        if not accounts:
            self.auth_status = "unauthenticated"
        else:
            self.auth_status = "expired"
        return None

    def initiate_device_flow(self):
        if self.client_secret: return None
        flow = self.app.initiate_device_flow(scopes=self.scopes)
        if "user_code" not in flow:
            raise Exception("No se pudo iniciar el flujo de dispositivo")
        return flow

    def complete_device_flow(self, flow):
        result = self.app.acquire_token_by_device_flow(flow)
        if "access_token" in result:
            self.save_cache()
            self.auth_status = "ok"
            return True
        return False

    def get_upcoming_meetings(self):
        token = self.get_token()
        if not token:
            return [], self.auth_status

        local_now = datetime.now()
        local_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
        local_end = local_start + timedelta(days=1)
        utc_start = local_start.astimezone(timezone.utc)
        utc_end = local_end.astimezone(timezone.utc)

        start_range = (utc_start - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        end_range = (utc_end + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")

        headers = {'Authorization': f'Bearer {token}'}
        params = {
            'startDateTime': start_range,
            'endDateTime': end_range,
            '$select': 'subject,start,end,location,onlineMeetingUrl,onlineMeeting',
            '$orderby': 'start/dateTime',
            '$top': '20'
        }

        if self.room_email and self.room_email.strip():
            endpoint = f"{GRAPH_URL}/users/{self.room_email.strip()}/calendarView"
        else:
            endpoint = f"{GRAPH_URL}/me/calendarView"

        try:
            response = requests.get(endpoint, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                events = response.json().get('value', [])
                self.auth_status = "ok"
                self.meetings_cache.save(events)
                return events, "ok"
            elif response.status_code == _TOKEN_EXPIRED_CODE:
                self.auth_status = "expired"
                cached, _ = self.meetings_cache.load()
                if cached:
                    logger.info("Usando reuniones en cache por token expirado")
                    return cached, "expired"
                return [], "expired"
            elif response.status_code == _PERMISSION_DENIED_CODE:
                self.auth_status = "forbidden"
                return [], "forbidden"
            else:
                self.auth_status = "error"
                cached, _ = self.meetings_cache.load()
                if cached:
                    logger.info("Usando reuniones en cache por error de red")
                    return cached, "error"
                return [], "error"
        except Exception as exc:
            logger.warning("Fallo de red al obtener reuniones: %s", exc)
            self.auth_status = "error"
            cached, _ = self.meetings_cache.load()
            if cached:
                logger.info("Usando reuniones en cache por excepción de red")
                return cached, "error"
            return [], "error"

    def get_cached_meetings(self) -> list:
        meetings, _ = self.meetings_cache.load()
        return meetings

    @staticmethod
    def _parse_graph_datetime(field: dict) -> datetime:
        raw = field.get('dateTime', '').split('.')[0]
        if not raw:
            return None
        try:
            parsed = datetime.strptime(raw, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            return None

        tz_name = field.get('timeZone', '')
        try:
            from zoneinfo import ZoneInfo
            if tz_name:
                tz = ZoneInfo(tz_name)
                return parsed.replace(tzinfo=tz).astimezone().replace(tzinfo=None)
        except Exception:
            pass
        return parsed

    @staticmethod
    def parse_meeting_datetime(mtg: dict) -> datetime:
        """Parsea el campo start.dateTime de Graph API a hora local."""
        return CalendarManager._parse_graph_datetime(mtg.get('start', {}))

    @staticmethod
    def get_meeting_join_url(mtg: dict) -> str:
        """Extrae la URL de unirse a la reunión online (Teams)."""
        return mtg.get('onlineMeetingUrl') or (mtg.get('onlineMeeting') or {}).get('joinUrl', '')

    def get_upcoming_alerts(self, minutes_ahead: int = 10) -> list:
        """Retorna reuniones que están por empezar en los próximos N minutos
        y que aún no han sido alertadas.

        Cada elemento es un dict con: id, subject, start_dt, end_dt, join_url, minutes_until
        """
        events, status = self.get_upcoming_meetings()
        if status != "ok" or not events:
            return []

        now = datetime.now()
        alerts = []
        for mtg in events:
            mtg_id = mtg.get('id') or mtg.get('iCalUId', '')
            start_dt = self.parse_meeting_datetime(mtg)
            if not start_dt:
                continue
            delta = (start_dt - now).total_seconds() / 60.0
            if 0 <= delta <= minutes_ahead:
                end_dt = self._parse_graph_datetime(mtg.get('end', {}))
                alerts.append({
                    "id": mtg_id,
                    "subject": mtg.get('subject', 'Sin título'),
                    "start_dt": start_dt,
                    "end_dt": end_dt,
                    "join_url": self.get_meeting_join_url(mtg),
                    "minutes_until": int(delta),
                })
        return alerts

    def get_ongoing_meetings(self) -> list:
        """Retorna reuniones que están en curso ahora mismo."""
        events, status = self.get_upcoming_meetings()
        if status != "ok" or not events:
            return []
        now = datetime.now()
        ongoing = []
        for mtg in events:
            start_dt = self.parse_meeting_datetime(mtg)
            if not start_dt:
                continue
            end_dt = self._parse_graph_datetime(mtg.get('end', {}))
            if not end_dt:
                continue
            if start_dt <= now <= end_dt:
                ongoing.append({
                    "id": mtg.get('id', ''),
                    "subject": mtg.get('subject', 'Sin título'),
                    "start_dt": start_dt,
                    "end_dt": end_dt,
                    "join_url": self.get_meeting_join_url(mtg),
                })
        return ongoing
