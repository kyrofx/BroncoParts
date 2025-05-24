from flask import Blueprint, jsonify, request
from flask import current_app as app
from .models import db, Project, Part, User, Order, OrderItem, RegistrationLink # Added RegistrationLink
from decimal import Decimal
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt # Import JWT functions
from .decorators import admin_required, editor_or_admin_required, readonly_or_higher_required
from datetime import datetime

@app.route('/api/hello')
@readonly_or_higher_required
def hello_world():
    return jsonify(message="Hello from Flask Backend!")

# --- Project Routes ---

@app.route('/api/projects', methods=['POST'])
@editor_or_admin_required
def create_project():
    data = request.json
    if not data or not data.get('name') or not data.get('prefix'):
        return jsonify(message="Error: Missing name or prefix"), 400
    
    new_project = Project(
        name=data['name'],
        prefix=data['prefix'],
        description=data.get('description'),
        hide_dashboards=data.get('hide_dashboards', False)
    )
    db.session.add(new_project)
    db.session.commit()
    return jsonify(message="Project created successfully", project={
        'id': new_project.id,
        'name': new_project.name,
        'prefix': new_project.prefix,
        'description': new_project.description,
        'hide_dashboards': new_project.hide_dashboards,
        'created_at': new_project.created_at.isoformat(),
        'updated_at': new_project.updated_at.isoformat()
    }), 201

@app.route('/api/projects', methods=['GET'])
@readonly_or_higher_required
def get_projects():
    projects = Project.query.all()
    output = []
    for project in projects:
        project_data = {
            'id': project.id,
            'name': project.name,
            'prefix': project.prefix,
            'description': project.description,
            'hide_dashboards': project.hide_dashboards,
            'created_at': project.created_at.isoformat(),
            'updated_at': project.updated_at.isoformat()
        }
        output.append(project_data)
    return jsonify(projects=output)

@app.route('/api/projects/<int:project_id>', methods=['GET'])
@readonly_or_higher_required
def get_project(project_id):
    project = Project.query.get_or_404(project_id)
    return jsonify(project={
        'id': project.id,
        'name': project.name,
        'prefix': project.prefix,
        'description': project.description,
        'hide_dashboards': project.hide_dashboards,
        'created_at': project.created_at.isoformat(),
        'updated_at': project.updated_at.isoformat()
    })

@app.route('/api/projects/<int:project_id>', methods=['PUT'])
@editor_or_admin_required
def update_project(project_id):
    project = Project.query.get_or_404(project_id)
    data = request.json
    if not data:
        return jsonify(message="Error: No input data provided"), 400

    project.name = data.get('name', project.name)
    project.prefix = data.get('prefix', project.prefix)
    project.description = data.get('description', project.description)
    project.hide_dashboards = data.get('hide_dashboards', project.hide_dashboards)
    
    db.session.commit()
    return jsonify(message="Project updated successfully", project={
        'id': project.id,
        'name': project.name,
        'prefix': project.prefix,
        'description': project.description,
        'hide_dashboards': project.hide_dashboards,
        'updated_at': project.updated_at.isoformat()
    })

@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
@admin_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return jsonify(message="Project deleted successfully")

@app.route('/api/projects/<int:project_id>/tree', methods=['GET'])
@readonly_or_higher_required
def get_project_tree(project_id):
    project = Project.query.get_or_404(project_id)

    memo = {} # Memoization cache for part nodes

    def format_part_node(part):
        if part.id in memo:
            return memo[part.id]

        node = {
            "name": part.name,
            "id": str(part.id),
            "type": part.type.lower(), # Ensure type is lowercase
            "attributes": {
                "part_number": part.part_number,
                # Add other relevant part attributes if needed
                # "description": part.description,
                # "status": part.status,
            }
        }

        if part.type.lower() == 'assembly':
            children_parts = part.children.order_by(Part.name).all() # Fetch and order children
            if children_parts:
                children_nodes = []
                for child_part in children_parts:
                    # Basic cycle detection: if child is already being processed higher up, skip
                    # This simple check might not cover all complex cycle scenarios in data
                    # but helps prevent infinite recursion for direct parent-child cycles.
                    # For robust cycle detection, a path tracking mechanism would be needed.
                    # However, react-d3-tree itself might have issues with cyclic data.
                    # For now, we assume data is mostly tree-like.
                    if child_part.id not in memo: # Check if child is not already processed (simple cycle check)
                         children_nodes.append(format_part_node(child_part))
                if children_nodes: # Only add children key if there are processed children
                    node["children"] = children_nodes
        
        memo[part.id] = node
        return node

    # Fetch top-level parts/assemblies for the project (those with no parent_id)
    # Order them by name for consistent tree structure
    top_level_parts = Part.query.filter_by(project_id=project.id, parent_id=None).order_by(Part.name).all()

    tree_children = []
    for p in top_level_parts:
        tree_children.append(format_part_node(p))

    return jsonify({
        "name": project.name,
        "id": f"project_{project.id}", # Giving the root node an ID too
        "type": "project", # Type for the root node
        "attributes": {
            "prefix": project.prefix,
            "description": project.description,
            # "created_at": project.created_at.isoformat() # Example of another attribute
        },
        "children": tree_children
    })

# --- Part Routes ---

