#!/bin/bash
set -e

# Criar diretórios necessários
mkdir -p /app/instance
mkdir -p /app/uploads/thumbnails
mkdir -p /app/data

# Definir permissões
chmod -R 777 /app/instance /app/uploads /app/data

# Verificar se a variável de ambiente DATABASE_PATH está definida
if [ -n "$DATABASE_PATH" ]; then
    # Modificar a configuração da aplicação para usar o caminho do banco de dados
    sed -i "s|app.config\['DATABASE'\] = 'tecnicolitoral.db'|app.config\['DATABASE'\] = '$DATABASE_PATH'|g" app.py
    echo "Configuração do banco de dados atualizada para: $DATABASE_PATH"
fi

# Iniciar a aplicação
exec "$@" 