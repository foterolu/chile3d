# Instalacion

Para el correcto funcionamiento de la libreria pdal (lectura de archivos las/laz) es necesario el sistema
operativo Ubuntu, para aquellos que requiera correr la API en otro sistema recomiendo utilizar docker

`sudo docker build -t chile-3d . && sudo docker run --network=host -p 8000:8000/tcp -it chile-3d `

En caso contrario, es necesario:

    apt-get install -y \
    python3 \
    python3-pip \
    pdal \
    libgdal-dev \
    python3-gdal

y luego las librerias del requirements.txt
