# Instalacion

Para el correcto funcionamiento de la libreria pdal (lectura de archivos las/laz) es necesario el sistema
operativo Ubuntu, para aquellos que requiera correr la API en otro sistema recomiendo utilizar docker

`docker compose -f docker-compose.yaml  up --build -V -d`

En caso contrario, para python es necesario:

    apt-get install -y \
    python3 \
    python3-pip \
    pdal \
    libgdal-dev \
    python3-gdal

y luego las librerias del requirements.txt.

En el caso de la DB es necesario mongodb.

