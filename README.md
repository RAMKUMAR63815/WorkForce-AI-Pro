# WorkForce AI Pro
## HR Attrition Prediction & Workforce Intelligence Platform

**Project Type:** Full-Stack Web Application  
**Backend:** FastAPI  
**Frontend:** React + Vite  
**Database:** MySQL 8  
**ORM:** SQLAlchemy  
**Authentication:** JWT (JSON Web Token)  
**Deployment:** Docker and Docker Compose  
**AI & Analytics:** Python-based attrition prediction and workforce analytics APIs

---

## 1. Project Overview

WorkForce AI Pro is a full-stack workforce management and intelligence platform designed to support employee administration, HR operations, workforce analytics, and AI-assisted employee attrition prediction.

The application combines a React frontend, FastAPI backend, and MySQL database. It uses SQLAlchemy for database operations, JWT-based authentication, and role-based access control to manage access to protected features.

The platform also includes APIs for dataset management, attrition model training and prediction, prediction history, employee risk monitoring, attrition analytics, alert evaluation, and workforce forecasting.

The goal is to provide HR teams and managers with a centralized application for managing workforce information and exploring data-driven workforce insights.

## 2. Project Objectives

The main objectives of WorkForce AI Pro are:

- Centralize workforce and employee information.
- Provide secure authentication and role-based authorization.
- Support common HR operations through backend APIs and frontend screens.
- Manage attendance, leave, and payroll workflows.
- Provide workforce dashboards and analytical reports.
- Support attrition prediction through AI-related APIs.
- Maintain prediction history and employee risk-monitoring information.
- Support HR review and intervention workflows where implemented.
- Containerize the application to simplify local development and deployment.

## 3. Technology Stack

### Backend

- Python
- FastAPI
- SQLAlchemy ORM
- Pydantic
- JWT authentication
- Role-based access control (RBAC)

### Frontend

- React
- Vite
- JavaScript and JSX
- CSS
- API integration with the backend

### Database

- MySQL 8
- SQLAlchemy database models and relationships

### AI and Analytics

- Python-based dataset processing
- Attrition model training and prediction APIs
- Prediction history
- Employee risk monitoring
- Attrition analytics
- Workforce forecasting APIs

The exact machine-learning estimator, preprocessing pipeline, and measured model performance must be documented from the implementation and actual training results.

### Containerization

- Docker
- Docker Compose

## 4. Application Architecture

The application follows a client-server architecture.

```text
React + Vite Frontend
        |
        | HTTP requests / JSON
        v
FastAPI Backend
        |
        | JWT Authentication
        | Role-Based Access Control
        | Request Validation
        v
SQLAlchemy ORM
        |
        v
MySQL Database

FastAPI AI and Analytics APIs
        |
        +-- Dataset Management
        +-- Attrition Model Training
        +-- Attrition Prediction
        +-- Prediction History
        +-- Risk Monitoring
        +-- Attrition Analytics
        +-- Workforce Forecasting
```

### Request flow

1. A user opens the frontend application.
2. The user signs in using the authentication interface.
3. The frontend sends API requests to the FastAPI backend.
4. The backend validates the request and authenticates protected operations.
5. Role-based authorization determines whether the user can access the requested operation.
6. SQLAlchemy performs the required database operations.
7. The backend returns the response to the frontend.
8. The frontend displays the returned information.

For AI-related operations, the backend exposes dataset, training, prediction, and analytics endpoints. The exact model workflow depends on the implemented AI service.

## 5. Main Application Modules

### 5.1 Authentication and Authorization

The authentication module supports user registration, login, and retrieval of the currently authenticated user.

JWT bearer authentication is used for protected API operations.

Known application roles:

- `ADMIN`
- `HR`
- `MANAGER`
- `EMPLOYEE`

The backend must enforce permissions for protected operations. Public registration must not allow users to assign themselves privileged roles.

### 5.2 Employee Management

The employee module supports workforce record management.

Known employee attributes include employee code, user association, department association, designation, joining date, salary, phone, and address.

The exact available create, read, update, and deactivate operations should be confirmed through the running API documentation.

### 5.3 Department and Shift Management

Department information supports workforce organization.

