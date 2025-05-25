# Feature: Enhanced Part Creation with Airtable Integration

This document outlines the tasks required to implement enhancements to the part creation process, including new fields and automatic Airtable integration.

**I. Backend Development**

1.  **Update Part Model & Database Schema:**
    *   [x] Add `quantity` (Integer, not nullable) to the `Part` model.
    *   [x] Add `raw_material` (String, not nullable) to the `Part` model.
    *   [x] Add `status` (String, not nullable, default: "in design") to the `Part` model.
    *   [x] Define `Machine` model/table (if not already existing, likely a static list initially) and establish a many-to-one relationship from `Part` to `Machine`.
    *   [x] Define `PostProcess` model/table (if not already existing, likely a static list initially) and establish a many-to-many relationship with the `Part` model.
    *   [x] Define `Subteam` (self-referential ForeignKey on `Part` model, linking to another `Part` record).
    *   [x] Define `Subsystem` (self-referential ForeignKey on `Part` model, linking to another `Part` record).
    *   [x] Generate and apply database migrations (e.g., using Alembic) to reflect these schema changes.

2.  **Update "Create Part" API Endpoint (e.g., `POST /api/parts`):**
    *   [x] Modify the request payload validation to accept and require:
        *   [x] `quantity` (Integer)
        *   [x] `machine_id` (Integer/String, representing the single selected machine)
        *   [x] `raw_material` (String - custom text)
        *   [x] `post_process_ids` (List of integers/strings, representing selected post-processes)
    *   [x] Optionally accept `subteam_id` and `subsystem_id` from the frontend if the user makes a specific selection from the dropdowns.
    *   [x] Ensure the `status` field is automatically set to "in design" during the part creation logic.
    *   [x] Implement logic to automatically determine `Subteam` and `Subsystem` if not provided in the request. This will be based on the part\'s parent hierarchy:
        *   [x] The `Subteam` is the name/ID of the part that is the 2nd item in the breadcrumb hierarchy (e.g., "Chassis" in "TLA > Chassis > Pedal Box > Front Plate").
        *   [x] The `Subsystem` is the name/ID of the part that is the 3rd item in the breadcrumb hierarchy (e.g., "Pedal Box" in "TLA > Chassis > Pedal Box > Front Plate").
        *   [x] This requires traversing up the `parent_id` chain of the newly created part.
    *   [x] Update the part creation service logic to correctly save the new fields and manage the relationships.

3.  **Airtable Integration:**
    *   [x] Install `pyairtable` (`pip install pyairtable`).
    *   [x] Add necessary Airtable configuration (Access Token, Base ID: `appWyhvDH5UvItLMY`, Table ID: `tblFusLFLj1XntXee` for parts) to environment variables and application configuration.
    *   [x] Implement a dedicated service or module for handling Airtable API communication using `pyairtable`.
        *   [x] Before sending data to Airtable, validate that the determined/selected `Subteam` and `Subsystem` names exist as options in the corresponding Airtable dropdown fields. If not, cancel the Airtable sync for this part and log an error/return an appropriate error message to the user.
        *   [x] Develop a function to map the application\'s part data to the corresponding Airtable columns (see field mapping below).
        *   [x] Develop a function to create a new record in the designated Airtable base/table. (Basic structure in `airtable_service.py` exists, needs uncommenting of `table.create()` and removal of simulation after mapping is complete)
    *   [x] Integrate this Airtable service into the part creation workflow.
    *   [ ] Implement robust error handling and logging. (Basic logging added, can be enhanced with more specific Airtable error handling)

4.  **(Optional) CRUD Endpoints for Supporting Models:**
    *   [x] API endpoints to list available machines and post-processes will be needed for the frontend.
    *   [x] API endpoint to list assemblies within the current part\'s project (for populating Subteam/Subsystem dropdowns in the create part form).

**II. Frontend Development**

1.  **Update "Create Part" Form/Component (e.g., `CreatePart.js`):**
    *   [x] Add a new input field for `Quantity` (number input, required).
    *   [x] Add a single-select input component for `Machine` (dropdown, required).
        *   [x] Fetch the list of available machines from the backend.
    *   [x] Add `Subteam` dropdown:
        *   [x] Populate with assemblies from the current part\'s project (fetched from backend).
        *   [x] This allows user override; if not selected, backend will derive.
    *   [x] Add `Subsystem` dropdown:
        *   [x] Populate with assemblies from the current part\'s project (fetched from backend).
        *   [x] This allows user override; if not selected, backend will derive.
    *   [x] Add a new input field for `Raw Material` (text input, required).
    *   [x] Add a multi-select input component for `Post Processes` (e.g., multi-select dropdown or checkboxes, required).
        *   [x] Fetch the list of available post-processes from the backend.
    *   [x] The existing `description` field in the form will be used for Airtable\'s "Notes".
    *   [x] `Status` ("in design") is backend-assigned and likely doesn\'t need to be on the form.
    *   [x] Update form state management and client-side validation.
    *   [x] Modify the API call to include: `quantity`, `machine_id` (single), `raw_material`, `post_process_ids` (list), and optionally `subteam_id`, `subsystem_id`.

