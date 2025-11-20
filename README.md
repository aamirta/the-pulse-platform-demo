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
5. [Deployment on Azure](#6--deployment-on-azure)

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


## 2. 🧩 Architecture Overview

### High-Level System Design

<img width="650" height="721" alt="image" src="https://github.com/user-attachments/assets/8624792a-ecce-4f34-8b5d-db058e62679f" />


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
│   ├── startups.html          # Startup listing with advanced filters
│   ├── startup_detail.html    # Detailed startup profile page
│   ├── founders.html          # Founder listing with search/filters
│   ├── founder_detail.html    # Founder profile with experience, education, startups
│   ├── investors.html         # Investor directory with filters
│   ├── investor_detail.html   # Investor profile with portfolio and funding rounds
│   ├── incubator_detail.html  # Incubator/Accelerator profile with startups
│   └── aboutus.html           # About page with team/mission info
│____
```

### Key Files

- **app.py** - Main Flask application with routes and authentication
- **models.py** - SQLAlchemy database models (11 entities)
- **Functions.py** - Helper functions for data aggregation and analytics
- **requirements.txt** - Python dependencies
- **templates/** - Jinja2 HTML templates for all pages

---

## 4. 🚀 Setup Instructions

## Overview

The Pulse Platform is already deployed on Azure App Service. These instructions are for local development purposes only.

---

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+** (Developed and tested with Python 3.12)
- **ODBC Driver 17 for SQL Server** ([Download here](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server))
- **Access to Azure SQL Database** or **local Microsoft SQL Server**

---

## 📦 Quick Start Guide

### 1. Clone the Repository

```bash
git clone https://github.com/younessmalhouni/ThePulsePlateform.git
cd ThePulseApp
```

### 2. Set Up Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Windows Command Prompt:
.\venv\Scripts\activate.bat

# macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Database Connection

You have two options for database setup:

---

## 🗄️ Database Setup Options

### Option 1: Use Existing Azure Database (Recommended)

This is the quickest way to get started as the database is already configured and populated with data.

#### Connection Details

| Parameter | Value |
|-----------|-------|
| **Server** | `thepulseserver.database.windows.net` |
| **Database** | `THEPULSEDB` |
| **Authentication** | SQL Server Authentication |
| **Driver** | ODBC Driver 17 for SQL Server |

#### Setup Steps

1. **Get Database Credentials**
   - Contact the project owner to obtain the username and password

2. **Update Connection String**
   
   Open `app.py` and update the `SQLALCHEMY_DATABASE_URI`:
   
   ```python
   app.config['SQLALCHEMY_DATABASE_URI'] = (
       "mssql+pyodbc://USERNAME:PASSWORD@thepulseserver.database.windows.net/THEPULSEDB"
       "?driver=ODBC+Driver+17+for+SQL+Server"
       "&Encrypt=yes&TrustServerCertificate=no&Connection Timeout=100"
   )
   ```
   
   Replace `USERNAME` and `PASSWORD` with your actual credentials.

3. **Configure Azure Firewall**
   
   - Go to [Azure Portal](https://portal.azure.com/)
   - Navigate to **SQL databases** → **THEPULSEDB**
   - Select **Set server firewall** from the top menu
   - Add your client IP address to the firewall rules
   - Click **Save**

4. **Test Connection**
   
   Run a simple test to verify database connectivity:
   
   ```bash
   python app.py
   ```

---

### Option 2: Create New Database

If you need to set up a fresh database instance, choose one of the following methods:

#### Method A: Azure SQL Database

1. **Create Azure SQL Resources**
   
   - Navigate to [Azure Portal](https://portal.azure.com/)
   - Create a new **SQL Server** (or use an existing one)
   - Create a new **SQL Database** within that server
   - Note down the server name, database name, and credentials

2. **Initialize Database Schema**
   
   - Once deployment is complete, access your database resource
   - In the left menu, navigate to **Query Editor**
   - Sign in using the credentials you set during database creation
   - Open the `Database.sql` file from the repository
   - Copy and paste the entire SQL schema script
   - Execute the script to create all tables and relationships

3. **Populate Database with Data**
   
   The schema is now created, but the database needs to be populated with data:
   
   - Clone the data insertion project:
     ```bash
     git clone https://github.com/younessmalhouni/TestProject.git
     ```
   - Follow the detailed instructions in that repository's README to:
     - Configure data source connections
     - Run the data collection scripts
     - Insert collected data into your new database
   
   - Once data insertion is complete, your database setup is finished

4. **Update Application Configuration**
   
   Update the connection string in `app.py` with your new database details:
   
   ```python
   app.config['SQLALCHEMY_DATABASE_URI'] = (
       "mssql+pyodbc://YOUR_USERNAME:YOUR_PASSWORD@YOUR_SERVER.database.windows.net/YOUR_DATABASE"
       "?driver=ODBC+Driver+17+for+SQL+Server"
       "&Encrypt=yes&TrustServerCertificate=no&Connection Timeout=100"
   )
   ```

#### Method B: Local SQL Server

1. **Install SQL Server Tools**
   
   - Download and install [Microsoft SQL Server Management Studio 20](https://docs.microsoft.com/en-us/sql/ssms/download-sql-server-management-studio-ssms)
   - Ensure SQL Server is running on your local machine

2. **Create Local Database**
   
   - Open SQL Server Management Studio (SSMS)
   - Connect to your local SQL Server instance
   - Right-click on **Databases** → **New Database**
   - Name your database (e.g., `THEPULSEDB_LOCAL`)
   - Click **OK** to create

3. **Execute Schema Script**
   
   - Click **New Query** in the toolbar
   - Open the `Database.sql` file from the repository
   - Copy and paste the entire SQL script
   - Click **Execute** to create all database objects

4. **Insert Data**
   
   - Clone and run the data insertion project:
     ```bash
     git clone https://github.com/younessmalhouni/TestProject.git
     ```
   - Follow the instructions in that repository's README to populate your local database

5. **Configure Local Connection String**
   
   Update `app.py` with your local SQL Server connection:
   
   ```python
   app.config['SQLALCHEMY_DATABASE_URI'] = (
       "mssql+pyodbc://YOUR_USERNAME:YOUR_PASSWORD@localhost/THEPULSEDB_LOCAL"
       "?driver=ODBC+Driver+17+for+SQL+Server"
       "&Trusted_Connection=yes"  # For Windows Authentication
   )
   ```

---

## ▶️ Running the Application

Once your database is configured:

```bash
python app.py
```

The application will start and be accessible at:

**http://127.0.0.1:5000/**

---

## 📚 Additional Resources

- [Azure SQL Database Documentation](https://docs.microsoft.com/en-us/azure/azure-sql/)
- [Flask-SQLAlchemy Documentation](https://flask-sqlalchemy.palletsprojects.com/)
- [Data Insertion Project Repository](https://github.com/younessmalhouni/TestProject.git)

---

## 4. ☁️ Deployment on Azure
## Current Deployment Status

The Pulse Platform is currently deployed and running on Microsoft Azure with the following resources:

- ✅ **Azure SQL Database** - Data persistence and storage
- ✅ **Azure App Service** - Web application hosting

---

## 🏗️ Azure Resources Overview

<img width="1143" height="900" alt="Azure Resources Diagram" src="https://github.com/user-attachments/assets/f5bff3ef-b7b5-4178-ac7f-de1f00352f78" />

*Figure: Azure resources created and configured for The Pulse Platform deployment*

---

## 🗄️ Azure SQL Database Configuration

### Service Tier: General Purpose (GP S Gen5)

The database is configured with a serverless compute tier optimized for cost-effectiveness and automatic scaling based on workload demands.

#### **Compute Tier: Serverless**

| Configuration | Value | Description |
|---------------|-------|-------------|
| **Compute Model** | Serverless | Auto-scales compute resources based on workload activity |
| **Billing Model** | Per-second billing | Charged only for vCores used per second |
| **Hardware Generation** | Standard-series (Gen5) | Latest generation Intel processors |
| **Max vCores** | 2 vCores | Maximum compute capacity allocated |
| **Min vCores** | 0.5 vCores | Minimum compute capacity when idle |
| **Memory** | Up to 240 GB | Maximum memory available (scales with vCores) |

#### **Memory Allocation**

- **Min Memory:** 2.05 GB (at 0.5 vCores)
- **Max Memory:** 6 GB (at 2 vCores)
- Memory scales proportionally with vCore usage

#### **Storage Configuration**

| Parameter | Value |
|-----------|-------|
| **Estimated Storage Cost** | $5.70 USD/month |
| **Allocated Log Space** | 9.6 GB |
| **Data Max Size** | 32 GB |
| **Compute Cost (per vCore/second)** | 0.000159 USD |


### ⚙️ Auto-Pause Delay Configuration

The **Auto-Pause Delay** feature is currently **enabled** and configured to **1 hour** of inactivity.  
After one hour without activity, the database will automatically pause to optimize resource consumption.

When the database is paused and a new connection is attempted, you may see an error such as:

> **Error:**  
> `Database 'THEPULSEDB' on server 'thepulseserver.database.windows.net' is not currently available. Please retry the connection later...`

This behavior is **expected**. As soon as a request is made, the database automatically resumes and becomes available again.  
A short delay may occur during this wake-up process.

#### 💡 Why Auto-Pause Is Enabled  
Since the platform is still in a **testing phase**, enabling Auto-Pause is a **good practice** to reduce unnecessary compute costs.

#### 🚀 For Production Use  
When the application moves to **production**, it is recommended to **disable Auto-Pause** to ensure continuous availability and eliminate the initial wake-up delay.


#### 🌐 Networking
we Enabled "Allow Azure services and resources to access this server" :

All **Azure services and resources** are allowed to access the SQL Server.  
This configuration ensures that requests originating from the **Azure App Service** can successfully connect to the database without connection restrictions.



## 🌐 Azure App Service Configuration

### Service Details

| Configuration | Value |
|---------------|-------|
| **Hosting Plan** | Azure App Service Plan |
| **Region** | Germany West Central |
| **Runtime Stack** | Python 3.12 |
| **Operating System** | Linux |


### Service Plan: Basic B1

The application is hosted on Azure App Service with the following specifications:

| Configuration | Value | Description |
|---------------|-------|-------------|
| **Pricing Tier** | Basic B1 |  |
| **ACU/vCPU** | 100 ACU | Azure Compute Units for performance measurement |
| **vCPU** | 1 vCore | Dedicated virtual CPU core |
| **Memory** | 1.75 GB | RAM allocated for application |
| **Remote Storage** | 10 GB | Disk space for application files |
| **Scale (instances)** | Up to 3 | Manual scaling capability |
| **SLA** | 99.95% | Uptime guarantee |
| **Cost per Hour** | $0.018 USD | Pay-as-you-go pricing |
| **Cost per Month** | $13.155 USD | Estimated monthly cost (730 hours) |

### 🌍 Custom Domain

The domain **thepulse.ma** was **purchased from Genious**.  
To make it accessible through our **Azure App Service**, we configured a custom domain mapping between **Genious DNS settings** and the **Azure App Service**.  

For detailed configuration steps, we followed the official Microsoft documentation:  
[👉 Configure a custom domain in Azure App Service](https://learn.microsoft.com/en-us/azure/app-service/app-service-web-tutorial-custom-domain?tabs=root%2Cazurecli)


### Deployment Method

The platform is deployed to **Azure App Service** using **GitHub Actions** for continuous deployment.  

Each time new code is pushed to this repository, an automated deployment process is triggered based on the workflow defined in:  
`.github/workflows/main_thepulse.yml`


---

## 💰 Cost Summary

### Monthly Estimated Costs

| Service | Configuration | Estimated Cost |
|---------|---------------|----------------|
| **Azure SQL Database** | Serverless GP S Gen5 (0.5-2 vCores) | ~$5.70/month (storage) + compute usage |
| **Azure App Service** | Basic B1 | ~$13.155/month |
| **Total Estimated** | - | ~$18.855/month |

---


## 📚 Additional Resources

- [Azure SQL Database Serverless Documentation](https://docs.microsoft.com/en-us/azure/azure-sql/database/serverless-tier-overview)
- [Azure App Service Documentation](https://docs.microsoft.com/en-us/azure/app-service/)
- [Azure Cost Management](https://docs.microsoft.com/en-us/azure/cost-management-billing/)
- [Azure Security Best Practices](https://docs.microsoft.com/en-us/azure/security/fundamentals/best-practices-and-patterns)

