############################################################
# Dockerfile to build a quality control container for pediatric T1 MR images
# Based on Ubuntu
############################################################

FROM ubuntu:16.04

RUN apt-get update && apt-get install -y \
    python3-nibabel \
    python3-numpy \
    python3-scipy \
    python3-sklearn \
    python3-pip

RUN pip3 install keras tensorflow h5py

ADD ./t1qc.py ~/t1qc.py
ADD ./ibis-qc.hdf5 ~/ibis-qc.hdf5

RUN ["mkdir", "~/.keras"]
ADD ./keras.json ~/.keras/keras.json

VOLUME ["/data"]

ENTRYPOINT ["python3", "~/t1qc.py", "/data"]
