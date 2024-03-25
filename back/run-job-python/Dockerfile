FROM public.ecr.aws/lambda/python:3.10


#install required packages for building c++ code
RUN yum install -y gcc-c++ make cmake3 git cmake



# clone repo if it is changed the commits will be different and the docker cache will be invalidated
ADD https://api.github.com/repos/cloudmrhub-com/tess/commits version.json
RUN git clone https://github.com/cloudmrhub-com/tess
RUN pip install git+https://github.com/cloudmrhub-com/tess
#compile tess

RUN cd tess && mkdir build && cd build && cmake ../CpTemperature && make && make install
# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}
ENV TESS_BIN cpptemperature
# Install the specified packages
RUN pip install -r requirements.txt


# Copy function code
COPY lambda_function.py ${LAMBDA_TASK_ROOT}
ENV SSL_CERT_FILE /etc/ssl/certs/ca-bundle.crt

#install cmrawspy
ADD https://api.github.com/repos/erosmontin/cmrawspy/commits version.json
RUN pip install git+https://github.com/erosmontin/cmrawspy.git
RUN mkdir ${LAMBDA_TASK_ROOT}/run-job-python
COPY job.json ${LAMBDA_TASK_ROOT}/run-job-python/job.json


# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "lambda_function.handler" ]


