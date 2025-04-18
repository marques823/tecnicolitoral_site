@echo off
echo Configurando o ambiente Django...

:: Verificar se o ambiente virtual existe
if not exist venv (
    echo Criando ambiente virtual...
    python -m venv venv
)

:: Ativar ambiente virtual
call venv\Scripts\activate

:: Instalar dependências
echo Instalando dependências...
pip install -r requirements.txt

:: Verificar se o projeto Django já existe
if not exist django_admin\manage.py (
    echo Criando projeto Django...
    django-admin startproject tecnicolitoral_admin django_admin
    
    :: Criar app principal
    cd django_admin
    python manage.py startapp dashboard
    cd ..
    
    echo Configurando settings.py manualmente...
    echo Por favor, verifique se as seguintes configurações foram aplicadas:
    echo 1. Adicione 'localhost', '127.0.0.1' e '*' ao ALLOWED_HOSTS
    echo 2. Configure o idioma para 'pt-br' e o fuso horário para 'America/Sao_Paulo'
    echo 3. Adicione 'dashboard', 'rest_framework' e 'corsheaders' aos INSTALLED_APPS
    echo 4. Adicione 'corsheaders.middleware.CorsMiddleware' ao MIDDLEWARE
    echo 5. Adicione CORS_ALLOW_ALL_ORIGINS = True ao final do arquivo
    pause
)

:: Aplicar migrações
echo Aplicando migrações...
cd django_admin
python manage.py makemigrations
python manage.py migrate

:: Criar superusuário se não existir
python manage.py shell -c "from django.contrib.auth.models import User; print('Superuser exists') if User.objects.filter(is_superuser=True).exists() else User.objects.create_superuser('admin', 'admin@tecnicolitoral.com', 'admin123')"

:: Iniciar servidor
echo Iniciando servidor Django...
python manage.py runserver 0.0.0.0:8000 