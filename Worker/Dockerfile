# Use una imagen base del SDK de .NET para compilar la aplicación
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build-env

# Establecer el directorio de trabajo en /app
WORKDIR /app

# Copiar el archivo csproj y restaurar las dependencias
COPY ./Worker/*.csproj ./
RUN dotnet restore

# Copiar todo el código y compilar la aplicación
COPY ./Worker/ ./
RUN dotnet publish -c Release -o out

# Use una imagen base más ligera para ejecutar la aplicación
FROM mcr.microsoft.com/dotnet/runtime:8.0
WORKDIR /app
COPY --from=build-env /app/out .

# Ejecutar la aplicación al iniciar el contenedor
CMD ["dotnet", "Worker.dll"]
