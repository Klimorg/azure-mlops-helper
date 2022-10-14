FROM python:3.10.0-slim

COPY . .
RUN pip install dist/*.whl
