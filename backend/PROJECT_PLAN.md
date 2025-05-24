# Project Plan: Backend Modernization (Phase 1)

**Goal:** Align the Flask/SQLAlchemy backend with `NEW_README.md` specifications for Part, Project, and User management. This phase excludes Order Management, WordPress SSO, and Email Notifications.

**Date:** May 22, 2025

---

## I. User Model & Authentication Enhancements

**Files Affected:** `app/models.py`, `app/routes.py`

1.  **Update `User` Model (`app/models.py`):**
    *   [x] Replace `is_admin` (Boolean) with `permission` (String).
        *   `permission = db.Column(db.String(50), nullable=False, default='readonly')`
        *   Valid values: "readonly", "editor", "admin".
    *   [x] Add `enabled` status.
        *   `enabled = db.Column(db.Boolean, nullable=False, default=False)` (New users default to disabled).
    *   [x] Update `__repr__` if necessary.

2.  **Update User Registration (`app/routes.py -> register_user`):**
    *   [x] When creating `new_user`, set `permission='readonly'` and `enabled=False` by default.
    *   [x] Update the JSON response to include `permission` and `enabled` fields.

3.  **Update Login (`app/routes.py -> login_user`):**
    *   [x] Modify `create_access_token`'s `identity` to include `user_id`, `username`, `permission`, and `enabled`.
        *   Example: `identity={'user_id': user.id, 'username': user.username, 'permission': user.permission, 'enabled': user.enabled}`
    *   [x] Add a check: If `not user.enabled`, return `jsonify(message="Error: Account disabled"), 403`.
    *   [x] Update the JSON response to include `permission` and `enabled`.

4.  **Update User Information Retrieval (`app/routes.py -> get_user`, `get_users`):**
    *   [x] Ensure `permission` and `enabled` fields are returned.
    *   [x] Remove references to `is_admin` from returned data if it was separate.

5.  **Update User Update (`app/routes.py -> update_user`):**
    *   [x] Logic for updating `permission` and `enabled`:
        *   Only users with `admin` permission (from JWT) can modify `permission` or `enabled` fields for any user.
        *   A non-admin user cannot change their own `permission` or `enabled` status.
    *   [x] Remove direct updates to `is_admin`.
    *   [x] Update response to reflect new fields.

6.  **Update Password Change (`app/routes.py -> change_user_password`):**
    *   [x] Ensure JWT identity check for admin rights uses the new `permission` field.

---

## II. Role-Based Access Control (RBAC)

**Files Affected:** `app/routes.py` (primarily, potentially a new `decorators.py`)

1.  **Create Permission Decorators:**
    *   [x] Define `admin_required(fn)`:
        *   Gets JWT identity.
        *   Returns `jsonify(message="Forbidden: Admin access required"), 403` if `identity['permission'] != 'admin'`.
    *   [x] Define `editor_or_admin_required(fn)`:
        *   Gets JWT identity.
        *   Returns `jsonify(message="Forbidden: Editor or Admin access required"), 403` if `identity['permission'] not in ['editor', 'admin']`.
    *   [x] Define `readonly_or_higher_required(fn)` (or simply rely on `@jwt_required` if all authenticated users have at least readonly):
        *   Gets JWT identity.
        *   Returns `jsonify(message="Forbidden: Access denied"), 403` if `identity['permission'] not in ['readonly', 'editor', 'admin']`. (Also check `enabled` status here for all protected routes).
        *   *Self-correction:* The `enabled` check should be part of these decorators or a general one applied after `@jwt_required`.

