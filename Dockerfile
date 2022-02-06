FROM python:3.8

WORKDIR /opt/install
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get install -y git make curl chafa lynx lcdf-typetools
RUN git clone https://github.com/alexmyczko/fnt.git
WORKDIR fnt
RUN make install
RUN fnt update
RUN fnt install agave
RUN fnt install rowdies
RUN fnt install montserrat
RUN fnt install poppins
RUN fnt install oswald
RUN fnt install ubuntu
RUN fnt install merriweather

WORKDIR /opt/quotes-slackbot

COPY init.sh ./
RUN ./init.sh

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY src setup.py config.json ./
RUN pip install .
CMD python -m quotes_slackbot.__main__