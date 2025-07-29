import datetime
import requests
from flask import current_app
from ..models import db, Project, Part, OnshapeProjectSetting


def generate_part_number(project: Project):
    last_part = (
        Part.query.filter_by(project_id=project.id)
        .order_by(Part.numeric_id.desc())
        .first()
    )
    next_num = (last_part.numeric_id if last_part else 0) + 1
    year = datetime.datetime.now().year
    part_number = f"{year}-{project.prefix}-{next_num:04d}"
    return part_number, next_num


def update_part_metadata(settings: OnshapeProjectSetting, document_id: str, workspace_id: str, element_id: str, part_id: str, part_number: str):
    url = f"{settings.base_url}/api/metadata/d/{document_id}/w/{workspace_id}/e/{element_id}/p/{part_id}"
    payload = {"properties": [{"name": "Part Number", "value": part_number}]}
    headers = {"Authorization": f"Bearer {settings.client_secret}", "Content-Type": "application/json"}
    try:
        requests.post(url, json=payload, headers=headers, timeout=5)
    except Exception as e:
        current_app.logger.error(f"Failed to update Onshape metadata: {e}")


def process_onshape_webhook(data: dict):
    doc_id = data.get("documentId")
    workspace_id = data.get("workspaceId")
    if not doc_id or not workspace_id:
        current_app.logger.warning("Webhook missing document or workspace id")
        return

    project = Project.query.first()
    if not project or not project.onshape_setting:
        current_app.logger.info("No project or Onshape settings configured")
        return

    part_number, numeric_id = generate_part_number(project)
    dummy_part_id = "newPart"
    dummy_element_id = data.get("elementId", "")

    new_part = Part(
        project_id=project.id,
        numeric_id=numeric_id,
        part_number=part_number,
        name="Onshape Part",
        type="part",
    )
    db.session.add(new_part)
    db.session.commit()

    update_part_metadata(project.onshape_setting, doc_id, workspace_id, dummy_element_id, dummy_part_id, part_number)
    current_app.logger.info(f"Assigned part number {part_number} for document {doc_id}")
