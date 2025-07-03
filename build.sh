#!/bin/bash
set -e

# Actualizar paquetes
apt-get update

# Instalar herramientas necesarias
apt-get install -y curl gnupg unixodbc-dev

# Agregar repositorio de Microsoft para ODBC
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update

# Instalar ODBC driver
ACCEPT_EULA=Y apt-get install -y msodbcsql17

# Instalar dependencias Python
pip install -r requirements.txt
