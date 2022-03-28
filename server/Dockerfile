# Build the Planutils image and install the selected packages

FROM aiplanning/planutils:latest

RUN planutils install -f -y lama-first
RUN planutils install -f -y kstar
RUN planutils install -f -y optic
RUN planutils install -f -y tfd
CMD /bin/bash