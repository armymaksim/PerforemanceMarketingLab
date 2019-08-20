FROM python:3.6
RUN mkdir -p /var/voltmobi /usr/local/etc/image_manager/
COPY ./ /var/voltmobi
RUN pip3 install --upgrade pip && pip3 install /var/voltmobi
WORKDIR /var/voltmobi