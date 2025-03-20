#Todo esto es una prueba por aquello
FROM python:3.11-slim

WORKDIR /app

#Instala dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#Copia el código de la aplicación
COPY . .

#Expone el puerto
EXPOSE 3200

#Comando para ejecutar la aplicación
CMD ["python", "app.py"]