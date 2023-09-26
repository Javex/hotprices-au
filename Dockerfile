FROM python:3

RUN mkdir -p /app/output
WORKDIR /app
COPY ./main.py ./requirements.txt ./
RUN pip3 install -r requirements.txt
COPY hotprices_au ./hotprices_au
ENTRYPOINT [ "python3" ]