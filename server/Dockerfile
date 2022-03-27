# Stage 0: Build Celery worker

FROM aiplanning/planutils:latest

# Branch name for the latest Planutils
ENV LATEST_BRANCH=main
RUN git clone https://github.com/AI-Planning/planutils.git
WORKDIR planutils
RUN git checkout ${LATEST_BRANCH}
RUN pip uninstall planutils --yes
RUN python3 setup.py install --old-and-unmanageable
RUN echo "y" | planutils setup


RUN planutils install -f -y lama-first
RUN planutils install -f -y kstar
RUN planutils install -f -y optic
RUN planutils install -f -y tfd
CMD /bin/bash