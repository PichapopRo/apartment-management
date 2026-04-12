# Apartment Management System

## Project Description
A web-based apartment management system for managing rooms, tenancies, meter readings, billing, receipts, and reporting. It supports role-based access control, automated bill calculation, document uploads per room, and data export for accounting workflows.

## System Architecture Overview
The system follows a hybrid layered + service-based architecture:
- **API Layer (FastAPI Routers)**: Request/response schemas, auth dependencies, role checks.
- **Service Layer**: Business logic (billing calculation, receipts, tenancy rules, exports).
- **Repository Layer**: Database access and queries (SQLAlchemy).
- **Domain Models**: SQLAlchemy models for core entities.
- **Shared Utilities**: Security, storage, helpers, and config.

High-level components:
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **Frontend**: Vue 3 + Vite + Tailwind CSS
- **Storage**: Local filesystem for room documents

## User Roles & Permissions
- **Admin**
  - Full access
  - Manage rooms, tenancies, meters, billing, receipts
  - Manage users (create, delete, change roles)
  - Edit global billing rates
  - Export reports
- **Staff**
  - Manage rooms and tenancies
  - Upload/view room documents
  - Manage meter readings and rent calculation
  - Generate bills and receipts
  - Export reports
- **Resident**
  - View public room list (status only)
  - See own room (marked) and latest rent summary
  - No access to admin/staff operations

## Technology Stack
- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Database**: PostgreSQL
- **Frontend**: Vue 3, Vite, Tailwind CSS
- **Auth**: JWT (OAuth2 password flow)
- **PDF**: ReportLab
- **Exports**: XLSX via pandas/openpyxl
- **Containerization**: Docker + Docker Compose

## Installation & Setup Instructions
### Prerequisites
- Docker Desktop
- (Optional local dev) Python 3.11+, Node 20+

### Environment
Create a `.env` file in `backend/` (example):
```
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/apartment
SECRET_KEY=change-me
UPLOAD_DIR=/app/uploads
```

### Docker Setup
From project root:
```
docker compose up --build
```

## How to Run the System
- **Backend API**: http://localhost:8000
- **Frontend UI**: http://localhost:5173

To stop:
```
docker compose down
```

## Data Import
### Import meter readings and bills from XLS
Use the import script to load legacy data from an Excel workbook:
```
python backend/scripts/migrate_xls.py --file "C:\path\to\Account sample_data.xls" --apply --create-rooms
```
Notes:
- The script reads the latest sheet by date for room pricing, and meter values per month.
- Rooms are created in `001`�`018` format according to the sample data.
- Bills are generated with stored totals from the sheet when present.

## Screenshots
- Login page: [image here]
- Dashboard: [image here]
- Rooms page: [image here]
- Meter readings: [image here]
- Rent calculation: [image here]
- Bill status: [image here]
- User management: [image here]

