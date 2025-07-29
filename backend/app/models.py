from . import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import datetime
from sqlalchemy.orm import validates

# Association table for Part and PostProcess
# Ensure db.Table is used if Table is not directly imported from sqlalchemy
part_post_processes = db.Table('part_post_processes', db.Model.metadata,
    db.Column('part_id', db.Integer, db.ForeignKey('parts.id'), primary_key=True),
    db.Column('post_process_id', db.Integer, db.ForeignKey('post_processes.id'), primary_key=True)
)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    permission = db.Column(db.String(50), nullable=False, default='readonly')  # Replaces is_admin
    enabled = db.Column(db.Boolean, nullable=False, default=False)  # New users default to disabled
    is_approved = db.Column(db.Boolean, nullable=False, default=False) # For account approval
    requested_at = db.Column(db.DateTime, default=datetime.datetime.utcnow) # For tracking approval request time
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    registered_via_link_id = db.Column(db.Integer, db.ForeignKey('registration_links.id'), nullable=True)  # Link used for registration

    # Relationships
    registration_link = db.relationship('RegistrationLink', foreign_keys=[registered_via_link_id], backref=db.backref('registered_users', lazy='dynamic'))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'permission': self.permission,
            'enabled': self.enabled,
            'is_approved': self.is_approved,
            'requested_at': self.requested_at.isoformat() if self.requested_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'registered_via_link_id': self.registered_via_link_id
        }

    def __repr__(self):
        return f'<User {self.username} ({self.permission}){" Enabled" if self.enabled else " Disabled"}{" Approved" if self.is_approved else " Pending Approval"}>'

class RegistrationLink(db.Model):
    __tablename__ = 'registration_links'

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False, default=lambda: secrets.token_urlsafe(32))
    custom_path = db.Column(db.String(100), unique=True, nullable=True)  # User-defined part of the URL
    
    max_uses = db.Column(db.Integer, nullable=False, default=1)  # How many accounts can be created. -1 for unlimited.
    current_uses = db.Column(db.Integer, nullable=False, default=0)
    
    expires_at = db.Column(db.DateTime, nullable=True)  # Optional expiration date for the link
    
    # Default settings for accounts created via this link
    default_permission = db.Column(db.String(50), nullable=False, default='viewer') # e.g., 'viewer', 'editor'
    auto_enable_new_users = db.Column(db.Boolean, nullable=False, default=False) # Accounts enabled/disabled by default
    
    # For single-use links (max_uses == 1) with pre-defined user details
    fixed_username = db.Column(db.String(80), nullable=True)
    fixed_email = db.Column(db.String(120), nullable=True)
    
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True) # To manually disable/enable a link

    creator = db.relationship('User', foreign_keys=[created_by_user_id], backref=db.backref('created_registration_links', lazy='dynamic'))

    @validates('custom_path')
    def validate_custom_path(self, key, custom_path):
        if custom_path:
            if not custom_path.isalnum() and '_' not in custom_path and '-' not in custom_path:
                raise ValueError("Custom path can only contain alphanumeric characters, underscores, and hyphens.")
            # Check for uniqueness against other active links if it's being set/changed
            # Ensure self.id exists for updates, otherwise it's a new record
            query = RegistrationLink.query.filter(RegistrationLink.custom_path == custom_path, RegistrationLink.is_active == True)
            if hasattr(self, 'id') and self.id is not None:
                query = query.filter(RegistrationLink.id != self.id)
            existing = query.first()
            if existing:
                raise ValueError(f"Custom path '{custom_path}' is already in use by an active link.")
        return custom_path

    @property
    def effective_link_path_segment(self):
        """The part of the URL that identifies this link, to be used like /register/link/{this_value}"""
        return self.custom_path if self.custom_path else self.token

    def is_currently_valid_for_registration(self):
        """Checks if the link can be used for a new registration right now. Returns (bool, message_string)."""
        if not self.is_active:
            return False, "Link is not active."
        if self.expires_at and datetime.datetime.utcnow() > self.expires_at:
            return False, "Link has expired."
        if self.max_uses != -1 and self.current_uses >= self.max_uses: # -1 means unlimited
            return False, "Link has reached its maximum number of uses."
        return True, "Link is valid for registration."

    def to_dict(self):
        return {
            'id': self.id,
            'token': self.token, # Internal token
            'link_identifier': self.effective_link_path_segment, # Used in public URL
            'custom_path': self.custom_path,
            'max_uses': self.max_uses,
            'current_uses': self.current_uses,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'default_permission': self.default_permission,
            'auto_enable_new_users': self.auto_enable_new_users,
            'fixed_username': self.fixed_username,
            'fixed_email': self.fixed_email,
            'created_by_user_id': self.created_by_user_id,
            'creator_username': self.creator.username if self.creator else None, # Added for convenience
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active,
            'is_currently_valid': self.is_currently_valid_for_registration() # Dynamic status
        }

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    prefix = db.Column(db.String(10), unique=True) # Assuming prefix should be unique
    onshape_document_id = db.Column(db.String(64), nullable=True)
    onshape_workspace_id = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    hide_dashboards = db.Column(db.Boolean, default=False)
    
    parts = db.relationship('Part', backref='project', lazy=True)
    orders = db.relationship('Order', backref='project', lazy=True)

    def __repr__(self):
        return f'<Project {self.name}>'

