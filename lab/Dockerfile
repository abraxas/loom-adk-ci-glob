FROM python:3.13-slim

ENV LANG=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/opt/adk_agent \
    ADK_ROOT=/opt/adk_agent \
    STRANDS_ROOT=/opt/strands_agent \
    LAB_BIND=0.0.0.0 \
    LAB_PORT=18750

WORKDIR /lab

COPY src-v1.9.0/agents/adk_agent /opt/adk_agent
COPY src-v1.9.0/agents/strands_agent /opt/strands_agent
COPY lab_server.py /lab/lab_server.py

EXPOSE 18750
CMD ["python", "/lab/lab_server.py"]
