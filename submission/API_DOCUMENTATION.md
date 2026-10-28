# WorkForce AI Pro — API Documentation

## 1. Overview

**WorkForce AI Pro** is an HR Attrition Prediction and Workforce Intelligence Platform built with FastAPI, MySQL, SQLAlchemy, JWT authentication, and machine learning.

This document provides an overview of the backend API endpoints and how to access them.

## 2. Base URLs

| Resource | URL |
|---|---|
| Backend API | `http://localhost:8003` |
| Swagger UI | `http://localhost:8003/docs` |
| ReDoc | `http://localhost:8003/redoc` |
| OpenAPI JSON | `http://localhost:8003/openapi.json` |
| Health check | `http://localhost:8003/health` |
| Database health | `http://localhost:8003/health/database` |

The API paths listed below are relative to the backend base URL.

## 3. Authentication

The application uses JWT-based authentication.

### Login

**Endpoint:** `POST /api/auth/login`

Use this endpoint to authenticate a user and obtain an access token.

### Register

**Endpoint:** `POST /api/auth/register`

Use this endpoint to register a user according to the application's registration rules.

### Current user

**Endpoint:** `GET /api/auth/me`

Returns the authenticated user's information.

### Using the access token

For protected endpoints, send the token in the HTTP request header:

`Authorization: Bearer YOUR_ACCESS_TOKEN`

In Swagger UI:

1. Open `/docs`.
2. Execute the login endpoint with valid credentials.
3. Copy the access token from the response.
4. Click **Authorize**.
5. Enter the token in the format required by the Swagger security scheme.
6. Execute the protected endpoint.

The exact request fields and response structures are defined by the live OpenAPI specification.

## 4. Role-Based Access Control (RBAC)

The application supports four roles:

- **ADMIN** — administrative operations.
- **HR** — human resources operations.
- **MANAGER** — manager-specific operations.
- **EMPLOYEE** — employee self-service operations.

Access to an endpoint depends on the role permissions configured in the backend. A valid token does not automatically grant access to every endpoint.

### RBAC verification endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/rbac/admin-check` | Verify administrator access |
| GET | `/api/rbac/hr-check` | Verify HR access |
| GET | `/api/rbac/manager-check` | Verify manager access |
| GET | `/api/rbac/employee-check` | Verify employee access |

Expected behavior depends on the user's role and the configured dependencies. A successful authorization generally returns a successful HTTP status; a role restriction generally returns `403 Forbidden`.

## 5. Health Monitoring

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Check backend health |
| GET | `/health/database` | Check database connectivity |

Use these endpoints when checking whether the backend and database are responding.

## 6. Employee Management

The employee module manages employee records.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/employees/` | Create an employee |
| GET | `/api/employees/` | List employees |
| GET | `/api/employees/{employee_id}` | Retrieve an employee |
| PUT | `/api/employees/{employee_id}` | Update an employee |
| DELETE | `/api/employees/{employee_id}` | Deactivate an employee |

The employee listing endpoint supports query parameters for searching, department filtering, designation filtering, active status, and pagination, as implemented in the employee router.

## 7. Department and Shift Management

### Departments

Use the department endpoints registered by the backend to manage department records and department status. Refer to `/docs` for the exact paths and supported operations.

### Shifts

| Method | Endpoint | Purpose |
|---|---|---|
| PUT | `/api/shifts/{shift_id}` | Update a shift |
| DELETE | `/api/shifts/{shift_id}` | Delete a shift |
| PATCH | `/api/shifts/assignments/{employee_id}` | Update an employee's shift assignment |

Check the live OpenAPI specification for required request fields and permission requirements.

## 8. Leave Management

The leave module supports leave requests, employee self-service, HR review, and leave balance information.

| Method | Endpoint | Purpose |
|---|---|---|
| GET/POST | `/api/leaves/` | List or create leave requests, according to the supported operations |
| GET | `/api/leaves/my` | Retrieve the current employee's leave requests |
| PATCH | `/api/leaves/{leave_id}/review` | Review a leave request |
| GET | `/api/leave-balances/` | Access leave balance records |
| GET | `/api/leave-balances/my` | Retrieve the current employee's leave balances |
| GET | `/api/leave-balances/employee/{employee_id}` | Retrieve leave balances for an employee |

Review and administrative operations may require elevated permissions.

## 9. Attendance and Payroll

### Attendance

Attendance endpoints provide access to attendance records and attendance summaries. Refer to Swagger UI for the registered attendance paths, request models, and response models.

### Payroll

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/payroll/process` | Process payroll |
| GET | `/api/payroll/my` | Retrieve the current employee's payroll records |
| GET | `/api/payroll/` | List payroll records |
| GET | Registered payslip PDF endpoints | Retrieve supported payslip documents |

Payroll processing and salary information should be restricted to authorized roles and the appropriate employee.

## 10. Notifications and Documents

### Notifications

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/notifications/my` | Retrieve the current user's notifications |
| PATCH | `/api/notifications/{notification_id}/read` | Mark a notification as read |
| GET | `/api/notifications/employee/{employee_id}` | Retrieve notifications for an employee |
| GET | `/api/notifications/` | List notifications |
| GET | `/api/notifications/my/unread-count` | Retrieve the unread notification count |

Confirm the supported HTTP methods for each route in `/docs`.

### Documents

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/documents/my` | List the current user's documents |
| POST | `/api/documents/my` | Upload a document, if supported by the registered operation |
| GET | `/api/documents/` | List documents |
| GET | `/api/documents/{document_id}/download` | Download a document |
| DELETE | `/api/documents/{document_id}` | Delete a document |

Document access should follow the application's authorization rules.

## 11. Performance Reviews and Employee Chat