@app.route('/api/parts', methods=['POST'])
@editor_or_admin_required
def create_part():
    data = request.json
    required_fields = ['name', 'project_id', 'type']
    if not data or not all(field in data for field in required_fields):
        return jsonify(message=f"Error: Missing one or more required fields: {required_fields}"), 400

    project_id = data['project_id']
    part_type = data['type'].lower()

    if part_type not in ['assembly', 'part']:
        return jsonify(message="Error: Invalid part type. Must be 'assembly' or 'part'."), 400

    project = Project.query.get(project_id)
    if not project:
        return jsonify(message=f"Error: Project with id {project_id} not found"), 404

    parent_id = data.get('parent_id')
    parent_assembly = None

    if part_type == 'part':
        if not parent_id:
            return jsonify(message="Error: 'parent_id' is required for type 'part'"), 400
        parent_assembly = Part.query.get(parent_id)
        if not parent_assembly:
            return jsonify(message=f"Error: Parent assembly with id {parent_id} not found"), 404
        if parent_assembly.project_id != project.id:
            return jsonify(message="Error: Parent assembly must belong to the same project."), 400
        if parent_assembly.type != 'assembly':
            return jsonify(message="Error: Parent part must be an assembly."), 400
    elif part_type == 'assembly' and parent_id:
        # Assemblies can optionally have a parent assembly
        parent_assembly = Part.query.get(parent_id)
        if not parent_assembly:
            return jsonify(message=f"Error: Parent assembly with id {parent_id} not found"), 404
        if parent_assembly.project_id != project.id:
            return jsonify(message="Error: Parent assembly must belong to the same project."), 400
        if parent_assembly.type != 'assembly':
            return jsonify(message="Error: Parent of an assembly must also be an assembly."), 400

    # New Part Numbering Logic
    next_numeric_id = None
    type_indicator = ''

    if part_type == 'assembly':
        type_indicator = 'A'
        last_assembly_numeric_id = db.session.query(db.func.max(Part.numeric_id)) \
            .filter(Part.project_id == project_id, Part.type == 'assembly').scalar()
        if last_assembly_numeric_id is None:
            next_numeric_id = 0 # First assembly starts at 0
        else:
            # Assemblies increment by 100 from the highest *assembly* numeric_id in the project
            next_numeric_id = ((last_assembly_numeric_id // 100) + 1) * 100 
            # This ensures that if last was 0, next is 100. If last was 100, next is 200.
            # If a part (e.g. 101) somehow has a higher numeric_id than an assembly (e.g. 100), this logic is safe.

    elif part_type == 'part': # parent_assembly is guaranteed to be set and validated here
        type_indicator = 'P'
        last_child_part_numeric_id = db.session.query(db.func.max(Part.numeric_id)) \
            .filter(Part.project_id == project_id, Part.type == 'part', Part.parent_id == parent_assembly.id).scalar()
        
        if last_child_part_numeric_id is None:
            # First child part starts at parent_assembly.numeric_id + 1
            next_numeric_id = parent_assembly.numeric_id + 1
        else:
            # Subsequent child parts increment by 1 from the last child part of that parent
            next_numeric_id = last_child_part_numeric_id + 1
        
        # Constraint: Child part's numeric_id should not encroach on the next assembly block.
        # e.g. if parent is A-0000 (numeric_id 0), children can be P-0001 to P-0099.
        # Next assembly will be A-0100 (numeric_id 100).
        if next_numeric_id % 100 == 0: # This means it's 100, 200, etc.
             # This situation implies we've run out of numbers in the 1-99 range for this parent assembly.
             # Or, the parent assembly itself is at a X99 number which is not per convention.
             # This is a system limitation or requires a more complex allocation strategy.
             return jsonify(message=f"Error: Cannot assign numeric_id {next_numeric_id}. It conflicts with assembly numbering sequence. Maximum 99 parts per assembly allowed with current scheme."), 400

    generated_part_number = f"{project.prefix}-{type_indicator}-{next_numeric_id:04d}"

    if Part.query.filter_by(part_number=generated_part_number).first():
        return jsonify(message=f"Error: Generated part number {generated_part_number} already exists. Collision detected."), 500
    if Part.query.filter_by(project_id=project_id, numeric_id=next_numeric_id).first():
        return jsonify(message=f"Error: Generated numeric_id {next_numeric_id} already exists for this project. Collision detected."), 500

    new_part = Part(
        numeric_id=next_numeric_id,
        part_number=generated_part_number,
        name=data['name'],
        project_id=project_id,
        type=part_type,
        parent_id=parent_assembly.id if parent_assembly else None, # Correctly assign parent_id
        description=data.get('description'),
        material=data.get('material'),
        revision=data.get('revision'),
        status=data.get('status', 'designing'),
        quantity_on_hand=data.get('quantity_on_hand', 0),
        quantity_on_order=data.get('quantity_on_order', 0),
        # New fields
        notes=data.get('notes'),
        source_material=data.get('source_material'),
        have_material=data.get('have_material', False),
        quantity_required=data.get('quantity_required'),
        cut_length=data.get('cut_length'),
        priority=data.get('priority', 1),
        drawing_created=data.get('drawing_created', False)
    )
    db.session.add(new_part)
    db.session.commit()
    
    part_data_response = {
        'id': new_part.id,
        'numeric_id': new_part.numeric_id,
        'part_number': new_part.part_number,
        'name': new_part.name,
        'project_id': new_part.project_id,
        'type': new_part.type,
        'parent_id': new_part.parent_id,
        'description': new_part.description,
        'material': new_part.material,
        'revision': new_part.revision,
        'status': new_part.status,
        'quantity_on_hand': new_part.quantity_on_hand,
        'quantity_on_order': new_part.quantity_on_order,
        'notes': new_part.notes,
        'source_material': new_part.source_material,
        'have_material': new_part.have_material,
        'quantity_required': new_part.quantity_required,
        'cut_length': new_part.cut_length,
        'priority': new_part.priority,
        'drawing_created': new_part.drawing_created,
        'created_at': new_part.created_at.isoformat(),
        'updated_at': new_part.updated_at.isoformat()
    }
    if parent_assembly: 
        part_data_response['parent_part_number'] = parent_assembly.part_number

    return jsonify(message="Part created successfully", part=part_data_response), 201

@app.route('/api/parts', methods=['GET'])
@readonly_or_higher_required
def get_parts():
    query = Part.query

    parent_id = request.args.get('parent_id')
    if parent_id:
        try:
            parent_id = int(parent_id)
            query = query.filter(Part.parent_id == parent_id)
        except ValueError:
            return jsonify(message="Error: Invalid parent_id format. Must be an integer."), 400

    parts = query.all()
    output = []
    for part in parts:
        part_data = {
            'id': part.id,
            'numeric_id': part.numeric_id, # Added numeric_id
            'part_number': part.part_number,
            'name': part.name,
            'project_id': part.project_id,
            'type': part.type, # Added type
            'parent_id': part.parent_id, # Added parent_id
            'description': part.description,
            'material': part.material,
            'revision': part.revision,
            'status': part.status,
            'quantity_on_hand': part.quantity_on_hand,
            'quantity_on_order': part.quantity_on_order,
            'notes': part.notes,
            'source_material': part.source_material,
            'have_material': part.have_material,
            'quantity_required': part.quantity_required,
            'cut_length': part.cut_length,
            'priority': part.priority,
            'drawing_created': part.drawing_created,
            'created_at': part.created_at.isoformat(),
            'updated_at': part.updated_at.isoformat()
        }
        # Optionally, fetch and add parent part number if parent_id exists
        if part.parent_id:
            parent = Part.query.get(part.parent_id)
            if parent:
                part_data['parent_part_number'] = parent.part_number
        output.append(part_data)
    return jsonify(parts=output)

@app.route('/api/projects/<int:project_id>/parts', methods=['GET'])
@readonly_or_higher_required
def get_parts_for_project(project_id):
    project = Project.query.get_or_404(project_id)
    parts = Part.query.filter_by(project_id=project_id).all()
    output = []
    for part in parts:
        part_data = {
            'id': part.id,
            'numeric_id': part.numeric_id, # Added numeric_id
            'part_number': part.part_number,
            'name': part.name,
            'project_id': part.project_id,
            'type': part.type, # Added type
            'parent_id': part.parent_id, # Added parent_id
            'description': part.description,
            'material': part.material,
            'revision': part.revision,
            'status': part.status,
            'quantity_on_hand': part.quantity_on_hand,
            'quantity_on_order': part.quantity_on_order,
            'notes': part.notes,
            'source_material': part.source_material,
            'have_material': part.have_material,
            'quantity_required': part.quantity_required,
            'cut_length': part.cut_length,
            'priority': part.priority,
            'drawing_created': part.drawing_created,
            'created_at': part.created_at.isoformat(),
            'updated_at': part.updated_at.isoformat()
        }
        # Optionally, fetch and add parent part number if parent_id exists
        if part.parent_id:
            parent = Part.query.get(part.parent_id)
            if parent:
                part_data['parent_part_number'] = parent.part_number
        output.append(part_data)
    return jsonify(parts=output)

@app.route('/api/parts/<int:part_id>', methods=['GET'])
@readonly_or_higher_required
def get_part(part_id):
    part = Part.query.get_or_404(part_id)
    part_data_response = {
        'id': part.id,
        'numeric_id': part.numeric_id, # Added numeric_id
        'part_number': part.part_number,
        'name': part.name,
        'project_id': part.project_id,
        'type': part.type, # Added type
        'parent_id': part.parent_id, # Added parent_id
        'description': part.description,
        'material': part.material,
        'revision': part.revision,
        'status': part.status,
        'quantity_on_hand': part.quantity_on_hand,
        'quantity_on_order': part.quantity_on_order,
        'notes': part.notes,
        'source_material': part.source_material,
        'have_material': part.have_material,
        'quantity_required': part.quantity_required,
        'cut_length': part.cut_length,
        'priority': part.priority,
        'drawing_created': part.drawing_created,
        'created_at': part.created_at.isoformat(),
        'updated_at': part.updated_at.isoformat()
    }
    if part.parent_id: # Add parent part number to response if applicable
        parent = Part.query.get(part.parent_id)
        if parent:
            part_data_response['parent_part_number'] = parent.part_number
    
    # Optionally, include children parts
    children_parts = []
    for child in part.children.all(): # Assuming 'children' is the relationship name in Part model
        children_parts.append({
            'id': child.id,
            'part_number': child.part_number,
            'name': child.name,
            'type': child.type
        })
    if children_parts:
        part_data_response['children_parts'] = children_parts

    return jsonify(part=part_data_response)

@app.route('/api/parts/<int:part_id>', methods=['PUT'])
@editor_or_admin_required
def update_part(part_id):
    part = Part.query.get_or_404(part_id)
    data = request.json
    if not data:
        return jsonify(message="Error: No input data provided"), 400

    # Fields that can be updated: name, description, material, revision, status, quantities, parent_id
    # and new fields: notes, source_material, have_material, quantity_required, cut_length, priority, drawing_created
    # Part number, numeric_id, project_id, type should generally not be changed after creation
    # or require special handling.

    part.name = data.get('name', part.name)
    part.description = data.get('description', part.description)
    part.material = data.get('material', part.material)
    part.revision = data.get('revision', part.revision)
    part.status = data.get('status', part.status)
    part.quantity_on_hand = data.get('quantity_on_hand', part.quantity_on_hand)
    part.quantity_on_order = data.get('quantity_on_order', part.quantity_on_order)

    # Update new fields
    part.notes = data.get('notes', part.notes)
    part.source_material = data.get('source_material', part.source_material)
    part.have_material = data.get('have_material', part.have_material)
    part.quantity_required = data.get('quantity_required', part.quantity_required)
    part.cut_length = data.get('cut_length', part.cut_length)
    part.priority = data.get('priority', part.priority)
    part.drawing_created = data.get('drawing_created', part.drawing_created)

    if 'parent_id' in data:
        new_parent_id = data['parent_id']
        if new_parent_id is not None:
            if new_parent_id == part.id: # Prevent self-parenting
                 return jsonify(message="Error: Part cannot be its own parent."), 400
            parent_part = Part.query.get(new_parent_id)
            if not parent_part:
                return jsonify(message=f"Error: New parent part with id {new_parent_id} not found"), 404
            if parent_part.project_id != part.project_id:
                 return jsonify(message="Error: New parent part must belong to the same project."), 400
            # TODO: Add cycle detection if allowing deep hierarchies and parent changes.
            part.parent_id = new_parent_id
        else: # Setting parent_id to null
            part.parent_id = None
            
    # Warn if trying to change immutable fields like type or project_id without specific logic
    if 'type' in data and data['type'] != part.type:
        return jsonify(message="Error: Part type cannot be changed after creation through this endpoint."), 400
    if 'project_id' in data and data['project_id'] != part.project_id:
        return jsonify(message="Error: Part project_id cannot be changed after creation through this endpoint."), 400
    
    db.session.commit()
    
    part_data_response = {
        'id': part.id,
        'numeric_id': part.numeric_id,
        'part_number': part.part_number,
        'name': part.name,
        'project_id': part.project_id,
        'type': part.type,
        'parent_id': part.parent_id,
        'description': part.description,
        'material': part.material,
        'revision': part.revision,
        'status': part.status,
        'quantity_on_hand': part.quantity_on_hand,
        'quantity_on_order': part.quantity_on_order,
        'notes': part.notes,
        'source_material': part.source_material,
        'have_material': part.have_material,
        'quantity_required': part.quantity_required,
        'cut_length': part.cut_length,
        'priority': part.priority,
        'drawing_created': part.drawing_created,
        'created_at': part.created_at.isoformat(), # Ensure created_at is also present
        'updated_at': part.updated_at.isoformat()
    }
    if part.parent_id:
        parent = Part.query.get(part.parent_id)
        if parent:
            part_data_response['parent_part_number'] = parent.part_number
            
    return jsonify(message="Part updated successfully", part=part_data_response)

@app.route('/api/parts/<int:part_id>', methods=['DELETE'])
@admin_required
def delete_part(part_id):
    part = Part.query.get_or_404(part_id)
    # Check if the part is an assembly and has children
    if part.type == 'assembly' and part.children.first(): # Assuming 'children' is the backref relationship
        return jsonify(message="Error: Cannot delete assembly that has child parts. Please delete or reassign child parts first."), 400
    db.session.delete(part)
    db.session.commit()
    return jsonify(message="Part deleted successfully")

# --- User Routes ---

@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.json
    required_fields = ['username', 'email', 'password', 'first_name', 'last_name']
    if not data or not all(field in data for field in required_fields):
        return jsonify(message=f"Error: Missing one or more required fields: {required_fields}"), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify(message="Error: Username already exists"), 409
    if User.query.filter_by(email=data['email']).first():
        return jsonify(message="Error: Email already exists"), 409

    new_user = User(
        username=data['username'],
        email=data['email'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        permission='readonly',  # Default permission
        enabled=False,  # Default enabled status
        is_approved=False, # Default approval status
        requested_at=datetime.utcnow() # Set request time
    )
    new_user.set_password(data['password'])
    db.session.add(new_user)
    db.session.commit()
    
    user_data = {
        'id': new_user.id,
        'username': new_user.username,
        'email': new_user.email,
        'first_name': new_user.first_name,
        'last_name': new_user.last_name,
        'permission': new_user.permission,
        'enabled': new_user.enabled,
        'is_approved': new_user.is_approved, # Include approval status
        'requested_at': new_user.requested_at.isoformat() if new_user.requested_at else None, # Include request time
        'created_at': new_user.created_at.isoformat()
    }
    return jsonify(message="User registered successfully. Account is pending admin approval.", user=user_data), 201

@app.route('/api/admin/users', methods=['POST'])
@admin_required
def admin_create_user():
    data = request.json
    required_fields = ['username', 'email', 'password', 'permission']
    if not data or not all(field in data for field in required_fields):
        return jsonify(message=f"Error: Missing one or more required fields: {required_fields}"), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify(message="Error: Username already exists"), 409
    if User.query.filter_by(email=data['email']).first():
        return jsonify(message="Error: Email already exists"), 409

    new_user = User(
        username=data['username'],
        email=data['email'],
        first_name=data.get('first_name', ''),
        last_name=data.get('last_name', ''),
        permission=data['permission'],
        enabled=data.get('enabled', True),  # Admins can create enabled users
        is_approved=data.get('is_approved', True), # Admins can create approved users
        requested_at=datetime.utcnow() # Set request time, though likely approved immediately
    )
    new_user.set_password(data['password'])
    db.session.add(new_user)
    db.session.commit()
    
    user_data = {
        'id': new_user.id,
        'username': new_user.username,
        'email': new_user.email,
        'first_name': new_user.first_name,
        'last_name': new_user.last_name,
        'permission': new_user.permission,
        'enabled': new_user.enabled,
        'is_approved': new_user.is_approved,
        'requested_at': new_user.requested_at.isoformat() if new_user.requested_at else None,
        'created_at': new_user.created_at.isoformat()
    }
    return jsonify(message="User created successfully by admin.", user=user_data), 201

@app.route('/api/login', methods=['POST'])
def login():
    app.logger.debug(f"Login attempt: headers: {request.headers}")
    app.logger.debug(f"Login attempt: is_json: {request.is_json}")
    app.logger.debug(f"Login attempt: raw data: {request.data}")
    try:
        data = request.get_json()
        app.logger.debug(f"Login attempt: parsed_json data: {data}")
    except Exception as e:
        app.logger.error(f"Error getting JSON: {e}")
        data = None

    # Expect 'email' instead of 'username' from the request payload
    if not data or not data.get('email') or not data.get('password'):
        app.logger.warning(f"Login failed: Missing email/password or not JSON. Data: {data}")
        return jsonify(message="Error: Missing email or password"), 400

    # Query user by email. Ensure your User model has an 'email' field for this query.
    user = User.query.filter_by(email=data['email']).first()

    if not user:
        app.logger.warning(f"Login attempt for non-existent email: {data['email']}")
        return jsonify(message="Error: Invalid credentials"), 401

    if not user.check_password(data['password']):
        app.logger.warning(f"Failed login attempt for email: {data['email']}") # Changed to log email
        return jsonify(message="Error: Invalid credentials"), 401

    if not user.enabled:
        app.logger.warning(f"Login attempt for disabled user with email: {data['email']}") # Changed to log email
        return jsonify(message="Error: Account disabled"), 403

    if not user.is_approved:
        app.logger.warning(f"Login attempt for not approved user with email: {data['email']}")
        return jsonify(message="Error: Account not approved"), 403

    # The main identity for the 'sub' claim should be a string (e.g., user.id as string).
    # Additional user details go into additional_claims.
    user_claims = {
        "username": user.username, # Keep user.username here for claims, it might be different from email
        "permission": user.permission,
        "enabled": user.enabled,
        "is_approved": user.is_approved
    }
    access_token = create_access_token(identity=str(user.id), additional_claims=user_claims)
    
    app.logger.info(f"User with email {data['email']} (username: {user.username}) logged in successfully.") # Enhanced log
    return jsonify(access_token=access_token, user = {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "permission": user.permission,
        "enabled": user.enabled,
        "is_approved": user.is_approved
    }), 200

# Basic CRUD for Users (would typically be admin-protected)
@app.route('/api/users', methods=['GET'])
@admin_required
def get_users():
    users = User.query.all()
    output = []
    for user in users:
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'permission': user.permission,
            'enabled': user.enabled,
            'is_approved': user.is_approved, # Add is_approved
            'requested_at': user.requested_at.isoformat() if user.requested_at else None, # Add requested_at
            'created_at': user.created_at.isoformat(),
            'updated_at': user.updated_at.isoformat()
        }
        output.append(user_data)
    return jsonify(users=output)

@app.route('/api/users/<int:user_id>', methods=['GET'])
@jwt_required() # Keep @jwt_required for identity, decorator handles specific logic
def get_user(user_id):
    # current_user_jwt = get_jwt_identity() # Incorrect: returns only the identity (sub)
    current_jwt_payload = get_jwt() # Correct: returns the full decoded JWT payload
    user_to_get = User.query.get_or_404(user_id)
    
    # Admin can get any user, or user can get their own info if enabled
    # The readonly_or_higher_required decorator already checks for enabled status.
    if not current_jwt_payload.get('enabled'):
        return jsonify(message="Error: Account disabled"), 403
    
    if not user_to_get.is_approved and current_jwt_payload.get('permission') != 'admin': # Non-admins cannot view non-approved users (even themselves if somehow not approved yet)
        return jsonify(message="Error: Account not approved."), 403

    if current_jwt_payload.get('permission') == 'admin' or \
       (str(user_to_get.id) == current_jwt_payload.get('sub') and \
        user_to_get.is_approved and \
        current_jwt_payload.get('permission') in ['readonly', 'editor', 'project_manager', 'viewer']): # Added viewer, ensure all roles can view themselves if approved
        # User data retrieval logic remains the same
        user_data = {
            'id': user_to_get.id,
            'username': user_to_get.username,
            'email': user_to_get.email,
            'first_name': user_to_get.first_name,
            'last_name': user_to_get.last_name,
            'permission': user_to_get.permission,
            'enabled': user_to_get.enabled,
            'is_approved': user_to_get.is_approved, # Add is_approved
            'requested_at': user_to_get.requested_at.isoformat() if user_to_get.requested_at else None, # Add requested_at
            'created_at': user_to_get.created_at.isoformat(),
            'updated_at': user_to_get.updated_at.isoformat()
        }
        return jsonify(user=user_data)
    else:
        return jsonify(message="Forbidden: You cannot access this user's information."), 403

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@jwt_required() # Keep @jwt_required for identity, decorator handles specific logic
def update_user(user_id):
    # current_user_jwt = get_jwt_identity() # Incorrect
    current_jwt_payload = get_jwt() # Correct
    user_to_update = User.query.get_or_404(user_id)
    data = request.get_json()

    if not data:
        return jsonify(message="Error: No input data provided"), 400

    # Permission check: Only admin can edit users
    if current_jwt_payload.get('permission') != 'admin':
        return jsonify(message="Forbidden: You do not have permission to edit users."), 403

    # Prevent admin from disabling or unapproving their own account
    if str(user_to_update.id) == current_jwt_payload.get('sub'):
        if 'enabled' in data and not data['enabled']:
            return jsonify(message="Error: You cannot disable your own account."), 400
        if 'is_approved' in data and not data['is_approved']:
            return jsonify(message="Error: You cannot unapprove your own account."), 400

    # Update fields
    if 'email' in data:
        existing_user = User.query.filter(User.email == data['email'], User.id != user_id).first()
        if existing_user:
            return jsonify(message=f"Error: Email {data['email']} is already in use."), 400
        user_to_update.email = data['email']
    
    if 'permission' in data:
        user_to_update.permission = data['permission']
    
    if 'enabled' in data:
        user_to_update.enabled = data['enabled']

    if 'is_approved' in data:
        user_to_update.is_approved = data['is_approved']
        if data['is_approved']:
            user_to_update.enabled = True # Also enable if approving
            if not user_to_update.requested_at: # If admin creates and approves, requested_at might be null
                user_to_update.requested_at = datetime.utcnow()

    if 'password' in data and data['password']:
        user_to_update.set_password(data['password'])

    db.session.commit()
    return jsonify(message="User updated successfully", user=user_to_update.to_dict()), 200

@app.route('/api/users/<int:user_id>/approve', methods=['POST'])
@admin_required
def approve_user(user_id):
    user_to_approve = User.query.get_or_404(user_id)
    
    if user_to_approve.is_approved:
        return jsonify(message="User is already approved."), 400
        
    user_to_approve.is_approved = True
    user_to_approve.enabled = True # Also enable the user upon approval
    # user_to_approve.requested_at = None # Optionally clear requested_at or leave as is for record
    db.session.commit()
    
    user_data = {
        'id': user_to_approve.id,
        'username': user_to_approve.username,
        'email': user_to_approve.email,
        'permission': user_to_approve.permission,
        'enabled': user_to_approve.enabled,
        'is_approved': user_to_approve.is_approved,
        'updated_at': user_to_approve.updated_at.isoformat()
    }
    return jsonify(message="User approved successfully.", user=user_data), 200

@app.route('/api/users/<int:user_id>/change-password', methods=['PUT'])
@jwt_required() # Keep @jwt_required, logic inside handles permissions
def change_user_password(user_id):
    current_user_jwt = get_jwt_identity()
    user_to_update = User.query.get_or_404(user_id)
    data = request.json

    if not current_user_jwt.get('enabled'):
        return jsonify(message="Error: Account disabled, cannot change password."), 403

    if not data or not data.get('new_password'):
        return jsonify(message="Error: Missing new_password"), 400
    
    is_admin_acting = current_user_jwt.get('permission') == 'admin'
    is_self_update = current_user_jwt.get('user_id') == user_to_update.id

    if is_self_update:
        if not data.get('old_password') or not user_to_update.check_password(data.get('old_password')):
            return jsonify(message="Error: Incorrect old password"), 401
    elif not is_admin_acting:
        return jsonify(message="Forbidden: You can only change your own password or you are not an admin."), 403

    user_to_update.set_password(data['new_password'])
    db.session.commit()
    return jsonify(message="Password updated successfully")

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    current_user_jwt_payload = get_jwt() # Changed to get_jwt() to get the full payload
    user_to_delete = User.query.get_or_404(user_id)
    # Compare with 'sub' claim which holds the user ID
    if str(user_to_delete.id) == current_user_jwt_payload.get('sub'): 
        return jsonify(message="Error: Admin users cannot delete themselves through this endpoint."), 400

    db.session.delete(user_to_delete)
    db.session.commit()
    return jsonify(message="User deleted successfully")

# --- Stats Routes ---

@app.route('/api/stats/active-users', methods=['GET'])
@readonly_or_higher_required # Or a more specific permission if needed
def get_active_users_count():
    try:
        count = User.query.filter_by(enabled=True, is_approved=True).count()
        return jsonify(count=count), 200
    except Exception as e:
        app.logger.error(f"Error fetching active users count: {e}")
        return jsonify(message="Error fetching active users count"), 500

@app.route('/api/stats/projects', methods=['GET'])
@readonly_or_higher_required # Or a more specific permission if needed
def get_projects_count():
    try:
        count = Project.query.count()
        return jsonify(count=count), 200
    except Exception as e:
        app.logger.error(f"Error fetching projects count: {e}")
        return jsonify(message="Error fetching projects count"), 500

@app.route('/api/stats/parts', methods=['GET'])
@readonly_or_higher_required # Or a more specific permission if needed
def get_parts_count():
    try:
        count = Part.query.count()
        return jsonify(count=count), 200
    except Exception as e:
        app.logger.error(f"Error fetching parts count: {e}")
        return jsonify(message="Error fetching parts count"), 500

# Add more routes here based on NEW_README.md

# --- Order Routes ---

@app.route('/api/orders', methods=['POST'])
@jwt_required() # Any authenticated user can create an order
def create_order():
    # current_user_jwt = get_jwt_identity() # User identity can be used if order needs to be associated with user
    data = request.json
    required_fields = ['order_number', 'items']
    if not data or not all(field in data for field in required_fields):
        return jsonify(message=f"Error: Missing one or more required fields: {required_fields}"), 400

    if not isinstance(data['items'], list) or not data['items']:
        return jsonify(message="Error: 'items' must be a non-empty list"), 400

    # Basic validation for items
    for item_data in data['items']:
        if not all(k in item_data for k in ('part_id', 'quantity', 'unit_price')):
            return jsonify(message="Error: Each item must have part_id, quantity, and unit_price"), 400
        if not isinstance(item_data['quantity'], int) or item_data['quantity'] <= 0:
            return jsonify(message="Error: Item quantity must be a positive integer"), 400
        try:
            Decimal(str(item_data['unit_price'])) # Validate unit_price can be Decimal
        except:
            return jsonify(message="Error: Item unit_price must be a valid number"), 400


    # Check if project exists if project_id is provided
    project_id = data.get('project_id')
    if project_id:
        project = Project.query.get(project_id)
        if not project:
            return jsonify(message=f"Error: Project with id {project_id} not found"), 404
    
    # Calculate total_amount from items
    total_amount = sum(Decimal(str(item['unit_price'])) * item['quantity'] for item in data['items'])

    new_order = Order(
        order_number=data['order_number'],
        customer_name=data.get('customer_name'),
        project_id=project_id,
        status=data.get('status', 'Pending'), # Default status
        total_amount=total_amount,
        reimbursed=data.get('reimbursed', False)
    )
    db.session.add(new_order)
    # Must flush to get new_order.id for order items
    db.session.flush() 

    order_items_list = []
    for item_data in data['items']:
        part = Part.query.get(item_data['part_id'])
        if not part:
            db.session.rollback() # Rollback if any part is not found
            return jsonify(message=f"Error: Part with id {item_data['part_id']} not found"), 404
        
        order_item = OrderItem(
            order_id=new_order.id,
            part_id=item_data['part_id'],
            quantity=item_data['quantity'],
            unit_price=Decimal(str(item_data['unit_price']))
        )
        order_items_list.append(order_item)
        db.session.add(order_item)

    db.session.commit()

    # Prepare response
    order_data = {
        'id': new_order.id,
        'order_number': new_order.order_number,
        'customer_name': new_order.customer_name,
        'project_id': new_order.project_id,
        'status': new_order.status,
        'total_amount': str(new_order.total_amount), # Convert Decimal to string for JSON
        'order_date': new_order.order_date.isoformat(),
        'reimbursed': new_order.reimbursed,
        'created_at': new_order.created_at.isoformat(),
        'updated_at': new_order.updated_at.isoformat(),
        'items': [{
            'id': oi.id,
            'part_id': oi.part_id,
            'quantity': oi.quantity,
            'unit_price': str(oi.unit_price)
        } for oi in order_items_list]
    }
    return jsonify(message="Order created successfully", order=order_data), 201

@app.route('/api/orders', methods=['GET'])
@jwt_required()
def get_orders():
    current_user_jwt = get_jwt_identity()
    if not current_user_jwt['is_admin']:
        return jsonify(message="Forbidden: Admin access required to list all orders"), 403
    # TODO: Add filtering options (e.g., by project_id, status, customer_name)
    orders = Order.query.all()
    output = []
    for order in orders:
        order_data = {
            'id': order.id,
            'order_number': order.order_number,
            'customer_name': order.customer_name,
            'project_id': order.project_id,
            'status': order.status,
            'total_amount': str(order.total_amount),
            'order_date': order.order_date.isoformat(),
            'reimbursed': order.reimbursed,
            'created_at': order.created_at.isoformat(),
            'updated_at': order.updated_at.isoformat(),
            'items_count': len(order.items) # Optionally add count of items
        }
        output.append(order_data)
    return jsonify(orders=output)

@app.route('/api/orders/<int:order_id>', methods=['GET'])
@jwt_required() # Any authenticated user can view a specific order
def get_order(order_id):
    order = Order.query.get_or_404(order_id)
    order_data = {
        'id': order.id,
        'order_number': order.order_number,
        'customer_name': order.customer_name,
        'project_id': order.project_id,
        'status': order.status,
        'total_amount': str(order.total_amount),
        'order_date': order.order_date.isoformat(),
        'reimbursed': order.reimbursed,
        'created_at': order.created_at.isoformat(),
        'updated_at': order.updated_at.isoformat(),
        'items': [{
            'id': item.id,
            'part_id': item.part_id,
            'part_name': item.part.name, # Include part name for convenience
            'part_number': item.part.part_number, # Include part number
            'quantity': item.quantity,
            'unit_price': str(item.unit_price)
        } for item in order.items]
    }
    return jsonify(order=order_data)

@app.route('/api/orders/<int:order_id>', methods=['PUT'])
@jwt_required()
def update_order(order_id):
    current_user_jwt = get_jwt_identity()
    if not current_user_jwt['is_admin']:
        return jsonify(message="Forbidden: Admin access required"), 403
    order = Order.query.get_or_404(order_id)
    data = request.json
    if not data:
        return jsonify(message="Error: No input data provided"), 400

    # Update basic order fields
    order.order_number = data.get('order_number', order.order_number)
    order.customer_name = data.get('customer_name', order.customer_name)
    order.status = data.get('status', order.status)
    order.reimbursed = data.get('reimbursed', order.reimbursed)

    if 'project_id' in data:
        if data['project_id'] is None: # Allow unsetting project_id
             order.project_id = None
        else:
            project = Project.query.get(data['project_id'])
            if not project:
                return jsonify(message=f"Error: Project with id {data['project_id']} not found"), 404
            order.project_id = data['project_id']

    # Handling order items update is complex:
    # Options: 1. Replace all items, 2. Add/remove/update individual items.
    # For simplicity, this example will focus on updating the main order fields.
    # A more robust implementation would handle item changes carefully.
    # If 'items' are provided, it could mean replacing them.
    
    # Recalculate total_amount if items are modified or if total_amount is explicitly provided
    # For now, we assume total_amount is managed if items are managed separately or not changed here.
    # If items were being updated, total_amount would need recalculation.
    if 'total_amount' in data: # Allow manual override if necessary, though usually calculated
        try:
            order.total_amount = Decimal(str(data['total_amount']))
        except:
            return jsonify(message="Error: Invalid total_amount format"), 400
            
    db.session.commit()
    
    updated_order_data = {
        'id': order.id,
        'order_number': order.order_number,
        'customer_name': order.customer_name,
        'project_id': order.project_id,
        'status': order.status,
        'total_amount': str(order.total_amount),
        'order_date': order.order_date.isoformat(),
        'reimbursed': order.reimbursed,
        'updated_at': order.updated_at.isoformat()
        # Items are not returned here for simplicity, assuming they are managed via separate endpoints or not changed
    }
    return jsonify(message="Order updated successfully", order=updated_order_data)


@app.route('/api/orders/<int:order_id>', methods=['DELETE'])
@jwt_required()
def delete_order(order_id):
    current_user_jwt = get_jwt_identity()
    if not current_user_jwt['is_admin']:
        return jsonify(message="Forbidden: Admin access required"), 403
    order = Order.query.get_or_404(order_id)
    # OrderItems are deleted due to cascade="all, delete-orphan" in Order model
    db.session.delete(order)
    db.session.commit()
    return jsonify(message="Order and associated items deleted successfully")

# --- OrderItem Routes (Optional - for managing items of an existing order if needed) ---
# These might be useful if you want to add/remove/update items after an order is created.

@app.route('/api/orders/<int:order_id>/items', methods=['POST'])
@jwt_required()
def add_order_item(order_id):
    current_user_jwt = get_jwt_identity()
    # For now, only admin can add items to an order. Could be extended to order owner.
    if not current_user_jwt['is_admin']:
        return jsonify(message="Forbidden: Admin access required"), 403
    order = Order.query.get_or_404(order_id)
    data = request.json
    required_fields = ['part_id', 'quantity', 'unit_price']
    if not data or not all(field in data for field in required_fields):
        return jsonify(message=f"Error: Missing one or more required fields: {required_fields}"), 400

    part = Part.query.get(data['part_id'])
    if not part:
        return jsonify(message=f"Error: Part with id {data['part_id']} not found"), 404
    
    try:
        quantity = int(data['quantity'])
        unit_price = Decimal(str(data['unit_price']))
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
    except ValueError as e:
        return jsonify(message=f"Error: Invalid quantity or unit price. {e}"), 400

    new_item = OrderItem(
        order_id=order.id,
        part_id=data['part_id'],
        quantity=quantity,
        unit_price=unit_price
    )
    db.session.add(new_item)
    
    # Recalculate order total_amount
    order.total_amount = sum(Decimal(str(item.unit_price)) * item.quantity for item in order.items) + (unit_price * quantity)
    db.session.commit()

    item_data = {
        'id': new_item.id,
        'order_id': new_item.order_id,
        'part_id': new_item.part_id,
        'quantity': new_item.quantity,
        'unit_price': str(new_item.unit_price)
    }
    return jsonify(message="Order item added successfully", item=item_data, new_total_amount=str(order.total_amount)), 201

@app.route('/api/orders/<int:order_id>/items/<int:item_id>', methods=['PUT'])
@jwt_required()
def update_order_item(order_id, item_id):
    current_user_jwt = get_jwt_identity()
    # For now, only admin can update items in an order. Could be extended to order owner.
    if not current_user_jwt['is_admin']:
        return jsonify(message="Forbidden: Admin access required"), 403
    order = Order.query.get_or_404(order_id)
    item = OrderItem.query.filter_by(id=item_id, order_id=order.id).first_or_404()
    data = request.json
    if not data:
        return jsonify(message="Error: No input data provided"), 400

    original_item_total = item.unit_price * item.quantity

    if 'quantity' in data:
        try:
            item.quantity = int(data['quantity'])
            if item.quantity <= 0:
                return jsonify(message="Error: Quantity must be a positive integer"), 400
        except ValueError:
            return jsonify(message="Error: Invalid quantity format"), 400
            
    if 'unit_price' in data:
        try:
            item.unit_price = Decimal(str(data['unit_price']))
        except:
            return jsonify(message="Error: Invalid unit_price format"), 400
    
    # Recalculate order total_amount
    new_item_total = item.unit_price * item.quantity
    order.total_amount = (order.total_amount - original_item_total) + new_item_total
    
    db.session.commit()
    updated_item_data = {
        'id': item.id,
        'order_id': item.order_id,
        'part_id': item.part_id,
        'quantity': item.quantity,
        'unit_price': str(item.unit_price)
    }
    return jsonify(message="Order item updated successfully", item=updated_item_data, new_total_amount=str(order.total_amount))

@app.route('/api/orders/<int:order_id>/items/<int:item_id>', methods=['DELETE'])
@jwt_required()
def delete_order_item(order_id, item_id):
    current_user_jwt = get_jwt() # Corrected to get_jwt()
    # For now, only admin can delete items from an order. Could be extended to order owner.
    if current_user_jwt.get('permission') != 'admin': # Corrected to use get('permission')
        return jsonify(message="Forbidden: Admin access required"), 403
    order = Order.query.get_or_404(order_id)
    item = OrderItem.query.filter_by(id=item_id, order_id=order.id).first_or_404()
    
    item_total_to_remove = item.unit_price * item.quantity
    
    db.session.delete(item)
    
    # Recalculate order total_amount
    order.total_amount -= item_total_to_remove
    if order.total_amount < 0: # Should not happen with positive prices/quantities
        order.total_amount = Decimal('0.00')

    db.session.commit()
    return jsonify(message="Order item deleted successfully", new_total_amount=str(order.total_amount))

# --- Registration Link Routes ---

@app.route('/api/admin/registration-links', methods=['POST'])
@admin_required
def create_registration_link():
    data = request.json
    required_fields = ['max_uses', 'default_permission']
    if not data or not all(field in data for field in required_fields):
        return jsonify(message=f"Error: Missing one or more required fields: {required_fields}"), 400

    current_user_id = get_jwt().get('sub') # Get current admin user's ID

    try:
        new_link = RegistrationLink(
            created_by_user_id=current_user_id,
            custom_path=data.get('custom_path'), # Can be None
            max_uses=int(data['max_uses']),
            default_permission=data['default_permission'],
            auto_enable_new_users=data.get('auto_enable_new_users', False),
            fixed_username=data.get('fixed_username') if int(data['max_uses']) == 1 else None,
            fixed_email=data.get('fixed_email') if int(data['max_uses']) == 1 else None,
            is_active=data.get('is_active', True)
        )
        if data.get('expires_at'):
            new_link.expires_at = datetime.fromisoformat(data['expires_at'])

        db.session.add(new_link)
        db.session.commit()
        return jsonify(message="Registration link created successfully", link=new_link.to_dict()), 201
    except ValueError as e:
        db.session.rollback()
        return jsonify(message=f"Error creating link: {str(e)}"), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating registration link: {e}")
        return jsonify(message="Internal server error creating registration link."), 500

@app.route('/api/admin/registration-links', methods=['GET'])
@admin_required
def get_registration_links():
    links = RegistrationLink.query.all()
    return jsonify(links=[link.to_dict() for link in links])

@app.route('/api/admin/registration-links/<int:link_id>', methods=['GET'])
@admin_required
def get_registration_link(link_id):
    link = RegistrationLink.query.get_or_404(link_id)
    return jsonify(link=link.to_dict())

@app.route('/api/admin/registration-links/<int:link_id>', methods=['PUT'])
@admin_required
def update_registration_link(link_id):
    link = RegistrationLink.query.get_or_404(link_id)
    data = request.json

    try:
        if 'custom_path' in data: # Allow setting to None/empty to remove custom path
            link.custom_path = data['custom_path'] if data['custom_path'] else None
        if 'max_uses' in data:
            link.max_uses = int(data['max_uses'])
            if link.max_uses == 1:
                if 'fixed_username' in data: # Only apply if max_uses is 1
                    link.fixed_username = data.get('fixed_username')
                if 'fixed_email' in data: # Only apply if max_uses is 1
                    link.fixed_email = data.get('fixed_email')
            else: # If max_uses is not 1, clear fixed fields
                link.fixed_username = None
                link.fixed_email = None
        if 'expires_at' in data:
            link.expires_at = datetime.fromisoformat(data['expires_at']) if data['expires_at'] else None
        if 'default_permission' in data:
            link.default_permission = data['default_permission']
        if 'auto_enable_new_users' in data:
            link.auto_enable_new_users = data['auto_enable_new_users']
        if 'is_active' in data:
            link.is_active = data['is_active']
        
        # Prevent changing fixed_username/email if current_uses > 0 and max_uses == 1? (Consider implications)

        db.session.commit()
        return jsonify(message="Registration link updated successfully", link=link.to_dict())
    except ValueError as e:
        db.session.rollback()
        return jsonify(message=f"Error updating link: {str(e)}"), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating registration link {link_id}: {e}")
        return jsonify(message="Internal server error updating registration link."), 500

@app.route('/api/admin/registration-links/<int:link_id>', methods=['DELETE'])
@admin_required
def delete_registration_link(link_id):
    link = RegistrationLink.query.get_or_404(link_id)
    # Instead of deleting, we can mark as inactive, or actually delete.
    # For now, let's make it inactive. A true delete might be another endpoint or flag.
    # link.is_active = False 
    # db.session.commit()
    # return jsonify(message="Registration link deactivated successfully.")
    try:
        db.session.delete(link)
        db.session.commit()
        return jsonify(message="Registration link deleted successfully.")
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting registration link {link_id}: {e}")
        return jsonify(message="Internal server error deleting registration link."), 500

@app.route('/api/register/<link_identifier>', methods=['GET'])
def get_registration_link_details(link_identifier):
    app.logger.info(f"PUBLIC_LINK_FETCH: Attempting to fetch link with identifier: {link_identifier}")
    link = RegistrationLink.query.filter(
        (RegistrationLink.token == link_identifier) | (RegistrationLink.custom_path == link_identifier)
    ).first()

    if not link:
        app.logger.warning(f"PUBLIC_LINK_FETCH: Link not found for identifier: {link_identifier}")
        return jsonify(message="Registration link not found."), 404
    
    app.logger.info(f"PUBLIC_LINK_FETCH: Link found (ID: {link.id}): "
                    f"Active: {link.is_active}, "
                    f"Expires: {link.expires_at}, "
                    f"Uses: {link.current_uses}/{link.max_uses}, "
                    f"FixedUser: {link.fixed_username}, FixedEmail: {link.fixed_email}")

    # Corrected method call here
    is_valid_bool, validity_message_str = link.is_currently_valid_for_registration()
    app.logger.info(f"PUBLIC_LINK_FETCH: Validity check for link ID {link.id}: is_valid={is_valid_bool}, message='{validity_message_str}'")

    if not is_valid_bool:
        response_payload = {"message": validity_message_str, "is_currently_valid": False}
        app.logger.warning(f"PUBLIC_LINK_FETCH: Link ID {link.id} is invalid. Returning: {response_payload}")
        return jsonify(response_payload), 200

    # If link is valid
    response_payload = {
        "link_identifier": link.effective_link_path_segment, # Changed to use the property
        "custom_path": link.custom_path,
        "max_uses": link.max_uses,
        "current_uses": link.current_uses,
        "expires_at": link.expires_at.isoformat() if link.expires_at else None,
        "default_permission": link.default_permission,
        "auto_enable_new_users": link.auto_enable_new_users,
        "fixed_username": link.fixed_username,
        "fixed_email": link.fixed_email,
        "is_active": link.is_active,
        "is_currently_valid": True, # Explicitly true here
        "message": "Link details fetched successfully."
    }
    app.logger.info(f"PUBLIC_LINK_FETCH: Link ID {link.id} is valid. Returning: {response_payload}")
    return jsonify(response_payload), 200

@app.route('/api/register/<link_identifier>', methods=['POST'])
def register_user_via_link(link_identifier):
    link = RegistrationLink.query.filter(
        (RegistrationLink.token == link_identifier) | (RegistrationLink.custom_path == link_identifier)
    ).first()

    if not link:
        return jsonify(message="Registration link not found."), 404
    
    if not link.is_currently_valid_for_registration():
        return jsonify(message="Registration link is invalid, expired, or has reached its maximum uses."), 403

    data = request.json
    required_fields = ['password', 'first_name', 'last_name']
    # Username and email might be fixed by the link
    if not link.fixed_username:
        required_fields.append('username')
    if not link.fixed_email:
        required_fields.append('email')
        
    if not data or not all(field in data for field in required_fields):
        missing = [field for field in required_fields if field not in data]
        return jsonify(message=f"Error: Missing one or more required fields: {', '.join(missing)}"), 400

    username = link.fixed_username if link.fixed_username else data['username']
    email = link.fixed_email if link.fixed_email else data['email']

    if User.query.filter_by(username=username).first():
        return jsonify(message="Error: Username already exists"), 409
    if User.query.filter_by(email=email).first(): # Corrected this line
        return jsonify(message="Error: Email already exists"), 409

    try:
        new_user = User(
            username=username,
            email=email,
            first_name=data['first_name'],
            last_name=data['last_name'],
            permission=link.default_permission,
            enabled=link.auto_enable_new_users,
            is_approved=link.auto_enable_new_users # If auto-enabled, assume also auto-approved by the link's nature
        )
        new_user.set_password(data['password'])
        
        link.current_uses += 1
        if link.max_uses != -1 and link.current_uses >= link.max_uses:
            link.is_active = False # Deactivate link if max uses reached

        db.session.add(new_user)
        db.session.add(link) # To save changes to current_uses and is_active
        db.session.commit()
        
        user_data = {
            'id': new_user.id,
            'username': new_user.username,
            'email': new_user.email,
            'first_name': new_user.first_name,
            'last_name': new_user.last_name,
            'permission': new_user.permission,
            'enabled': new_user.enabled,
            'is_approved': new_user.is_approved,
            'created_at': new_user.created_at.isoformat()
        }
        # Do not return a token here unless the user is also auto-logged-in
        return jsonify(message="User registered successfully via link.", user=user_data), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error registering user via link {link_identifier}: {e}")
        return jsonify(message="Internal server error during registration."), 500
