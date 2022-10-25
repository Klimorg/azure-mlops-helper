FROM python:3.11.0-slim

COPY . .
RUN pip install dist/*.whl
