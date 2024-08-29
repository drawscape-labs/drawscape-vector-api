FROM continuumio/miniconda3

WORKDIR /app

COPY environment.yml .
RUN conda env create -f environment.yml

COPY . .

SHELL ["conda", "run", "-n", "drawscape_api", "/bin/bash", "-c"]

CMD gunicorn server:app