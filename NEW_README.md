# Bronco Parts (Modernized)

This document outlines the features and technical details of the Bronco Parts application, a system for tracking parts through the design, manufacturing, and ordering lifecycle. This new version aims to modernize the original "Cheesy Parts" application.

## Core Functionalities

### 1. Part Tracking & Management

- **Unique Part Numbering:** The system generates a `full_part_number` for each part. The format is: `{ProjectNumberPrefix}-{TypeIndicator}-{NumericId}`.
    - `{ProjectNumberPrefix}`: Defined at the Project level (e.g., "BP25").
    - `{TypeIndicator}`: "A" for Assembly, "P" for Part.
    - `{NumericId}`: A zero-padded 4-digit number.
        - For `part` type: Increments from the parent assembly's `part_number` (or 0 if no parent). E.g., if parent assembly is `XXX-A-0100`, its first part will be `XXX-P-0101`.
        - For `assembly` type: Increments in steps of 100 from the highest existing assembly `part_number` in the project (or starts at 0, then 100, 200, etc.).
- **Lifecycle Tracking:** Monitors parts through various stages. Each status is a string stored in the database, with a more user-friendly display name.
    - `designing`: "Design in progress"
    - `material`: "Material needs to be ordered"
    - `ordered`: "Waiting for materials"
    - `drawing`: "Needs drawing"
    - `ready`: "Ready to manufacture"
    - `cnc`: "Ready for CNC"
    - `laser`: "Ready for laser"
    - `lathe`: "Ready for lathe"
    - `mill`: "Ready for mill"
    - `printer`: "Ready for 3D printer"
    - `router`: "Ready for router"
    - `manufacturing`: "Manufacturing in progress"
    - `outsourced`: "Waiting for outsourced manufacturing"
    - `welding`: "Waiting for welding"
    - `scotchbrite`: "Waiting for Scotch-Brite" (surface finishing)
    - `anodize`: "Ready for anodize"
    - `powder`: "Ready for powder coating"
    - `coating`: "Waiting for coating" (other generic coating)
    - `assembly`: "Waiting for assembly"
    - `done`: "Done"
