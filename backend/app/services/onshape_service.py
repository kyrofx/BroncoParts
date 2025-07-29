import requests
from flask import current_app
from ..models import db


class OnshapeService:
    BASE_URL = "https://cad.onshape.com"

    def __init__(self, project):
        self.project = project
        self.token = project.onshape_access_token

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def list_parts(self):
        url = f"{self.BASE_URL}/api/parts/d/{self.project.onshape_document_id}/w/{self.project.onshape_workspace_id}"
        resp = requests.get(url, headers=self._headers())
        resp.raise_for_status()
        return resp.json().get("parts", [])

    def get_part_metadata(self, element_id, part_id):
        url = f"{self.BASE_URL}/api/metadata/d/{self.project.onshape_document_id}/w/{self.project.onshape_workspace_id}/e/{element_id}/p/{part_id}"
        resp = requests.get(url, headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def update_part_metadata(self, element_id, part_id, part_number):
        url = f"{self.BASE_URL}/api/metadata/d/{self.project.onshape_document_id}/w/{self.project.onshape_workspace_id}/e/{element_id}/p/{part_id}"
        payload = {"properties": [{"name": "Part Number", "value": part_number}]}
        resp = requests.post(url, json=payload, headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def generate_part_number(self):
        next_num = self.project.onshape_next_part_number or 1
        part_number = f"{self.project.prefix}-P-{next_num:04d}"
        self.project.onshape_next_part_number = next_num + 1
        db.session.commit()
        return part_number