Shift-related API operations documented during development include updating shifts, deactivating shifts, and assigning shifts to employees.

### 5.4 Attendance Management

Attendance-related workflows support workforce attendance information. The current API documentation should be consulted for exact operations, fields, validation rules, and permissions.

### 5.5 Leave Management

The documented leave-related operations include applying for leave, retrieving leave records, retrieving the current user's leave records, and reviewing leave requests.

### 5.6 Leave Balance Management

The application includes APIs for creating leave balances and retrieving leave balances for the current user or a specified employee.

### 5.7 Payroll Management

The documented payroll operations include payroll processing, retrieving payroll records, attendance summaries, and downloading payslips in PDF format.

Payroll calculations and generated outputs should be verified with test records before being used for real payroll.

### 5.8 Notifications

The notification module includes operations for retrieving notifications, checking unread notification counts, marking notifications as read, and sending employee notifications.

### 5.9 Document Management

The documented document operations include uploading a user's document, retrieving documents, downloading a document, and deleting a document.

### 5.10 Performance Reviews

The performance-review module includes operations for creating, listing, retrieving, updating, and deleting review records, subject to the configured permissions.

### 5.11 One-to-One Chat

The documented chat APIs include listing conversations, creating conversations, sending messages, retrieving messages, and marking messages as read.

### 5.12 Dataset Management

The dataset module provides APIs to upload and list datasets, retrieve dataset details, and inspect dataset validation errors.

### 5.13 AI Attrition Prediction

The attrition module exposes APIs for training a model against a dataset, requesting predictions, listing trained models, and retrieving prediction history.

The quality of predictions depends on the dataset, preprocessing, model implementation, and evaluation results.

### 5.14 Employee Risk Monitoring

Risk-monitoring APIs provide operations for retrieving risk summaries, risk logs, and the risk history associated with an employee.

### 5.15 Attrition Analytics and Alerts

The application includes APIs for attrition analytics and alert evaluation. These features are intended to help HR users review workforce risk indicators and decide whether further investigation or support is appropriate.

### 5.16 Workforce Forecasting

Workforce-forecasting APIs support generating forecasts and retrieving forecast history.

The forecasting method, input data, and evaluation should be documented according to the actual implementation.

---

## 6. Local Development Configuration

The project has previously used the following local ports:

| Component | Local address |
|---|---|
| Frontend | `http://localhost:5175` |
| FastAPI backend | `http://localhost:8003` |
| Swagger API documentation | `http://localhost:8003/docs` |
| OpenAPI JSON | `http://localhost:8003/openapi.json` |
| MySQL host port | `3308` |

These are development settings and may differ from the current `docker-compose.yml`.

## 7. Prerequisites

Install or configure:

- Docker Desktop
- Docker Compose
- Git, if version control is required
- A code editor such as Visual Studio Code
- A web browser

For the Docker-based workflow, Python, Node.js, and MySQL do not necessarily need to be installed directly on the host if the relevant services and dependencies are configured inside containers.

## 8. Installation and Startup

Open PowerShell and navigate to the project directory.

```powershell
cd C:\WorkForce-AI-Pro
```

Build and start the application:

```powershell
docker compose up -d --build
```

Check container status:

```powershell
docker compose ps
```

Check backend logs:

```powershell
docker compose logs --tail=100 backend
```

Check frontend logs:

```powershell
docker compose logs --tail=100 frontend
```

If a service has a different name in the Compose configuration, use that service name instead.

### Access the application

Open the frontend URL configured by Docker Compose.

Open the backend API documentation:

`http://localhost:8003/docs`

The Swagger interface can be used to inspect registered API routes, request schemas, response schemas, and authentication requirements.

## 9. API Documentation

The application uses FastAPI's OpenAPI integration.

**Swagger UI**

`http://localhost:8003/docs`

**OpenAPI JSON**

`http://localhost:8003/openapi.json`

The API documentation includes the routes registered by the running backend.

For the endpoint inventory and usage notes, refer to `API_DOCUMENTATION.md`.

## 10. Database Design

The application uses MySQL with SQLAlchemy models.

Known core relationships include:

- A role can be associated with multiple users.
- A user can have at most one employee profile through the unique employee-to-user relationship.
- A department can be associated with multiple employees.
- An employee's department reference can be nullable.

