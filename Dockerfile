FROM ollama/ollama:latest

WORKDIR /app
COPY . /app

# Install python, pip and venv
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv

# Create and activate virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies in the virtual environment
RUN pip install -r requirements.txt

# Run the application
CMD ["sh", "-c", "ollama serve & sleep 5 && python main.py"]