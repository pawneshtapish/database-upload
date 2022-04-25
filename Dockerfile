FROM python:3.8
EXPOSE 5000
WORKDIR /database-upload
ADD . /database-upload
RUN pip3 install -r requirements.txt
CMD python3 app.py
