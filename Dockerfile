FROM python:3.10.7-slim

COPY . .
RUN pip install dist/*.whl
