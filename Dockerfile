FROM python:3

RUN mkdir -p /app/output
WORKDIR /app
COPY ./coles.py ./woolies.py ./requirements.txt ./
RUN pip3 install -r requirements.txt
ENTRYPOINT [ "python3" ]