import msal
import requests
import os
import json
from datetime import datetime, timedelta

CACHE_FILE = "token_cache.bin"
GRAPH_URL = "https://graph.microsoft.com/v1.0"

class CalendarManager:
    def __init__(self, client_id, tenant_id="common"):
        self.client_id = client_id
        self.tenant_id = tenant_id
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.scopes = ["Calendars.Read"]
        
        # Setup Token Cache
        self.cache = msal.SerializableTokenCache()
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as f:
                self.cache.deserialize(f.read())
        
        self.app = msal.PublicClientApplication(
            self.client_id, 
            authority=self.authority,
            token_cache=self.cache
        )

    def save_cache(self):
        if self.cache.has_state_changed:
            with open(CACHE_FILE, "w") as f:
                f.write(self.cache.serialize())

    def get_token(self):
        # 1. Try to get from cache
        accounts = self.app.get_accounts()
        if accounts:
            result = self.app.acquire_token_silent(self.scopes, account=accounts[0])
            if result:
                self.save_cache()
                return result.get("access_token")
        return None

    def initiate_device_flow(self):
        """
        Inicia el flujo de código de dispositivo.
        Devuelve el diccionario de flujo que contiene 'user_code' y 'message'.
        """
        flow = self.app.initiate_device_flow(scopes=self.scopes)
        if "user_code" not in flow:
            error_msg = flow.get("error_description") or flow.get("error") or "Desconocido"
            raise Exception(f"No se pudo iniciar el flujo de dispositivo: {error_msg}")
        return flow

    def complete_device_flow(self, flow):
        """
        Espera a que el usuario complete el inicio de sesión.
        """
        result = self.app.acquire_token_by_device_flow(flow)
        if "access_token" in result:
            self.save_cache()
            return True
        return False

    def get_upcoming_meetings(self):
        """
        Obtiene las reuniones de hoy.
        """
        token = self.get_token()
        if not token:
            return []

        # Rango de tiempo: Un poco más amplio para evitar problemas de zona horaria
        now = datetime.utcnow()
        # Pedimos desde hace 12 horas hasta dentro de 24 horas para cubrir todo el día local
        start_range = (now - timedelta(hours=12)).isoformat() + "Z"
        end_range = (now + timedelta(hours=24)).isoformat() + "Z"

        headers = {
            'Authorization': f'Bearer {token}',
            'Prefer': 'outlook.timezone="UTC"' # Usamos UTC y convertimos nosotros
        }
        params = {
            'startDateTime': start_range,
            'endDateTime': end_range,
            '$select': 'subject,start,end,location,onlineMeetingUrl,onlineMeeting',
            '$orderby': 'start/dateTime',
            '$top': '20'
        }

        try:
            response = requests.get(
                f"{GRAPH_URL}/me/calendarView",
                headers=headers,
                params=params,
                timeout=10
            )
            if response.status_code == 200:
                events = response.json().get('value', [])
                return events
            else:
                print(f"Error Graph API: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            print(f"Error fetching meetings: {e}")
            return []
