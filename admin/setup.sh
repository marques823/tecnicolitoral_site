#!/bin/bash

# Diretório onde o script está
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

echo "Configurando o ambiente Django..."
cd "$SCRIPT_DIR"

# Ativar ambiente virtual
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv
fi

source venv/bin/activate

# Instalar dependências
echo "Instalando dependências..."
pip install -r requirements.txt

# Verificar se o projeto Django já existe
if [ ! -f "django_admin/manage.py" ]; then
    echo "Criando projeto Django..."
    django-admin startproject tecnicolitoral_admin django_admin
    
    # Criar app principal
    cd django_admin
    python manage.py startapp dashboard
    cd ..
    
    # Configurar ALLOWED_HOSTS
    sed -i "s/ALLOWED_HOSTS = \[\]/ALLOWED_HOSTS = \['localhost', '127.0.0.1', '10.10.10.2', '*'\]/" django_admin/tecnicolitoral_admin/settings.py
    
    # Configurar idioma e fuso horário
    sed -i "s/LANGUAGE_CODE = 'en-us'/LANGUAGE_CODE = 'pt-br'/" django_admin/tecnicolitoral_admin/settings.py
    sed -i "s/TIME_ZONE = 'UTC'/TIME_ZONE = 'America\/Sao_Paulo'/" django_admin/tecnicolitoral_admin/settings.py
    
    # Adicionar apps ao settings.py
    sed -i "/INSTALLED_APPS = \[/a\    'dashboard',\n    'rest_framework',\n    'corsheaders'," django_admin/tecnicolitoral_admin/settings.py
    
    # Adicionar middleware CORS
    sed -i "/SessionMiddleware',/a\    'corsheaders.middleware.CorsMiddleware'," django_admin/tecnicolitoral_admin/settings.py
    
    # Adicionar configuração CORS
    echo -e "\n# Configurações CORS\nCORS_ALLOW_ALL_ORIGINS = True" >> django_admin/tecnicolitoral_admin/settings.py
fi

# Aplicar migrações
echo "Aplicando migrações..."
cd django_admin
python manage.py makemigrations
python manage.py migrate

# Criar superusuário se não existir
echo "Verificando superusuário..."
python manage.py shell -c "from django.contrib.auth.models import User; print('Superuser exists') if User.objects.filter(is_superuser=True).exists() else User.objects.create_superuser('admin', 'admin@tecnicolitoral.com', 'admin123')"

# Iniciar servidor
echo "Iniciando servidor Django..."
python manage.py runserver 0.0.0.0:8000 