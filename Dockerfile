FROM python:3

RUN mkdir -p /app/output
WORKDIR /app
COPY ./main.py ./requirements.txt ./
RUN pip3 install -r requirements.txt
RUN python3 -m camoufox fetch
RUN apt update && apt install -y libgtk-3-0 libx11-xcb1 libasound2
COPY hotprices_au ./hotprices_au
ENTRYPOINT [ "python3", "main.py" ]
