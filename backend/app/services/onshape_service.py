import requests
from datetime import datetime, timedelta
from flask import current_app

API_BASE = "https://cad.onshape.com/api"

class OnshapeService:
    def __init__(self, config):
        self.config = config

    def _auth_headers(self):
        token = self.config.access_token
        return {"Authorization": f"Bearer {token}", "Accept": "application/json", "Content-Type": "application/json"}

    def refresh_token_if_needed(self):
        if not self.config.refresh_token:
            return
        if self.config.token_expires_at and self.config.token_expires_at > datetime.utcnow() + timedelta(minutes=2):
            return
        # Minimal token refresh call; assumes OAuth token endpoint
        resp = requests.post(
            "https://cad.onshape.com/oauth/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.config.refresh_token,
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        self.config.access_token = data.get("access_token")
        self.config.refresh_token = data.get("refresh_token", self.config.refresh_token)
        expires_in = data.get("expires_in", 3600)
        self.config.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        from .. import db
        db.session.commit()

    def list_parts(self):
        self.refresh_token_if_needed()
        url = f"{API_BASE}/parts/d/{self.config.document_id}/w/{self.config.workspace_id}"
        r = requests.get(url, headers=self._auth_headers())
        r.raise_for_status()
        return r.json().get("parts", [])

    def get_part_metadata(self, element_id, part_id):
        self.refresh_token_if_needed()
        url = f"{API_BASE}/metadata/d/{self.config.document_id}/w/{self.config.workspace_id}/e/{element_id}/p/{part_id}"
        r = requests.get(url, headers=self._auth_headers())
        r.raise_for_status()
        return r.json()

    def update_part_metadata(self, element_id, part_id, part_number):
        self.refresh_token_if_needed()
        url = f"{API_BASE}/metadata/d/{self.config.document_id}/w/{self.config.workspace_id}/e/{element_id}/p/{part_id}"
        payload = {"properties": [{"name": "Part Number", "value": part_number}]}
        r = requests.post(url, headers=self._auth_headers(), json=payload)
        r.raise_for_status()
        return r.json()

    def assign_part_numbers(self):
        parts = self.list_parts()
        updated = []
        for p in parts:
            if not p.get('elementId') or not p.get('partId'):
                continue
            meta = self.get_part_metadata(p['elementId'], p['partId'])
            properties = {prop['propertyName']: prop.get('value') for prop in meta.get('properties', [])}
            if not properties.get('Part Number'):
                part_number = self.generate_next_part_number()
                self.update_part_metadata(p['elementId'], p['partId'], part_number)
                updated.append({'elementId': p['elementId'], 'partId': p['partId'], 'partNumber': part_number})
        return updated

    def generate_next_part_number(self):
        prefix = self.config.number_format.split('{')[0] if self.config.number_format else 'PN'
        number = self.config.counter or 1
        part_number = self.config.number_format.format(prefix=prefix, counter=number)
        self.config.counter = number + 1
        from .. import db
        db.session.commit()
        return part_number
