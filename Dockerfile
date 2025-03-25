FROM python:3.11-slim

WORKDIR /app

#Instalar dependencias del sistema necesarias para PostgreSQL
RUN apt-get update && apt-get install -y libpq-dev gcc

# Copiar dependencias
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Exponer puerto
EXPOSE 3200

# Comando para ejecutar la aplicación
CMD ["python", "app.py"]