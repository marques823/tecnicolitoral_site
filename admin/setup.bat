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