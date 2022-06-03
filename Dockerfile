FROM python:2

WORKDIR /root
RUN apt-get update && apt-get install -y python-requests python-libxml2 python-yaml && apt-get clean
#RUN python -m pip install requests lxml pyyaml

COPY *.py basicauth.csv tests.zip ./
COPY appd_API/*.py ./appd_API/

#ENTRYPOINT ["/usr/bin/python"]
CMD ["/root/test.py"]