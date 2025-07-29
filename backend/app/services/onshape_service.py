import os
import logging
import requests
from flask import current_app

class OnshapeService:
    """Simple service for interacting with the Onshape API."""

    def __init__(self):
        self.base_url = os.environ.get("ONSHAPE_BASE_URL", "https://cad.onshape.com/api")
        self.access_token = os.environ.get("ONSHAPE_ACCESS_TOKEN")
        # In-memory counters for part numbers per project prefix
        if not hasattr(OnshapeService, "_counters"):
            OnshapeService._counters = {}

    def _headers(self):
        headers = {"Accept": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def generate_part_number(self, project_prefix: str) -> str:
        """Generate a simple part number using a prefix and incremental counter."""
        counter = OnshapeService._counters.get(project_prefix, 0) + 1
        OnshapeService._counters[project_prefix] = counter
        return f"{project_prefix}-{counter:04d}"

    def list_parts(self, document_id: str, workspace_id: str):
        url = f"{self.base_url}/parts/d/{document_id}/w/{workspace_id}"
        resp = requests.get(url, headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def get_part_metadata(self, document_id: str, workspace_id: str, element_id: str, part_id: str):
        url = f"{self.base_url}/metadata/d/{document_id}/w/{workspace_id}/e/{element_id}/p/{part_id}"
        resp = requests.get(url, headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def update_part_metadata(self, document_id: str, workspace_id: str, element_id: str, part_id: str, part_number: str):
        url = f"{self.base_url}/metadata/d/{document_id}/w/{workspace_id}/e/{element_id}/p/{part_id}"
        payload = {"properties": [{"name": "Part Number", "value": part_number}]}
        resp = requests.post(url, json=payload, headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def process_document(self, document_id: str, workspace_id: str, project_prefix: str):
        """Assign part numbers to parts in the document that lack them."""
        try:
            parts = self.list_parts(document_id, workspace_id)
        except Exception as e:
            logging.error(f"Failed to list parts: {e}")
            return

        for part in parts:
            part_id = part.get("partId")
            element_id = part.get("elementId")
            if not part_id or not element_id:
                continue
            try:
                meta = self.get_part_metadata(document_id, workspace_id, element_id, part_id)
            except Exception as e:
                logging.error(f"Failed to get metadata for part {part_id}: {e}")
                continue
            properties = meta.get("properties", [])
            has_part_number = any(p.get("name") == "Part Number" and p.get("value") for p in properties)
            if not has_part_number:
                new_number = self.generate_part_number(project_prefix)
                try:
                    self.update_part_metadata(document_id, workspace_id, element_id, part_id, new_number)
                    logging.info(f"Assigned part number {new_number} to part {part_id}")
                except Exception as e:
                    logging.error(f"Failed to update metadata for part {part_id}: {e}")

