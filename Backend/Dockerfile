# Use una imagen base de Python para Flask
FROM python:3.9-slim

# Establecer el directorio de trabajo en /app
WORKDIR /app

# Copiar los archivos de la aplicación Flask al contenedor
COPY ./requirements.txt /app/requirements.txt
COPY ./app.py /app/app.py
COPY ./static /app/static
COPY ./templates /app/templates

# Instalar las dependencias requeridas
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto en el que Flask se ejecutará
EXPOSE 80

# Ejecutar la aplicación Flask
CMD ["python", "app.py"]
