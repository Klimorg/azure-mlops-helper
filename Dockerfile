FROM python:3.11-slim

COPY . .
RUN pip install dist/*.whl
