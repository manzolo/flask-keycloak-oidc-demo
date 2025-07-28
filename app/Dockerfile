FROM python:3.12-slim
WORKDIR /app
#COPY app.py .
#COPY templates .
COPY . .
RUN pip install flask requests python-dotenv
CMD ["python", "app.py"]
