FROM fimbaz/algorand-datanet101:latest
COPY block2.py
RUN apt-get -y install python3.8 python3-venv
RUN pip install -r requirements.txt