FROM python:3

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    gdal-bin \
    libgdal-dev \
    libboost-dev \
    python3-gdal \
    osmium-tool

ENV PATH="/osmium/bin:${PATH}"

RUN pip install osmsg

CMD ["/bin/bash"]
