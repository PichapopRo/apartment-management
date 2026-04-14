# Project Report - Apartment Management System

## Project Overview
The Apartment Management System is a web application for managing rooms, tenancies, meter readings, billing, receipts, and exports for a single-building operation. It includes role-based access control, billing configuration, document uploads per room, PDF receipt generation, and Excel exports.

Key goals:
- Centralize room and tenant management
- Track monthly water/electric meter readings
- Automate bill calculation and receipt generation
- Provide admin/staff tools for operations and exports

## System Requirements
### Functional
- User authentication with RBAC (Admin, Staff, Resident)
- First-user bootstrap: the first registration must be an Admin; later self-registrations are Residents
- Admin user management (create users, update roles, delete users except the first admin)
- Room creation, editing, deletion (Admin only)
- Room listing for Admin/Staff; public room status list for Residents
- Assign tenants by name or linked resident account, track move-in/move-out
- Upload/view room documents (citizen ID, contract)
- Record monthly meter readings (water/electric) with validation against previous month
- Configure billing rates (water, electric, garbage fee, late fee)
- Generate monthly bills per room with optional unit overrides and late-fee flag
- Update bill payment status and remarks (Admin only)
- Issue and void receipts; generate receipt PDFs (single or bulk)
- Export bills/readings (by month or all data) to Excel
- Optional import tool to migrate legacy XLS meter/bill data

### Non-Functional
- Secure password hashing (Argon2) and JWT-based authentication
- Data integrity through unique constraints
- Layered API / Service / Repository structure
- Docker-based deployment
- Local file storage for uploaded room documents

## Architecture Characteristics
### Explicit Characteristics
**Security & Access Control**
- JWT-based auth with role guards (Admin, Staff, Resident)
- Resident endpoints limited to their own summary and public room list
- Admin-only operations for user management, billing config updates, and bill status updates

**Data Integrity**
- Unique constraints for monthly readings and bills per room
- Unique receipt numbers and single receipt per bill
- Validation that new meter readings exceed the previous month

**Operational Usability**
- Bulk meter input, billing generation, and receipt printing
- Excel exports for accounting workflows

**Deployability**
- Docker Compose for frontend, backend, and PostgreSQL
- Environment-based configuration

### Implicit Characteristics
**Maintainability / Modifiability**
- Service layer encapsulates business rules (billing, receipts, tenancy)

**Performance (Fit-for-purpose)**
- Designed for a single building with tens to hundreds of rooms

## Architecture Design
### Presentation Layer (Frontend)
- **Framework**: Vue 3 + Vite + Tailwind CSS
- **Routing**: Vue Router with role-based navigation
- **State**: lightweight module store for auth/session
- **Responsibilities**: UI rendering, user input handling, API calls, and displaying validation/error feedback

### Backend Implementation
- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Schemas**: Pydantic
- **Authentication**: JWT + Argon2 password hashing
- **Receipt generation**: ReportLab (PDF)
- **Exports**: XLSX via pandas/openpyxl

### Backend Structure
**API Layer (Routers)**
- Defines endpoints and schemas
- Enforces auth/RBAC

**Service Layer**
- Billing calculations and bill creation
- Meter reading validation rules
- Tenancy assignment/move-out
- Receipt issuance/voiding and PDF rendering
- Export generation

**Repository Layer**
- SQLAlchemy CRUD and query operations

**Shared Utilities**
- Security helpers, configuration, file storage

## Database Design
### Core Tables
- `users`
- `rooms`
- `tenancies`
- `room_documents`
- `meter_readings`
- `billing_config`
- `bills`
- `receipts`

### Foreign Keys
- `tenancies.room_id -> rooms.id`
- `tenancies.resident_user_id -> users.id`
- `room_documents.room_id -> rooms.id`
- `room_documents.uploaded_by_user_id -> users.id`
- `meter_readings.room_id -> rooms.id`
- `bills.room_id -> rooms.id`
- `receipts.bill_id -> bills.id`

### Constraints
- Unique `(room_id, billing_month)` in `meter_readings` and `bills`
- Unique `(room_id, doc_type)` in `room_documents`
- Unique `receipt_number` and unique `bill_id` in `receipts`
- Unique `username` and `email` in `users`

## Role & Permission Structure
### Admin
- Full system access
- Manage users/roles and billing configuration
- Create/edit/delete rooms
- Manage tenancies, readings, bills, receipts, and exports
- Update bill paid status and remarks

### Staff
- Manage rooms (read-only), tenancies, readings, bills, receipts, and exports
- Cannot manage users or change billing configuration
- Cannot update bill paid status (admin-only API constraint)

### Resident
- View public room list with occupancy status
- View their own room summary and latest bill status

## Implementation Details
### Key Workflows Implemented
**User Bootstrap & Management**
- First registration must be an Admin
- Admin can create users, change roles, and delete users (except the first admin)

**Room & Tenancy Setup**
- Admin creates rooms with rent rate and status
- Staff/Admin assigns residents to rooms or records tenant names
- Move-out updates tenancy and room status

**Monthly Meter Readings**
- Staff/Admin records monthly water/electric readings
- Readings must exceed the previous month�s values
- Recent readings (last 6) and yearly views are supported

**Billing Generation**
- Bills are generated per room/month using rates from `billing_config`
- Optional overrides for calculated water/electric units
- Late fee is a configurable fixed amount, applied per bill via a flag

**Receipts**
- Issue receipt per bill with unique receipt number
- Void receipts with a reason (status-based, not deleted)
- PDF receipts can be generated for single bills or in bulk

**Reporting & Export**
- Export bills and readings by month
- Export all bills, readings, or combined data as Excel files

### Frontend Implementation
- **Framework**: Vue 3 + Vite + Tailwind CSS
- **Auth**: Login + Register (bootstrap-aware)
- **Core Pages**:
  - Dashboard (Admin/Staff stats, Resident summary)
  - Rooms & Tenancies
  - Meter Readings (monthly) + Yearly Meter View
  - Rent Calculation (billing config, bill creation, receipt bulk PDF)
  - Bill Status (paid/remark updates)
  - Users (Admin-only)

### Deployment
- Docker Compose runs frontend, backend, and PostgreSQL
- Environment variables configure DB and JWT secrets

### Testing
- FastAPI tests for auth, billing calculation, reports, and room/tenancy flows
- Tests located in `backend/tests`