2.  **Display of Auto-Fetched/Selected Information (Subteam/Subsystem):**
    *   [x] **Resolved:** Yes, this information should be displayed on part detail views.
    *   [x] Update the `PartDetails.js` component and any other relevant UI sections to display the `Subteam` and `Subsystem` associated with a part.

**III. General Tasks**

1.  **Testing:**
    *   **Backend:**
        *   [ ] Write unit tests for the `Part` model changes and new relationships.
        *   [ ] Write unit tests for the API endpoint validation, part creation logic (including the auto-fetching of subteam/subsystem), and correct handling of new fields.
        *   [ ] Write unit tests for the Airtable integration service, mocking Airtable API calls.
        *   [ ] Write integration tests for the complete part creation flow, including database interactions and (mocked) Airtable calls.
    *   **Frontend:**
        *   [ ] Write component tests for the updated "Create Part" form, covering new inputs, validation, and data submission.
        *   [ ] Consider end-to-end tests for the part creation user journey, including filling out the new fields and verifying the part is created (verification of Airtable record creation might be complex for E2E and could be covered by backend integration tests).
2.  **Documentation:**
    *   [ ] Update any existing API documentation (e.g., Swagger/OpenAPI specs) for the "Create Part" endpoint to reflect the new request body parameters.
    *   [ ] Document the Airtable integration setup, including required environment variables and any assumptions about the Airtable base structure.
    *   [ ] Update user guides or internal team documentation regarding the new part creation process and fields.

**IV. Clarifications & Resolved Items:**

*   **Tree Structure for Subteam/Subsystem:**
    *   **Resolved:** The backend will derive `Subteam` (2nd tree item) and `Subsystem` (3rd tree item) from the part's parent hierarchy if not explicitly selected by the user in the creation form.
*   **Airtable Details:**
    *   **Resolved:** Use `PyAirtable`.
    *   Access Token: To be provided securely.
    *   Base ID: `appWyhvDH5UvItLMY`
    *   Table ID: `tblFusLFLj1XntXee`
    *   View ID (for reference): `viwaj1gxLv9L4JqFw`
    *   **Resolved: Field Mapping & Handling:**
        *   Application `Part.name` -> Airtable **Name** (Text)
        *   Application derived/selected `Subteam` name -> Airtable **Subteam** (Single Select Dropdown). **Must match an existing Airtable option, otherwise error.**
        *   Application derived/selected `Subsystem` name -> Airtable **Subsystem** (Single Select Dropdown). **Must match an existing Airtable option, otherwise error.**
        *   Application `Part.quantity` -> Airtable **Manufacturing Quantity** (Number)
        *   Application `Part.status` ("in design") -> Airtable **Status** (Dropdown)
        *   Application selected `Machine` (single name) -> Airtable **Machine** (Single Select Dropdown)
        *   Application `Part.raw_material` -> Airtable **Raw material** (Text)
        *   Application selected `PostProcesses` (list of names) -> Airtable **Post-process** (Multiple Select Dropdown or compatible type)
        *   Application `Part.description` -> Airtable **Notes** (Text)
        *   *Fields to disregard: Part Image, Vendor, Part Number, COTSquanitity, Owner, Machinist, Mfg priority, Created.*
*   **Source of Options for Machine, Post Processes, Raw Material:**
    *   **Resolved for Machines:** Predefined list. Backend provides to frontend for single-select dropdown.
    *   **Resolved for Post Processes:** Predefined list. Backend provides to frontend for multi-select.
    *   **Resolved for Raw Material:** Custom text input.
*   **Display of Auto-Fetched Subteam/Subsystem in UI:**
    *   **Resolved:** Yes, display in part detail views. The "Create Part" form will also have dropdowns for these, populated with assemblies from the current project, allowing user selection/override.
*   **Notes Field:**
    *   **Resolved:** The application's existing `Part.description` will be used for Airtable's "Notes" field. No separate "Notes" field in the creation form is needed for this purpose.

This detailed task list should help guide the development of this feature.
