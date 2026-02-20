FROM python:3

RUN mkdir -p /app/output
WORKDIR /app
COPY ./main.py ./requirements.txt ./
RUN pip3 install -r requirements.txt
RUN python3 -m camoufox fetch
RUN playwright install --with-deps chromium
RUN apt update && apt install -y libgtk-3-0 libx11-xcb1 libasound2
# Install AWS CLI
RUN curl --no-progress-meter "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
      unzip -q awscliv2.zip && \
      ./aws/install
COPY hotprices_au ./hotprices_au
ENTRYPOINT [ "python3", "/app/main.py" ]