### Performance reviews

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/performance-reviews/` | List performance reviews |
| GET | `/api/performance-reviews/my` | Retrieve the current user's reviews |
| GET | `/api/performance-reviews/{review_id}` | Retrieve a review |
| PATCH | `/api/performance-reviews/{review_id}` | Update a review |
| DELETE | `/api/performance-reviews/{review_id}` | Delete a review |

### Chat

| Method | Endpoint | Purpose |
|---|---|---|
| GET/POST | `/api/chat/conversations` | List or create conversations, depending on the registered operations |
| GET | `/api/chat/{conversation_id}/messages` | Retrieve conversation messages |
| POST | `/api/chat/{conversation_id}/messages` | Send a message |
| PATCH | `/api/chat/{conversation_id}/read` | Mark a conversation as read, if supported by the registered operation |

Consult Swagger UI for exact request and response schemas.

## 12. AI Attrition Prediction

The AI module supports dataset management, model training, prediction, and model history.

### Dataset management

| Method | Endpoint | Purpose |
|---|---|---|
| GET/POST | `/api/datasets/` | List or upload/register datasets |
| GET | `/api/datasets/{dataset_id}` | Retrieve dataset information |
| GET | `/api/datasets/{dataset_id}/errors` | Retrieve dataset validation errors |

### Model training and prediction

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/attrition/train/{dataset_id}` | Train a model using a dataset |
| POST | `/api/attrition/predict` | Request an attrition prediction |
| GET | `/api/attrition/models` | Retrieve available model information |
| GET | `/api/attrition/history` | Retrieve prediction or model history |

The actual prediction fields, probability format, model metrics, and training results must be taken from the API response and the implemented model. They are not assumed in this document.

## 13. Attrition Risk Monitoring and Alerts

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/risk-monitoring/summary` | Retrieve risk-monitoring summary |
| GET | `/api/risk-monitoring/logs` | Retrieve risk-monitoring logs |
| GET | `/api/risk-monitoring/employees/{employee_id}/history` | Retrieve an employee's risk history |
| GET | `/api/employee-risk-alert-dashboard/summary` | Retrieve employee risk-alert dashboard data |
| POST | `/api/attrition-alerts/evaluate` | Evaluate employees for attrition alerts |

The alert evaluation endpoint may accept `cooldown_hours` as a query parameter. For example:

`POST /api/attrition-alerts/evaluate?cooldown_hours=1`

Use this example only if the deployed route registers that HTTP method and parameter. Alert creation and cooldown behavior depend on the current implementation.

## 14. Workforce Forecasting and Analytics

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/workforce-forecast/generate` | Generate a workforce forecast |
| GET | `/api/workforce-forecast/history` | Retrieve forecast history |
| GET | `/api/attrition-analytics/summary` | Retrieve attrition analytics |
| GET | `/api/dashboard/employee` | Retrieve employee dashboard data |
| GET | `/api/dashboard/hr` | Retrieve HR dashboard data |

Forecasting and analytics outputs depend on available data and the implemented business logic.

## 15. HTTP Status Codes

Common HTTP status codes include:

| Status | Meaning |
|---|---|
| 200 OK | Request completed successfully |
| 201 Created | Resource created successfully |
| 204 No Content | Request succeeded without a response body |
| 400 Bad Request | Request cannot be processed |
| 401 Unauthorized | Authentication is missing or invalid |
| 403 Forbidden | Authenticated user lacks permission |
| 404 Not Found | Requested resource does not exist |
| 409 Conflict | Request conflicts with existing data |
| 422 Unprocessable Entity | Request validation failed |
| 500 Internal Server Error | Unexpected server-side error |

The status codes actually returned depend on each endpoint's implementation.

## 16. API Testing

### Step 1 — Start the containers

Open PowerShell in the project directory:

```powershell
cd C:\WorkForce-AI-Pro
docker compose up -d --build
```

### Step 2 — Check container status

```powershell
docker compose ps
```

Confirm that the backend is running and MySQL is healthy.

### Step 3 — Inspect backend logs

```powershell
docker compose logs --tail=100 backend
```

### Step 4 — Open Swagger UI

Navigate to:

`http://localhost:8003/docs`

### Step 5 — Test the API

1. Test the health endpoints.
2. Log in using a test account.
3. Authorize Swagger with the returned token.
4. Test endpoints permitted for that user's role.
5. Test restricted endpoints with a user who lacks permission.
6. Check validation behavior using invalid input.
7. Confirm that database changes are reflected in subsequent reads.

Record actual response codes and results in `TEST_RESULTS.md`. Do not mark a test as passed until it has been executed.

## 17. OpenAPI Specification

FastAPI generates the OpenAPI specification automatically.

Open:

`http://localhost:8003/openapi.json`

The generated specification is the source of truth for:

- Registered routes and HTTP methods.
- Required path, query, and header parameters.
- Request body schemas.
- Response schemas.
- Authentication schemes.
- Declared response status codes.

If this document and the live OpenAPI specification differ, use the live specification to verify the deployed API and update this document accordingly.

## 18. Security Notes

- Never commit passwords, JWT secrets, database credentials, or production tokens to version control.
- Use environment variables for sensitive configuration.
- Enforce role-based access control on protected operations.
- Validate incoming request data.
- Protect employee personal information and payroll data.
- Use HTTPS in production.
- Keep dependencies updated and review logs for unexpected failures.
- Test authentication and authorization for every sensitive endpoint.

## 19. Documentation Maintenance

Update this document whenever routes, schemas, permissions, or business logic change.

Before submitting the project, verify the complete endpoint inventory using Swagger UI and add real test evidence to the test report.

**Project:** WorkForce AI Pro  
**Backend:** FastAPI  
**Database:** MySQL  
**ORM:** SQLAlchemy  
**Authentication:** JWT  
**API specification:** OpenAPI
