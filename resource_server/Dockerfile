FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install flask requests python-jose
CMD ["python", "app.py"]
