FROM python:3.12-slim

WORKDIR /workspace

# Install system dependencies (Prisma needs openssl and libatomic1 for nodeenv node)
RUN apt-get update && apt-get install -y openssl libatomic1 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./app/
RUN pip install --no-cache-dir -r app/requirements.txt

COPY . ./app/

# Generate Prisma client
ENV PRISMA_SKIP_POSTINSTALL_GENERATE=1
RUN cd app && prisma generate

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--ws", "wsproto"]