- **Detailed Part Information:**
    - `name`: Descriptive name of the part (HTML characters like `"` are escaped to `&quot;`).
    - `type`: Category of the part. Stored as "part" or "assembly".
    - `parent_part_id`: Foreign key linking to another `Part` record if it's a sub-component of an assembly. Assemblies themselves do not have a `parent_part_id` (or it's 0/null).
    - `status`: Current stage in the lifecycle (see above list). Default for new parts is "designing".
    - `notes`: General textual notes about the part.
    - `source_material`: Description of the raw material (e.g., "6061 Aluminum 1/4\\" plate"). Default is empty string.
    - `have_material`: Boolean (0 or 1) indicating if the required material is on hand. Default is 0 (false).
    - `quantity`: Number of units required. Can be a string to accommodate non-standard quantities (e.g., "As needed", "1 set"). Default is empty string.
    - `cut_length`: Specific length for materials that are cut from stock (e.g., "100mm"). Default is empty string.
    - `priority`: Numerical priority. Stored as 0 (High), 1 (Normal), 2 (Low). Default is 1.
    - `drawing_created`: Boolean (0 or 1) indicating if a manufacturing drawing exists and is finalized. Default is 0 (false).
- **CRUD Operations:** Allows users with `editor` or `admin` permissions to create, view, edit, and delete parts. Deletion of an assembly is prevented if it has child parts.
- **Project Association:** All parts must belong to a "Project."

### 2. Project Management

- **Project Creation:** Users with `editor` or `admin` permissions can define new projects.
- **Project Attributes:**
    - `name`: Name of the project (e.g., "2025 Robot Drivetrain").
    - `part_number_prefix`: A short string code used as the base for generating `full_part_number`s within this project (e.g., "BP25").
    - `hide_dashboards`: A boolean (0 or 1) flag to control visibility of the project on main dashboard views. Default is `false` (0).
- **CRUD Operations:** Allows `editor` or `admin` users to create, view, edit, and delete projects.

### 3. User Management & Authentication

- **User Accounts:**
    - Registration: New users can register. Accounts are created as `disabled` (`enabled = 0`) and `readonly` by default, pending administrator approval.
    - Login: Authenticates using email and password. Supports redirection after login.
    - Optional WordPress SSO: Can be configured to authenticate against a WordPress user database (Team 254 specific).
- **Password Security:**
    - Uses PBKDF2 with HMAC-SHA1 for password hashing.
    - `PBKDF2_ITERATIONS = 1000`
    - `HASH_BYTES = 24`
    - `SALT_BYTES = 24` (salt is Base64 encoded)
    - Users can change their own passwords after providing their old password.
- **Role-Based Access Control (RBAC):** Permissions are stored as strings.
    - `readonly`: "Read-only" - Can view data.
    - `editor`: "Editor" - Can create/edit projects, parts, orders.
    - `admin`: "Administrator" - Full control, including user management.
- **Account Management:** Administrators (`admin` role) can:
    - View all users.
    - Create new users with specified permissions and enabled status.
    - Edit existing users (email, name, password, permission, enabled status).
    - Delete users.
- **Email Notifications:** Uses Pony library via Gmail SMTP for sending emails.
    - When a new user registers, an email is sent to the admin (defined by `CheesyCommon::Config.gmail_user`) for approval.
    - When an admin approves/enables a user account, an email is sent to the user.
    - Configuration for email (`gmail_user`, `gmail_password`) is in `config.json`.

### 4. Order Management

- **Procurement Tracking:** Manages orders for parts/materials from external vendors.
- **Order Association:** Orders are linked to a specific `Project`.
- **Order Status:**
    - `open`: "Open" - Order is being drafted, items can be added/modified.
    - `ordered`: "Ordered" - Order has been placed with the vendor.
    - `received`: "Received" - All items in the order have been received.
- **Vendor Information:** `vendor_name` is stored directly on the `Order` record. If an `OrderItem` is added with a vendor, and an "open" order for that project and vendor doesn't exist, a new `Order` is created.
- **Order Line Items (`OrderItem`):**
    - `quantity`: Integer, number of units for the line item.
    - `part_number`: String, vendor's part number or internal identifier.
    - `description`: String, detailed description of the item.
    - `unit_cost`: Float, cost per unit. Dollar signs are stripped on input.
    - `notes`: Text, additional notes.
    - `total_cost`: Calculated as `unit_cost * quantity`.
- **Financial Tracking (on `Order`):**
    - `subtotal`: Calculated sum of `total_cost` for all `OrderItem`s in the order.
    - `tax_cost`: Float, applicable taxes. Dollar signs stripped on input.
    - `shipping_cost`: Float, shipping charges. Dollar signs stripped on input.
    - `total_cost`: Calculated as `subtotal + tax_cost + shipping_cost`.
    - `paid_for_by`: String, tracks who made the payment.
    - `reimbursed`: Boolean (0 or 1), indicates if the payer has been reimbursed.
    - `ordered_at`: Date/Timestamp, when the order was placed.
- **CRUD Operations:** Users with `editor` or `admin` permissions can:
    - Create new `OrderItem`s (which may create a new `Order`).
    - Edit `OrderItem`s (can change vendor, which might move item to a different order or create a new one).
    - Delete `OrderItem`s.
    - Edit `Order` details (status, dates, financial info, notes).
    - Delete `Order`s (only if they contain no `OrderItem`s).
- **Reporting/Views:**
    - Lists of orders filtered by status (open, ordered, received/complete) per project.
    - "All orders" view with optional filtering.
    - Order statistics: Aggregates spending by vendor and by purchaser (showing reimbursed vs. outstanding amounts).

### 5. Dashboards

- **Overall Dashboards View (`/dashboards`):** Lists all projects (that don't have `hide_dashboards=true`) with a link to their individual dashboards.
- **Project-Specific Dashboard (`/projects/:id/dashboard`):** Provides a visual summary of parts for a specific project, typically showing counts of parts by status.
- **Dashboard Parts View (`/projects/:id/dashboard/parts`):** A more detailed view, potentially filterable by part `status`.

## Application Structure & Key Files

- **`parts_server.rb`:** The main Sinatra application file.
    - Defines all routes (HTTP GET/POST handlers).
    - Manages session cookies (`Rack::Session::Cookie`).
    - Enforces authentication for most routes.
    - Contains helper methods for permission checks and sending emails.
    - Renders ERB templates from the `views/` directory.
- **`models/` directory:** Contains Sequel model definitions.
    - **`part.rb`:** Defines the `Part` model, its relationships (to `Project`, self for assemblies), part types, status map, priority map, and the `generate_number_and_create` method for part numbering logic. Includes `full_part_number` formatting.
    - **`project.rb`:** Defines the `Project` model and its relationships (to `Part`, `Order`).
    - **`user.rb`:** Defines the `User` model, password authentication logic (`authenticate`, `set_password`), permission checks (`can_edit?`, `can_administer?`), and permission map.
    - **`order.rb`:** Defines the `Order` model, relationships, status map, and calculated financial properties (`subtotal`, `total_cost`).
    - **`order_item.rb`:** Defines the `OrderItem` model, relationships, and calculated `total_cost`.
- **`db.rb`:** Sets up the Sequel database connection using credentials from `config.json` (via `CheesyCommon::Config`).
- **`config.json`:** Configuration file.
    - `global`: Common settings like database host/user/name, server port, base URL, Gmail user, and feature flags (`enable_wordpress_auth`, `hide_unused_fields`).
    - `dev`, `prod`: Environment-specific settings like database passwords, Gmail passwords, and WordPress members URL. Passwords can be encrypted.
- **`Rakefile`:** Contains Rake tasks, primarily for database migrations (`db:migrate`).
- **`db/migrations/`:** Contains Sequel migration files for schema changes. Each file represents an incremental change to the database structure.
- **`views/` directory:** Contains ERB templates for rendering HTML pages.
    - `layout.erb` (implicitly, or `header.erb`/`footer.erb` act as such): Defines the main page structure.
    - Specific views for each resource and action (e.g., `projects.erb`, `part_edit.erb`, `new_order_item.erb`).
- **`public/` directory:** Contains static assets.
    - `css/`: Stylesheets (Bootstrap, custom `css.css`).
    - `js/`: JavaScript files (jQuery, Bootstrap JS, custom `js.js`).
    - `img/`: Image assets (e.g., glyphicons).
- **`Gemfile` & `Gemfile.lock`:** Manage Ruby gem dependencies (e.g., sinatra, sequel, mysql2, pony, eventmachine).
- **`parts_server_control.rb`:** A script to control the running of the Sinatra server (start, stop, run, restart). Likely uses `Process.daemon` for backgrounding.

## Technical Details (Original Application for Reference)

- **Backend Framework:** Ruby with Sinatra (a DSL for quickly creating web applications in Ruby with minimal effort).
- **Database:** MySQL (connected via `mysql2` gem).
- **Data Access/ORM:** Sequel (a lightweight database toolkit for Ruby).
- **Schema Management:** Database migrations managed by `rake` tasks and Sequel's migration system.
- **Frontend Templating:** ERB (Embedded Ruby), standard in Ruby web development for embedding Ruby code within HTML.
- **Styling:** CSS, with an older version of Bootstrap for base styling and components. Custom styles in `public/css/css.css`.
- **Client-Side Scripting:** JavaScript, primarily using jQuery for DOM manipulation and AJAX, and Bootstrap JavaScript components. Custom logic in `public/js/js.js`.
- **Email:** Pony library for sending emails, configured for Gmail SMTP. Email sending is deferred to a background thread using `EventMachine` to prevent blocking web requests.
- **Session Management:** `Rack::Session::Cookie` for storing session data (like `user_id`) in a client-side cookie.
- **Concurrency (for email):** `EventMachine` is used to run email sending operations asynchronously.
- **Configuration:** `config.json` parsed by `CheesyCommon::Config` (likely a custom utility library, not detailed here but its role is to provide access to config values).

## Data Models (Conceptual for New Build - Reflecting Original Schema)

This section outlines the primary data entities and their key attributes as implemented in the original application.

### `Project` (Table: `projects`)

- `id`: Integer, Primary Key, Auto-incrementing.
- `name`: String, required.
- `part_number_prefix`: String, required, unique.
- `hide_dashboards`: Integer (0 or 1), default: 0.
- *Relationships: Has many `Part`s, Has many `Order`s.*

### `Part` (Table: `parts`)

- `id`: Integer, Primary Key, Auto-incrementing.
- `project_id`: Integer, Foreign Key to `projects.id`, required.
- `part_number`: Integer, used in generation logic, see "Unique Part Numbering".
- `type`: String, required (e.g., "part", "assembly").
- `parent_part_id`: Integer, Foreign Key to `parts.id` (self-referential), nullable (or 0).
- `name`: String, required.
- `status`: String, required, (e.g., "designing").
- `notes`: Text, nullable.
- `source_material`: String, nullable.
- `have_material`: Integer (0 or 1), default: 0.
- `quantity`: String, nullable.
- `cut_length`: String, nullable.
- `priority`: Integer, default: 1.
- `drawing_created`: Integer (0 or 1), default: 0.
- *Timestamps (created_at, updated_at) are typically managed by Sequel if columns exist, but not explicitly listed in provided model code.*
- *Relationships: Belongs to `Project`, Belongs to `Part` (as child), Has many `Part`s (as parent).*

### `User` (Table: `users`)

- `id`: Integer, Primary Key, Auto-incrementing.
- `email`: String, required, unique.
- `first_name`: String, required.
- `last_name`: String, required.
- `password`: String (stores Base64 encoded PBKDF2 hash).
- `salt`: String (stores Base64 encoded salt).
- `permission`: String, required (e.g., "readonly", "editor", "admin").
- `enabled`: Integer (0 or 1), default: 1 (or 0 for new registrations).
- `wordpress_user_id`: Integer, nullable (for SSO).
- *Timestamps likely exist.*

### `Order` (Table: `orders`)

- `id`: Integer, Primary Key, Auto-incrementing.
- `project_id`: Integer, Foreign Key to `projects.id`, required.
- `vendor_name`: String, nullable.
- `status`: String, required (e.g., "open", "ordered", "received").
- `ordered_at`: Timestamp, nullable.
- `paid_for_by`: String, nullable.
- `tax_cost`: Decimal/Float, default: 0.0.
- `shipping_cost`: Decimal/Float, default: 0.0.
- `notes`: Text, nullable.
- `reimbursed`: Integer (0 or 1), default: 0.
- *Timestamps likely exist.*
- *Relationships: Belongs to `Project`, Has many `OrderItem`s.*

### `OrderItem` (Table: `order_items`)

- `id`: Integer, Primary Key, Auto-incrementing.
- `order_id`: Integer, Foreign Key to `orders.id`, nullable (items can exist before being assigned to a specific vendor order).
- `project_id`: Integer, Foreign Key to `projects.id` (denormalized).
- `quantity`: Integer, required, default: 1.
- `part_number`: String, nullable (vendor's part number).
- `description`: String, required.
- `unit_cost`: Decimal/Float, required, default: 0.0.
- `notes`: Text, nullable.
- *Timestamps likely exist.*
- *Relationships: Belongs to `Order`, Belongs to `Project`.*

## Modernization Goals & Tech Stack Choices (To Be Determined)

- **Backend Framework:** [e.g., Node.js with Express/NestJS, Python with Django/Flask, Ruby on Rails, Go with Gin]
- **Frontend Framework:** [e.g., React, Vue, Angular, Svelte, possibly with TypeScript]
- **Database:** [e.g., PostgreSQL, MySQL, MongoDB]
- **UI/CSS Framework:** [e.g., Tailwind CSS, Material UI, Bootstrap 5]
- **API Style:** [e.g., RESTful, GraphQL]

This `NEW_README.md` provides a comprehensive overview. We can refine it as we make decisions about the new tech stack and architecture.


