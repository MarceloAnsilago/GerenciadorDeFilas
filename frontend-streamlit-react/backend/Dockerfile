# Usa uma imagem leve com Python
FROM python:3.11-slim

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos para dentro do container
COPY . /app

# Instala as dependências do projeto
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta que será usada pela API
EXPOSE 8080

# Executa o FastAPI com Uvicorn na porta correta
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
