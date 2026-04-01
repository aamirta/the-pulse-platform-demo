#!/usr/bin/env bash
# Install Microsoft ODBC Driver 17 for SQL Server on Render (Ubuntu/Debian)
set -e

apt-get update
apt-get install -y curl gnupg2 apt-transport-https

curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/ubuntu/22.04/prod jammy main" > /etc/apt/sources.list.d/mssql-release.list

apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev

pip install --upgrade pip
pip install -r requirements.txt
