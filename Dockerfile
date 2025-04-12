FROM python:3.10-slim

WORKDIR /app

# Instalar dependências necessárias para a Pillow e SQLite
RUN apt-get update && apt-get install -y \
    gcc \
    libc6-dev \
    libffi-dev \
    libjpeg-dev \
    zlib1g-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro para aproveitar o cache do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código da aplicação
COPY . .

# Tornar o script de entrada executável
RUN chmod +x docker-entrypoint.sh

# Criar os diretórios necessários
RUN mkdir -p instance uploads/thumbnails data && \
    chmod -R 777 instance uploads data

# Expor a porta
EXPOSE 9998

# Usar o script de entrada como ponto de entrada
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Comando para iniciar a aplicação
CMD ["gunicorn", "--bind", "0.0.0.0:9998", "--workers", "3", "app:app"] 