class Machine(db.Model):
    __tablename__ = 'machines'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<Machine {self.name}>'

class PostProcess(db.Model):
    __tablename__ = 'post_processes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<PostProcess {self.name}>'

class Part(db.Model):
    __tablename__ = 'parts'
    id = db.Column(db.Integer, primary_key=True)
    
    # Fields for generated part number
    numeric_id = db.Column(db.Integer, nullable=False) # Stores the numeric part of the ID, e.g., 100, 101
    part_number = db.Column(db.String(50), unique=True, nullable=False) # Stores the full generated part number, e.g., BP25-A-0100

    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    material = db.Column(db.String(50)) # Existing material field, potentially for CAD material.
    revision = db.Column(db.String(10))
    status = db.Column(db.String(50), nullable=False, default="in design") # Updated as per new reqs
    quantity_on_hand = db.Column(db.Integer, default=0)
    quantity_on_order = db.Column(db.Integer, default=0)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    
    # Type and hierarchy for part numbering
    type = db.Column(db.String(10), nullable=False)  # 'assembly' or 'part'
    parent_id = db.Column(db.Integer, db.ForeignKey('parts.id'), nullable=True)
    children = db.relationship('Part',
                               foreign_keys=[parent_id], # Specify the foreign key for the self-referential relationship
                               backref=db.backref('parent', remote_side=[id]),
                               lazy='dynamic')

    # New fields from NEW_README.md / PROJECT_PLAN.md
    notes = db.Column(db.Text, nullable=True)
    source_material = db.Column(db.String(255), nullable=True, default='')
    have_material = db.Column(db.Boolean, default=False, nullable=False)
    quantity_required = db.Column(db.String(50), nullable=True, default='') # e.g., "As needed", "1 set"
    cut_length = db.Column(db.String(50), nullable=True, default='')
    priority = db.Column(db.Integer, default=1, nullable=False) # 0=High, 1=Normal, 2=Low
    drawing_created = db.Column(db.Boolean, default=False, nullable=False)

    # New fields from feature_part_creation_enhancements.md
    quantity = db.Column(db.Integer, nullable=False) # Manufacturing quantity
    raw_material = db.Column(db.String(255), nullable=True) # Custom text for raw material - Made nullable

    machine_id = db.Column(db.Integer, db.ForeignKey('machines.id'), nullable=True) # FK to Machine table
    machine = db.relationship('Machine', backref=db.backref('parts', lazy='dynamic'))

    post_processes = db.relationship('PostProcess', secondary=part_post_processes,
                                     lazy='subquery', backref=db.backref('parts', lazy=True))

    subteam_id = db.Column(db.Integer, db.ForeignKey('parts.id'), nullable=True)
    subsystem_id = db.Column(db.Integer, db.ForeignKey('parts.id'), nullable=True)

    # Relationships for subteam and subsystem (self-referential to Part)
    # Using primaryjoin to be explicit for self-referential FKs
    subteam = db.relationship('Part', foreign_keys=[subteam_id], remote_side=[id], backref='part_subteams', lazy='joined')
    subsystem = db.relationship('Part', foreign_keys=[subsystem_id], remote_side=[id], backref='part_subsystems', lazy='joined')


    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    order_items = db.relationship('OrderItem', backref='part', lazy=True)

    # Ensure uniqueness for project_id and numeric_id combination
    __table_args__ = (db.UniqueConstraint('project_id', 'numeric_id', name='_project_numeric_uc'),)

    def __repr__(self):
        return f'<Part {self.part_number} Prio:{self.priority} Mat:{self.have_material}>'

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_name = db.Column(db.String(100)) # Or could be a ForeignKey to a Customer table if needed
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True) # Nullable if orders can be general
    status = db.Column(db.String(50)) # E.g., 'Pending', 'Processing', 'Shipped', 'Completed', 'Cancelled'
    total_amount = db.Column(db.Numeric(10, 2)) # Assuming a decimal for currency
    order_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    reimbursed = db.Column(db.Boolean, default=False)

    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Order {self.order_number}>'

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    part_id = db.Column(db.Integer, db.ForeignKey('parts.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False) # Price at the time of order
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<OrderItem OrderID:{self.order_id} PartID:{self.part_id} Qty:{self.quantity}>'
