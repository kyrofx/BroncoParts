import os
import requests
from flask import current_app as app
from ..models import db, Part


class OnshapeService:
    def __init__(self, config):
        self.config = config
        self.base_url = os.environ.get('ONSHAPE_BASE_URL', 'https://cad.onshape.com')

    def _refresh_token(self):
        if not self.config.refresh_token or not self.config.client_id:
            return
        token_url = 'https://oauth.onshape.com/oauth/token'
        data = {'grant_type': 'refresh_token', 'refresh_token': self.config.refresh_token}
        auth = (self.config.client_id, self.config.client_secret)
        resp = requests.post(token_url, data=data, auth=auth)
        if resp.ok:
            tok = resp.json()
            self.config.access_token = tok['access_token']
            self.config.refresh_token = tok.get('refresh_token', self.config.refresh_token)
            db.session.commit()
        else:
            app.logger.error('Failed to refresh Onshape token: %s', resp.text)

    def _headers(self):
        if not self.config.access_token:
            self._refresh_token()
        return {'Authorization': f'Bearer {self.config.access_token}', 'Content-Type': 'application/json'}

    def list_parts(self):
        url = f"{self.base_url}/api/parts/d/{self.config.document_id}/w/{self.config.workspace_id}"
        resp = requests.get(url, headers=self._headers())
        if resp.ok:
            return resp.json().get('parts', [])
        app.logger.error('Failed to list parts: %s', resp.text)
        return []

    def get_part_metadata(self, element_id, part_id):
        url = f"{self.base_url}/api/metadata/d/{self.config.document_id}/w/{self.config.workspace_id}/e/{element_id}/p/{part_id}"
        resp = requests.get(url, headers=self._headers())
        if resp.ok:
            return resp.json()
        app.logger.error('Failed to fetch metadata: %s', resp.text)
        return {}

    def update_part_number(self, element_id, part_id, part_number):
        url = f"{self.base_url}/api/metadata/d/{self.config.document_id}/w/{self.config.workspace_id}/e/{element_id}/p/{part_id}"
        payload = {"properties": [{"name": "Part Number", "value": part_number}]}
        resp = requests.post(url, json=payload, headers=self._headers())
        if not resp.ok:
            app.logger.error('Failed to update part metadata: %s', resp.text)
        return resp.ok

    def extract_part_number(self, metadata):
        for prop in metadata.get('properties', []):
            if prop.get('name') == 'Part Number':
                return prop.get('value')
        return None


def generate_part_number(project, config):
    last = db.session.query(db.func.max(Part.numeric_id)).filter(Part.project_id == project.id).scalar()
    next_id = 1 if last is None else last + 1
    scheme = config.naming_scheme or 'OS'
    number = f"{project.prefix}-{scheme}-{next_id:04d}"
    return number, next_id