Other feature modules may introduce additional tables and relationships.

### Database deliverables

- `DATABASE_SCHEMA.sql` — actual SQL schema exported from MySQL.
- `DATABASE_ER_DIAGRAM.png` — entity-relationship diagram.

The schema export should contain the actual table definitions, column types, constraints, indexes, and foreign keys from the current database.

## 11. AI Attrition Prediction Workflow

The documented API workflow includes the following steps.

1. Upload a dataset.
2. Retrieve dataset information.
3. Inspect dataset validation errors.
4. Train an attrition model using a dataset identifier.
5. Submit a prediction request.
6. Retrieve trained-model information.
7. Review prediction history.
8. Retrieve risk-monitoring information.
9. Evaluate configured attrition alerts.
10. Generate and review workforce forecasts.

### Documented AI-related endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/datasets/` | Upload a dataset |
| GET | `/api/datasets/` | List datasets |
| GET | `/api/datasets/{dataset_id}` | Retrieve dataset details |
| GET | `/api/datasets/{dataset_id}/errors` | Retrieve dataset validation errors |
| POST | `/api/attrition/train/{dataset_id}` | Train an attrition model |
| POST | `/api/attrition/predict` | Request an attrition prediction |
| GET | `/api/attrition/models` | List trained models |
| GET | `/api/attrition/history` | Retrieve prediction history |
| GET | `/api/risk-monitoring/summary` | Retrieve a risk summary |
| GET | `/api/risk-monitoring/logs` | Retrieve risk logs |
| GET | `/api/attrition-analytics/summary` | Retrieve attrition analytics |
| POST | `/api/workforce-forecast/generate` | Generate a workforce forecast |
| GET | `/api/workforce-forecast/history` | Retrieve forecast history |

Check Swagger UI for the exact request fields, response formats, and required permissions.

### Responsible use of AI

Attrition predictions are estimates, not certainties. They should support human review rather than automatically determine employment decisions.

Model evaluation should document the actual dataset, model version, feature preparation, train/test strategy, and measured performance metrics.

## 12. Testing and Verification

The project has had development checks for authentication, role-based access control, and selected attrition-related endpoints.

The final submission should include reproducible tests for:

- Backend startup
- Database connectivity
- Authentication and token validation
- Role-based access control
- Employee operations
- Attendance and leave workflows
- Payroll operations
- AI model training and prediction
- Analytics and report output
- Frontend/API integration
- Database schema export

Refer to `TEST_RESULTS.md` for recorded observations and the final verification checklist.

Do not report a test as passed unless it has been run against the relevant application version.

## 13. Security Considerations

- Keep secrets and real credentials out of source control.
- Do not submit a real `.env` file.
- Use placeholder values in `.env.example`.
- Do not include live bearer tokens in documentation or screenshots.
- Enforce authorization in the backend.
- Protect employee records, payroll information, and documents.
- Use anonymized or synthetic data for demonstrations.
- Apply appropriate access controls to employee-level risk predictions.

## 14. Project Deliverables

The final submission contains the following required categories.

1. Backend source code.
2. Frontend source code.
3. AI prediction APIs.
4. Workforce dashboards.
5. Analytics reports.
6. UI screenshots and demo.
7. API documentation.
8. Database schema and ER diagram.
9. Test results.

### Suggested submission structure

```text
WorkForce-AI-Pro/
├── backend/
├── frontend/
├── submission/
│   ├── README.md
│   ├── API_DOCUMENTATION.md
│   ├── DATABASE_SCHEMA.sql
│   ├── DATABASE_ER_DIAGRAM.png
│   ├── AI_MODEL_DOCUMENTATION.md
│   ├── TEST_RESULTS.md
│   ├── screenshots/
│   └── demo/
├── docker-compose.yml
└── .env.example
```

## 15. Conclusion

WorkForce AI Pro combines workforce management APIs, authentication, role-based authorization, and AI-oriented attrition analytics in a containerized full-stack application.

The platform is intended to help HR teams manage workforce information and explore attrition-related insights through a centralized interface.

Before final submission, verify the current application build, export the actual database schema, capture screenshots from the running UI, and record the outcomes of the final tests.
