# Use una imagen base de Node.js
FROM node:14-slim

# Establecer el directorio de trabajo en /app
WORKDIR /app

# Copiar los archivos del frontend al contenedor
COPY ./ /app/

# Instalar las dependencias del frontend
RUN npm install

# Exponer el puerto en el que Express se ejecutará
EXPOSE 3000

# Ejecutar la aplicación Node.js
CMD ["npm", "start"]