2.  **Apply Decorators to Routes:**
    *   [x] **Project Routes:**
        *   `create_project`, `update_project`: Apply `@editor_or_admin_required`. (Note: `delete_project` was updated to `@admin_required` based on typical requirements, overriding the plan's initial suggestion for `@editor_or_admin_required` for delete actions).
        *   `get_projects`, `get_project`: Apply `@readonly_or_higher_required`.
    *   [x] **Part Routes:**
        *   `create_part`, `update_part`: Apply `@editor_or_admin_required`. (Note: `delete_part` was updated to `@admin_required` for similar reasons as project deletion).
        *   `get_parts`, `get_parts_for_project`, `get_part`: Apply `@readonly_or_higher_required`.
    *   [x] **User Routes:**
        *   `get_users`, `delete_user`: Apply `@admin_required`.
        *   `update_user`: The route itself needs `@jwt_required`. Internal logic will differentiate self-update vs. admin update based on `user_id` and JWT `permission`. (Decorators applied handle enabled status).
        *   `get_user`: Similar to `update_user`, `@jwt_required` and internal logic. (Decorators applied handle enabled status, specific logic for self vs admin view retained).
        *   `change_user_password`: Similar, `@jwt_required` and internal logic. (Decorators applied handle enabled status).
    *   [x] Replace all existing `if not current_user_jwt['is_admin']:` checks with the new decorators or updated internal logic.
    *   [x] Ensure all permission decorators also check `if not current_user_jwt['enabled']: return jsonify(message="Error: Account disabled"), 403`.

---

## III. Part Model Enhancements

**Files Affected:** `app/models.py`

1.  **Update `Part` Model:**
    *   [x] Add `notes`: `db.Column(db.Text, nullable=True)` (Consider if `description` field already serves this purpose. Per `NEW_README.md`, `notes` is separate).
    *   [x] Add `source_material`: `db.Column(db.String(255), nullable=True, default='')`.
    *   [x] Add `have_material`: `db.Column(db.Boolean, default=False, nullable=False)`.
    *   [x] Add `quantity_required`: `db.Column(db.String(50), nullable=True, default='')` (For "As needed", "1 set". This is distinct from inventory `quantity_on_hand`).
    *   [x] Add `cut_length`: `db.Column(db.String(50), nullable=True, default='')`.
    *   [x] Add `priority`: `db.Column(db.Integer, default=1, nullable=False)` (0=High, 1=Normal, 2=Low).
    *   [x] Add `drawing_created`: `db.Column(db.Boolean, default=False, nullable=False)`.
    *   [x] Update `__repr__` if necessary.

---

## IV. Part Numbering Logic

**Files Affected:** `app/routes.py` (within `create_part`), potentially `app/models.py` for a helper.

1.  **Implement New Part Numbering in `create_part` route:**
    *   [x] **Input Validation:**
        *   `part_type` must be 'assembly' or 'part'.
        *   If `part_type == 'part'`, `parent_id` (referring to an assembly) must be provided and valid.
    *   [x] **Fetch Project:** `project = Project.query.get(project_id)`.
    *   [x] **Assembly Numbering (`part_type == 'assembly'`):
        *   Query for the `Part` with the highest `numeric_id` where `project_id == project.id` and `type == 'assembly'`.
        *   `last_assembly_numeric_id = db.session.query(db.func.max(Part.numeric_id)).filter(Part.project_id == project_id, Part.type == 'assembly').scalar()`
        *   If `last_assembly_numeric_id is None` (no assemblies yet), `next_numeric_id = 0`.
        *   Else, `next_numeric_id = ((last_assembly_numeric_id // 100) + 1) * 100`.
        *   `type_indicator = 'A'`.
    *   [x] **Part Numbering (`part_type == 'part'`):
        *   `parent_assembly = Part.query.get(parent_id)`. Validate it exists, belongs to the same project, and `parent_assembly.type == 'assembly'`.
        *   Query for the `Part` with the highest `numeric_id` where `project_id == project.id`, `type == 'part'`, and `parent_id == parent_assembly.id`.
        *   `last_child_part_numeric_id = db.session.query(db.func.max(Part.numeric_id)).filter(Part.project_id == project_id, Part.type == 'part', Part.parent_id == parent_id).scalar()`
        *   If `last_child_part_numeric_id is None` (no children yet for this parent assembly), `next_numeric_id = parent_assembly.numeric_id + 1`.
        *   Else, `next_numeric_id = last_child_part_numeric_id + 1`.
        *   `type_indicator = 'P'`.
        *   Constraint for child part `numeric_id` to not conflict with assembly block (e.g. `< parent_assembly.numeric_id + 100`).
    *   [x] **Generate `full_part_number`:** `f"{project.prefix}-{type_indicator}-{next_numeric_id:04d}"`.
    *   [x] **Collision Check:** `if Part.query.filter_by(part_number=generated_part_number).first(): ... return error ...` and `if Part.query.filter_by(project_id=project_id, numeric_id=next_numeric_id).first(): ... return error ...`.
    *   [x] Store the calculated `numeric_id` and `part_number` in the new `Part` object.

---

## V. Route Adjustments for Parts

**Files Affected:** `app/routes.py`

1.  **Update `create_part` Route:**
    *   [x] Integrate the new part numbering logic.
    *   [x] Ensure all new fields from the `Part` model (Step III) can be accepted from `request.json` and saved.
    *   [x] Update the JSON response to include all `Part` fields.

2.  **Update `update_part` Route:**
    *   [x] Allow updating of the new `Part` model fields.
    *   [x] Continue to prevent changing `numeric_id`, `part_number`, `project_id`, `type`.
    *   [x] Update the JSON response.

3.  **Update `get_part`, `get_parts`, `get_parts_for_project` Routes:**
    *   [x] Ensure all new and existing `Part` model fields are included in JSON responses.

4.  **Update `delete_part` Route:**
    *   [x] Add check: If `part.type == 'assembly'` and `Part.query.filter_by(parent_id=part_id).first()` exists, return `jsonify(message="Error: Cannot delete assembly with child parts"), 400`.

---

## VI. Database Migrations

1.  [x] After all model changes are complete:
    *   [x] Run `flask db migrate -m "Update User and Part models, implement RBAC and new part numbering"` (or a similar comprehensive message).
    *   [x] Run `flask db upgrade`.
2.  [ ] Test thoroughly after migrations.

---
