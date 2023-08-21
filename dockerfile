FROM python:3
WORKDIR /

COPY . / 


RUN apt-get update && \
    apt-get install -y software-properties-common vim && \
    rm -rf /var/lib/apt/lists/*


RUN add-apt-repository ppa:ubuntugis/ppa


RUN apt-get install -y \
    python3 \
    python3-pip \
    pdal \
    libgdal-dev \
    python3-gdal

RUN export CPLUS_INCLUDE_PATH=/usr/include/gdal
RUN export C_INCLUDE_PATH=/usr/include/gdal


COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt



CMD ["uvicorn","app:app", "--host", "0.0.0.0" , "--reload"]