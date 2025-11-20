# The Pulse - Moroccan Startup Ecosystem Platform
## Project Handover Documentation

![The Pulse](https://img.shields.io/badge/Version-1.0.0-green)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey)
![Azure](https://img.shields.io/badge/Azure-SQL%20Database-blue)

> **This document is intended for the team continuing development of The Pulse platform.**

---

## 📋 Table of Contents
1. [Project Overview](#1--project-overview)
2. [Architecture Overview](#2--architecture-overview)
3. [Project Structure](#3--project-structure)
4. [Setup Instructions](#4--setup-instructions)
5. [Database Configuration](#5--database-configuration)
6. [Deployment on Azure](#6--deployment-on-azure)

---

## 1. 🏷️ Project Overview

**The Pulse** is a web platform for tracking and visualizing the Moroccan startup ecosystem. It centralizes data about startups, founders, investors, incubators, and funding activities.

### Key Features
- User authentication and session management
- Comprehensive profiles for startups, founders, investors, and incubators
- Interactive analytics dashboard with Chart.js visualizations
- Advanced filtering and search capabilities
- Funding rounds tracking and investment analytics
- Dark/Light theme toggle
- Responsive design (mobile, tablet, desktop)

### Target Users
- Ecosystem Analysts
- Investors & VCs
- Founders & Entrepreneurs
- Incubators/Accelerators
- Government & Policy Makers

---

## 2. 🧩 Architecture Overview

### High-Level System Design

```
┌─────────────────────────────────────────────────────────────┐
│                         USER BROWSER                         │
│                    (Chrome, Firefox, Safari)                 │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS Requests
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    FLASK WEB APPLICATION                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  app.py (Main Application)                           │  │
│  │  - Routes & Controllers                              │  │
│  │  - Session Management                                │  │
│  │  - Authentication                                    │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  models.py (Data Models)                             │  │
│  │  - SQLAlchemy ORM Models                             │  │
│  │  - Relationships                                     │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Functions.py (Business Logic)                       │  │
│  │  - Helper Functions                                  │  │
│  │  - Data Aggregation                                  │  │
│  │  - Analytics Calculations                            │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  templates/ (Jinja2 HTML)                            │  │
│  │  - 17+ HTML template files                           │  │
│  │  - Dark/Light theme CSS                              │  │
│  │  - JavaScript for interactivity                      │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │ SQL Queries (pyodbc + SQLAlchemy)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              AZURE SQL DATABASE (Cloud)                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Database: THEPULSEDB                                │  │
│  │  Server: thepulseserver.database.windows.net        │  │
│  │                                                      │  │
│  │  Tables:                                             │  │
│  │  - Startups, Founders, Investors                    │  │
│  │  - Incubators, FundingRounds                        │  │
│  │  - Investments, Funds, Education                    │  │
│  │  - Experience, Institutes                           │  │
│  │  - Junction Tables (Many-to-Many)                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend:**
- Flask 3.0 (Python web framework)
- SQLAlchemy (ORM for database)
- Azure SQL Database
- Session-based authentication

**Frontend:**
- Bootstrap 5.3.0
- Chart.js 3.9.1
- Font Awesome 6.4.0
- Jinja2 templates

---

## 3. 📁 Project Structure

```
ThePulseApp/
│
├── app.py                      # Main Flask application (routes, authentication, DB config)
├── models.py                   # SQLAlchemy ORM models (11 entity classes)
├── Functions.py                # Helper functions (data aggregation, analytics)
├── requirements.txt            # Python dependencies (Flask, SQLAlchemy, pyodbc, etc.)
├── Database.sql                # Database schema/structure reference
├── README.md                   # This documentation file
│
├── templates/                  # Jinja2 HTML templates (frontend)
│   ├── base.html              # Base template with navbar, theme toggle, common layout
│   ├── login.html             # Authentication page with theme support
│   ├── home.html              # Homepage/landing page
│   ├── Dashboard.html         # Analytics dashboard with Chart.js visualizations
│   ├── startups.html          # Startup listing with advanced filters
│   ├── startup_detail.html    # Detailed startup profile page
│   ├── founders.html          # Founder listing with search/filters
│   ├── founder_detail.html    # Founder profile with experience, education, startups
│   ├── investors.html         # Investor directory with filters
│   ├── investor_detail.html   # Investor profile with portfolio and funding rounds
│   ├── incubator_detail.html  # Incubator/Accelerator profile with startups
│   ├── funds.html             # Investment funds listing
│   └── aboutus.html           # About page with team/mission info
│
├── static/                     # Static assets (images, CSS, JS - if separated)
│   └── images/                # Logos and images
│       ├── amic_logo.png
│       ├── azur_innovation_logo.png
│       ├── bank_almaghrib_logo.png
│       ├── cdg_invest_logo.png
│       ├── tamwilcom_logo.png
│       └── um6p_logo.png
│
└── __pycache__/               # Python bytecode cache (auto-generated, ignore in git)
    ├── Functions.cpython-312.pyc
    └── models.cpython-312.pyc
```

### Key Files

- **app.py** - Main Flask application with routes and authentication
- **models.py** - SQLAlchemy database models (11 entities)
- **Functions.py** - Helper functions for data aggregation and analytics
- **requirements.txt** - Python dependencies
- **templates/** - Jinja2 HTML templates for all pages

---

## 4. 🚀 Setup Instructions

### Prerequisites
- Python 3.8+ (Developed with Python 3.12)
- ODBC Driver 17 for SQL Server
- Azure SQL Database access

### Quick Start

```bash
# Clone repository
git clone <repository-url>
cd ThePulseApp

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell

# Install dependencies
pip install -r requirements.txt

# Configure database connection in app.py
# Update USERNAME and PASSWORD in SQLALCHEMY_DATABASE_URI

# Run application
python app.py
```

Application will start on `http://127.0.0.1:5000/`

---

## 5. 🗄️ Database Configuration

### Existing Database (Recommended)

**Connection Details:**
- **Server**: `thepulseserver.database.windows.net`
- **Database**: `THEPULSEDB`
- **Authentication**: SQL Server Authentication

**Setup Steps:**
1. Get credentials from project owner
2. Update connection string in `app.py`:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = (
    "mssql+pyodbc://USERNAME:PASSWORD@thepulseserver.database.windows.net/THEPULSEDB"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&Encrypt=yes&TrustServerCertificate=no&Connection Timeout=100"
)
```
3. Add your IP to Azure SQL firewall rules
4. Test connection

### Database Schema

**Main Tables:**
- Startups, Founders, Investors, Incubators
- FundingRounds, Investments, Funds
- Education, Experience, Institutes
- Junction tables for many-to-many relationships

---

## 6. ☁️ Deployment on Azure

### Current Status
- ✅ Azure SQL Database: Active (`thepulseserver.database.windows.net`)
- 🟡 Azure App Service: To be verified

### Quick Deployment

**Create Azure App Service:**
```bash
az login
az group create --name ThePulseResourceGroup --location westeurope
az appservice plan create --name ThePulsePlan --resource-group ThePulseResourceGroup --sku B1 --is-linux
az webapp create --name thepulseapp --resource-group ThePulseResourceGroup --plan ThePulsePlan --runtime "PYTHON:3.12"
```

**Configure Environment Variables:**
```bash
az webapp config appsettings set \
    --name thepulseapp \
    --resource-group ThePulseResourceGroup \
    --settings \
        SECRET_KEY="your-key" \
        DB_SERVER="thepulseserver.database.windows.net" \
        DB_NAME="THEPULSEDB" \
        DB_USERNAME="<username>" \
        DB_PASSWORD="<password>"
```

**Deploy:**
- Use Git deployment or ZIP file upload
- Configure startup command: `gunicorn --bind=0.0.0.0:8000 --timeout 600 app:app`
- Enable Azure SQL firewall for App Service IPs

### Production Recommendations
- Use Azure Key Vault for secrets
- Enable HTTPS only
- Configure autoscaling
- Enable Application Insights monitoring

---

**Last Updated:** October 31, 2025  
**For:** Project Handover to Continuing Development Team

---

**Good luck with the project! 🚀**
