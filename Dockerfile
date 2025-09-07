FROM ollama/ollama:latest

WORKDIR /app
COPY . /app

RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip3 install -r requirements.txt --break-system-packages --break-system-packages --break-system-packages --break-system-packages

CMD ["sh", "-c", "ollama serve & sleep 5 && python3 main.py"]