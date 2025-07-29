```
           ,                        '           .        '        ,  
   .            .        '       .         ,         
                                                   .       '     +
       +          .-'''''-.     
                .'         `.   +     .     ________||
       ___     :             :     |       /        ||  .     '___
  ____/   \   :               :   ||.    _/      || ||\_______/   \
 /         \  :      _/|      :   `|| __/      ,.|| ||             \
/  ,   '  . \  :   =/_/      :     |'_______     || ||  ||   .      \
    |        \__`._/ |     .'   ___|        \__   \\||  ||...    ,   \
   l|,   '   (   /  ,|...-'        \   '   ,     __\||_//___          
 ___|____     \_/^\/||__    ,    .  ,__             ||//    \    .  ,
           _/~  `""~`"` \_           ''(       ....,||/       '   
 ..,...  __/  -'/  `-._ `\_\__        | \           ||  _______   .
   itz/jgs/ccm'`  `\   \  \-.\        /(_1_,..      || /
                                            ______/""""
```                                           





# Bronco Parts
Modern parts management tool for engineering teams and projects. Fully integrated with Airtable and with built in user management. 


## Features

- **Project, Part, and Assembly Management:**
  - Create, update, and organize projects, assemblies, and parts with hierarchical relationships.
  - Automatic part numbering and hierarchy-aware metadata (subteam, subsystem, etc).
  - Super cool tree view.
- **Order and Inventory Tracking:**
  - Manage orders, order items, and track part inventory and status.
  - Database and forms have the ability for this - not implemented fully right now.
- **User Management & Permissions:**
  - Role-based access (admin, editor, readonly, etc).
  - Registration links for controlled onboarding (single-use, multi-use, with fixed or user-supplied credentials).
- **Airtable Integration:**
  - Sync parts and assemblies to Airtable.
  - Add new options to Airtable single-select fields programmatically.
  - See code or contact maintainer for example Airtable setup.
- **Machine & Post-Process Management:**
  - Track machines, post-processes, and associate them with parts.
- **REST API:**
  - Modern Flask-based API for all operations, with JWT authentication and role checks.
- **Frontend:**
  - React-based frontend (see `frontend/`) for user interaction.

## Use Cases

- University or professional engineering teams managing hardware projects.
- Manufacturing teams tracking part fabrication, post-processing, and inventory.
- Organizations needing controlled, auditable user onboarding and permissions.
- Teams that want to sync engineering data with Airtable for reporting or collaboration.
- Anyone that wants to organize their projects that contain lots of small parts. 

## Project Structure

- `backend/` — Flask API, database models, migrations, and integration logic.
- `frontend/` — React app for user interface.
- `docker-compose.yml` — Multi-container orchestration for local/prod deployment.
- `testing/` — Scripts for integration with Airtable and test automation.
- `migrations/` — Alembic migrations for database schema management.
- `tests/` — Automated tests (pytest). *IN PROGRESS\*

## How It Works

- The backend exposes a REST API for all resources (projects, parts, users, orders, etc).
- User authentication is via JWT, with role-based decorators for access control.
- Registration links allow admins to invite users with specific permissions and onboarding flows.
- Parts and assemblies can be synced to Airtable, and new options can be added to Airtable fields via the API.
- The frontend consumes the API and provides a modern UI for all operations.

## Running the Project

### Prerequisites
- Docker and Docker Compose
- (Optional) Python 3.11+ and Node.js if running backend/frontend outside Docker

### Quick Start (Recommended)

1. **Clone the repository:**
   ```sh
   git clone <your-repo-url>
   cd BroncoPartsV2
   ```
2. **Set environment variables:**
   - Copy `.env.example` to `.env` and fill in secrets (DB, JWT, Airtable keys, etc).
   - Or set variables in your shell or Docker Compose override.
3. **Start all services:**
   ```sh
   docker-compose up --build
   ```
   This will start MySQL, the Flask backend, and the React frontend.
4. **Access the app:**
   - Frontend: [http://localhost:8080](http://localhost:8080)
   - Backend API: [http://localhost:8000/api](http://localhost:8000/api)
   - MySQL: localhost:3306 (see docker-compose for credentials)

### Running Backend Only (Dev)

1. Install Python dependencies:
   ```sh
   cd backend
   pip install -r requirements.txt
   ```
2. Set environment variables (see above).
3. Run database migrations:
   ```sh
   alembic upgrade head
   ```
4. Start the backend:
   ```sh
   flask run
   ```

### Running Frontend Only (Dev)

1. Install Node dependencies:
   ```sh
   cd frontend
   npm install
   ```
2. Start the frontend:
   ```sh
   npm start
   ```

## Airtable Integration
- Configure your Airtable API key, base ID, and table ID in environment variables or the relevant scripts.
- Use scripts in `backend/testing/` to test Airtable sync and option creation.

## Onshape Integration
BroncoParts can automatically number new parts created in Onshape. Configure each project's document and workspace IDs plus OAuth credentials via the new **Onshape Settings** page. When the Onshape webhook fires, the backend assigns a part number using the project's naming scheme and stores it in the Onshape part metadata and in BroncoParts.

## Testing
- Run backend tests with:
  ```sh
  cd backend
  pytest
  ```
- See `testing/` for integration scripts and test helpers.

## Security Notes
- Change all default passwords and secrets before deploying to production.
- Use HTTPS and secure your environment variables.

## License
This project abides by the MIT License. 

---
For more details, see the code and comments in each directory, or contact the project maintainer.

```
           ,                        '           .        '        ,  
   .            .        '       .         ,         
                                                   .       '     +
       +          .-'''''-.     
                .'         `.   +     .     ________||
       ___     :             :     |       /        ||  .     '___
  ____/   \   :               :   ||.    _/      || ||\_______/   \
 /         \  :      _/|      :   `|| __/      ,.|| ||             \
/  ,   '  . \  :   =/_/      :     |'_______     || ||  ||   .      \
    |        \__`._/ |     .'   ___|        \__   \\||  ||...    ,   \
   l|,   '   (   /  ,|...-'        \   '   ,     __\||_//___          
 ___|____     \_/^\/||__    ,    .  ,__             ||//    \    .  ,
           _/~  `""~`"` \_           ''(       ....,||/       '   
 ..,...  __/  -'/  `-._ `\_\__        | \           ||  _______   .
   itz/jgs/ccm'`  `\   \  \-.\        /(_1_,..      || /
                                            ______/""""
```                                           





# Bronco Parts
Modern parts management tool for engineering teams and projects. Fully integrated with Airtable and with built in user management. 


## Features

- **Project, Part, and Assembly Management:**
  - Create, update, and organize projects, assemblies, and parts with hierarchical relationships.
  - Automatic part numbering and hierarchy-aware metadata (subteam, subsystem, etc).
  - Super cool tree view.
- **Order and Inventory Tracking:**
  - Manage orders, order items, and track part inventory and status.
  - Database and forms have the ability for this - not implemented fully right now.
- **User Management & Permissions:**
  - Role-based access (admin, editor, readonly, etc).
  - Registration links for controlled onboarding (single-use, multi-use, with fixed or user-supplied credentials).
- **Airtable Integration:**
  - Sync parts and assemblies to Airtable.
  - Add new options to Airtable single-select fields programmatically.
  - See code or contact maintainer for example Airtable setup.
- **Machine & Post-Process Management:**
  - Track machines, post-processes, and associate them with parts.
- **REST API:**
  - Modern Flask-based API for all operations, with JWT authentication and role checks.
- **Frontend:**
  - React-based frontend (see `frontend/`) for user interaction.

## Use Cases

- University or professional engineering teams managing hardware projects.
- Manufacturing teams tracking part fabrication, post-processing, and inventory.
- Organizations needing controlled, auditable user onboarding and permissions.
- Teams that want to sync engineering data with Airtable for reporting or collaboration.
- Anyone that wants to organize their projects that contain lots of small parts. 

## Project Structure

- `backend/` — Flask API, database models, migrations, and integration logic.
- `frontend/` — React app for user interface.
- `docker-compose.yml` — Multi-container orchestration for local/prod deployment.
- `testing/` — Scripts for integration with Airtable and test automation.
- `migrations/` — Alembic migrations for database schema management.
- `tests/` — Automated tests (pytest). *IN PROGRESS\*

## How It Works

- The backend exposes a REST API for all resources (projects, parts, users, orders, etc).
- User authentication is via JWT, with role-based decorators for access control.
- Registration links allow admins to invite users with specific permissions and onboarding flows.
- Parts and assemblies can be synced to Airtable, and new options can be added to Airtable fields via the API.
- The frontend consumes the API and provides a modern UI for all operations.

## Running the Project

### Prerequisites
- Docker and Docker Compose
- (Optional) Python 3.11+ and Node.js if running backend/frontend outside Docker

### Quick Start (Recommended)

1. **Clone the repository:**
   ```sh
   git clone <your-repo-url>
   cd BroncoPartsV2
   ```
2. **Set environment variables:**
   - Copy `.env.example` to `.env` and fill in secrets (DB, JWT, Airtable keys, etc).
   - Or set variables in your shell or Docker Compose override.
3. **Start all services:**
   ```sh
   docker-compose up --build
   ```
   This will start MySQL, the Flask backend, and the React frontend.
4. **Access the app:**
   - Frontend: [http://localhost:8080](http://localhost:8080)
   - Backend API: [http://localhost:8000/api](http://localhost:8000/api)
   - MySQL: localhost:3306 (see docker-compose for credentials)

### Running Backend Only (Dev)

1. Install Python dependencies:
   ```sh
   cd backend
   pip install -r requirements.txt
   ```
2. Set environment variables (see above).
3. Run database migrations:
   ```sh
   alembic upgrade head
   ```
4. Start the backend:
   ```sh
   flask run
   ```

### Running Frontend Only (Dev)

1. Install Node dependencies:
   ```sh
   cd frontend
   npm install
   ```
2. Start the frontend:
   ```sh
   npm start
   ```

## Airtable Integration
- Configure your Airtable API key, base ID, and table ID in environment variables or the relevant scripts.
- Use scripts in `backend/testing/` to test Airtable sync and option creation.

## Testing
- Run backend tests with:
  ```sh
  cd backend
  pytest
  ```
- See `testing/` for integration scripts and test helpers.

## Security Notes
- Change all default passwords and secrets before deploying to production.
- Use HTTPS and secure your environment variables.

## License
This project abides by the MIT License. 

---
For more details, see the code and comments in each directory, or contact the project maintainer.