# Painel Administrativo Técnico Litoral

Este é o painel administrativo para gerenciamento do site da Técnico Litoral, desenvolvido com Django.

## Requisitos

- Python 3.8+
- Virtualenv

## Configuração

### Linux/Mac

```bash
# Instalar virtualenv se não estiver instalado
pip install virtualenv

# Configurar e executar
chmod +x setup.sh
./setup.sh
```

### Windows

```bash
# Executar o script de configuração
setup.bat
```

## Acesso ao Painel

Após a instalação, o painel administrativo estará disponível em:

- URL: http://localhost:8000/admin
- Usuário: admin
- Senha: admin123

## Estrutura do Projeto

- `django_admin/` - Projeto Django principal
  - `dashboard/` - Aplicativo principal para o painel
  - `tecnicolitoral_admin/` - Configurações do projeto

## Desenvolvimento

Para rodar o projeto em modo de desenvolvimento:

```bash
cd admin
source venv/bin/activate  # No Windows: venv\Scripts\activate
cd django_admin
python manage.py runserver
``` 