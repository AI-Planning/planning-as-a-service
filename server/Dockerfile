# Build the Planutils image and install the selected packages

FROM aiplanning/planutils:latest

# FD Planner
RUN planutils install -f -y lama-first

# Satisficing classical planning
RUN planutils install -f -y dual-bfws-ffparser

#Optimal classical planning
RUN planutils install -f -y delfi

# top-k classical planning -- currently unavailable
# RUN planutils install -f -y forbiditerative-topk

# numeric planning
RUN planutils install -f -y enhsp

# PDDL3 support
RUN planutils install -f -y optic

# Temporal planning
RUN planutils install -f -y tfd

RUN mkdir /paas
COPY requirements.txt /paas/requirements.txt

RUN apt-get update
RUN apt-get install -y python3-dev default-libmysqlclient-dev build-essential

# install requirements
RUN python3 -m pip install --upgrade pip setuptools wheel
RUN python3 -m pip install -r /paas/requirements.txt

CMD /bin/bash
