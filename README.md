# Técnico Litoral - Sistema Web

Site institucional com painel administrativo para a empresa Técnico Litoral, especializada em serviços de segurança eletrônica e automação.

## Características

- **Site responsivo**: Interface adaptável para dispositivos móveis e desktop
- **Painel administrativo**: Gerenciamento de conteúdo por interface web
- **Galeria de imagens**: Upload e gerenciamento de fotos
- **Banco de dados SQLite**: Armazenamento persistente sem necessidade de servidor de banco de dados
- **Processamento de imagens**: Redimensionamento e geração de miniaturas automáticos
- **Sistema de autenticação**: Proteção do painel administrativo com login e senha
- **Diagnóstico e reparo automático**: Verificação e correção de inconsistências no banco de dados

## Estrutura do Sistema

### Componentes Principais

- `app.py`: Aplicação principal Flask com rotas e funções
- `admin.html`: Interface administrativa para gestão de conteúdo
- `index.html`: Site principal da empresa
- `tecnicolitoral/`: Pacote Python com módulos para gerenciamento de dados e imagens
  - `tecnicolitoral/app.py`: Aplicação modularizada da versão mais recente
  - `tecnicolitoral/database/db.py`: Funções para manipulação do banco de dados SQLite
  - `tecnicolitoral/database/image_handler.py`: Processamento e gerenciamento de imagens

### Banco de Dados

O sistema utiliza SQLite para armazenamento de dados com as seguintes tabelas:
- `config`: Armazena configurações como contatos, senha de administrador e textos
  - Chaves principais: contact_phone, contact_whatsapp, contact_email, contact_address, about_text, admin_password
- `images`: Mantém registro das imagens enviadas e seus metadados
  - Armazena: filename, original_filename, uploaded_at

### Sistema de Arquivos

- `uploads/`: Diretório para armazenamento das imagens enviadas
- `uploads/thumbnails/`: Subdiretório contendo miniaturas automáticas (300x300px)

### Processamento de Imagens

O sistema realiza automaticamente:
- Geração de nomes únicos baseados em UUID para evitar conflitos
- Redimensionamento de imagens grandes (máx. 1200x1200px)
- Criação de miniaturas para visualização rápida (300x300px)
- Otimização de imagens para reduzir tamanho de arquivo
- Conversão de formatos com transparência para formatos web

## Funcionalidades

### Painel Administrativo

- **Autenticação**: Proteção por login e senha
- **Edição de contatos**: Telefone, WhatsApp, e-mail e endereço
- **Edição de textos**: Informações sobre a empresa
- **Gerenciamento de imagens**: Upload e exclusão de imagens
- **Diagnóstico do banco de dados**: Verificação e correção automática de inconsistências

### API

O sistema disponibiliza os seguintes endpoints:

- `/api/config`: Retorna/atualiza configurações do site
- `/api/login`: Autenticação de administradores
- `/api/logout`: Encerramento de sessão
- `/api/upload`: Upload de imagens
- `/api/delete/<filename>`: Exclusão de imagens
- `/api/images`: Lista todas as imagens disponíveis
- `/api/image-status`: Verifica status de integridade do banco de imagens
- `/api/repair-db`: Repara inconsistências no banco de dados

## Mecanismos de Segurança e Estabilidade

- **Verificação de consistência**: Detecção e correção automática de inconsistências entre banco de dados e sistema de arquivos
- **Processamento de imagens**: Validação de formato, redimensionamento e otimização
- **Autenticação por sessão**: Proteção do painel administrativo
- **Hash de senha**: Armazenamento seguro da senha do administrador
- **Backup automático**: Preservação de dados durante migração
- **Recuperação robusta**: Sistema em cascata de recuperação para garantir exibição correta de imagens:
  1. Verifica configurações no banco de dados
  2. Consulta API de imagens diretamente
  3. Verifica arquivos físicos no sistema

## Migração de Dados

O sistema suporta migração automática de um formato JSON anterior para SQLite:
- Detecta a presença do arquivo `config.json`
- Migra as configurações para o banco de dados SQLite
- Cria um backup do arquivo JSON original
- Mantém a compatibilidade com versões anteriores do sistema

## Como Instalar

1. Clone o repositório
2. Instale as dependências: `pip install -r requirements.txt`
3. Execute a aplicação: `PYTHONPATH=$PWD ./run.py`
4. Acesse o site: `http://localhost:9998/`
5. Acesse o painel administrativo: `http://localhost:9998/admin` (usuário: admin, senha: admin123)

## Requisitos do Sistema

- Python 3.6+
- Bibliotecas: Flask, Pillow, Werkzeug (veja `requirements.txt` para a lista completa)
- Acesso ao sistema de arquivos para armazenamento de imagens
- Navegador web moderno

## Manutenção

### Verificação de Consistência do Banco de Dados

O painel administrativo possui botões específicos para:
1. **Verificar Banco de Dados**: Exibe o estado atual de todas as imagens
2. **Reparar Banco de Dados**: Corrige automaticamente as inconsistências

### Solução de Problemas Comuns

- **Imagens não aparecem**: Use o botão de verificação e reparo no painel administrativo
- **Banco de dados danificado**: Delete o arquivo `tecnicolitoral.db` e reinicie a aplicação (ele será recriado automaticamente)
- **Problemas de upload**: Verifique as permissões da pasta `uploads/`

## Implantação em Produção

Para usar este sistema em um ambiente de produção, recomendamos as seguintes configurações:

### Usando Gunicorn e Nginx

1. **Instale o Gunicorn**:
   ```
   pip install gunicorn
   ```

2. **Crie um arquivo de serviço systemd** (exemplo em `tecnicolitoral.service`):
   ```
   [Unit]
   Description=Tecnico Litoral Web Service
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/caminho/para/tecnicolitoral_site
   Environment="PATH=/caminho/para/venv/bin"
   ExecStart=/caminho/para/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 tecnicolitoral.app:app

   [Install]
   WantedBy=multi-user.target
   ```

3. **Configure o Nginx** como proxy reverso:
   ```
   server {
       listen 80;
       server_name seu-dominio.com www.seu-dominio.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }

       location /uploads {
           alias /caminho/para/tecnicolitoral_site/uploads;
       }
   }
   ```

4. **Permissões**:
   ```bash
   # Ajuste as permissões da pasta uploads
   sudo chown -R www-data:www-data /caminho/para/tecnicolitoral_site/uploads
   sudo chmod -R 755 /caminho/para/tecnicolitoral_site/uploads
   ```

5. **Ative e inicie o serviço**:
   ```bash
   sudo systemctl enable tecnicolitoral.service
   sudo systemctl start tecnicolitoral.service
   ```

### Segurança em Produção

- Altere a senha padrão do administrador imediatamente
- Defina uma chave secreta forte em `app.py` (app.secret_key)
- Configure HTTPS com Let's Encrypt
- Faça backup regular do banco de dados SQLite e das imagens
- Defina limites de tamanho para arquivos de upload no Nginx 