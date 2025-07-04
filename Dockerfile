# Usa una imagen base con Python y soporte para instalar paquetes
FROM python:3.11-slim

# Evita preguntas durante la instalación
ENV DEBIAN_FRONTEND=noninteractive

# Instala dependencias necesarias del sistema
RUN apt-get update && \
    apt-get install -y gnupg2 curl apt-transport-https && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Crea y usa el directorio de la app
WORKDIR /app

# Copia los archivos de tu proyecto al contenedor
COPY . /app

# Instala las dependencias Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expone el puerto usado por Uvicorn
EXPOSE 10000

# Comando para iniciar el servidor
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
