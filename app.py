from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for, make_response
import os
import json
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import datetime
from PIL import Image
import io
import uuid
import secrets  # Para gerar chaves seguras

app = Flask(__name__)
# Gerar uma chave secreta aleatória se não existir uma salva
SECRET_KEY_FILE = 'instance/secret_key'
os.makedirs(os.path.dirname(SECRET_KEY_FILE), exist_ok=True)

try:
    if os.path.exists(SECRET_KEY_FILE):
        with open(SECRET_KEY_FILE, 'r') as f:
            app.secret_key = f.read().strip()
    else:
        # Gerar uma nova chave secreta
        app.secret_key = secrets.token_hex(32)
        with open(SECRET_KEY_FILE, 'w') as f:
            f.write(app.secret_key)
        print("Nova chave secreta gerada e salva")
except Exception as e:
    print(f"Erro ao lidar com a chave secreta: {str(e)}")
    # Fallback para uma chave temporária (menos segura)
    app.secret_key = 'tecnicolitoral_temp_key_' + secrets.token_hex(8)

# Configurações de segurança da sessão 
app.config['SESSION_COOKIE_SECURE'] = False  # Desativado para desenvolvimento, ativar em produção
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=1)

# Outras configurações
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_IMAGE_SIZE'] = (1200, 1200)  # Tamanho máximo das imagens (largura, altura)
app.config['THUMBNAIL_SIZE'] = (300, 300)    # Tamanho das miniaturas
app.config['QUALITY'] = 85                   # Qualidade de compressão JPEG (0-100)
app.config['DATABASE'] = 'tecnicolitoral.db'  # Banco de dados SQLite

# Criar diretório de uploads se não existir
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails'), exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Criar tabela de configurações
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS config (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    ''')
    
    # Criar tabela de imagens
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        original_filename TEXT,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Inserir configurações padrão se não existirem
    default_config = {
        'contact_phone': '(XX) XXXXX-XXXX',
        'contact_whatsapp': '55XXXXXXXXXXX',
        'contact_email': 'contato@tecnicolitoral.com.br',
        'contact_address': 'Barra do Shay, São Sebastião - São Paulo',
        'about_text': 'A Técnico Litoral é uma empresa especializada em soluções de segurança eletrônica e automação, atendendo clientes residenciais e empresariais na região do litoral.\n\nContamos com profissionais experientes e qualificados, comprometidos em oferecer serviços de alta qualidade e atendimento personalizado.\n\nNossa missão é proporcionar tranquilidade e segurança através de soluções tecnológicas modernas e eficientes.',
        'admin_password': 'admin123',
        'logo_image': 'default_logo.png',
        'favicon_image': 'default_favicon.ico'
    }
    
    # Verificar se já existem configurações
    for key, value in default_config.items():
        cursor.execute('SELECT value FROM config WHERE key = ?', (key,))
        if not cursor.fetchone():
            cursor.execute('INSERT INTO config (key, value) VALUES (?, ?)', (key, value))
    
    conn.commit()
    conn.close()

# Inicializar banco de dados ao iniciar o aplicativo
init_db()

# Garantir que os diretórios e arquivos estáticos existam
os.makedirs('static/img', exist_ok=True)

# Verificar arquivos de logo e favicon padrão
default_logo_path = 'static/img/default_logo.png'
default_favicon_path = 'static/img/default_favicon.ico'

# Criar arquivos padrão se não existirem (pode ser substituído por arquivos reais mais tarde)
if not os.path.exists(default_logo_path):
    # Criar um logo simples como fallback
    try:
        img = Image.new('RGB', (200, 80), color = (0, 123, 255))
        d = Image.Draw(img)
        d.text((40, 30), "Técnico Litoral", fill=(255, 255, 255))
        img.save(default_logo_path)
    except Exception as e:
        print(f"Não foi possível criar o logo padrão: {e}")

if not os.path.exists(default_favicon_path):
    # Criar um favicon simples como fallback
    try:
        img = Image.new('RGB', (32, 32), color = (0, 123, 255))
        img.save(default_favicon_path)
    except Exception as e:
        print(f"Não foi possível criar o favicon padrão: {e}")

# Migrar dados do config.json para o banco de dados (se existir)
def migrate_from_json():
    try:
        if os.path.exists('config.json'):
            with open('config.json', 'r') as f:
                config = json.load(f)
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Migrar contatos
            if 'contact' in config:
                cursor.execute('UPDATE config SET value = ? WHERE key = ?', 
                              (config['contact'].get('phone', ''), 'contact_phone'))
                cursor.execute('UPDATE config SET value = ? WHERE key = ?', 
                              (config['contact'].get('whatsapp', ''), 'contact_whatsapp'))
                cursor.execute('UPDATE config SET value = ? WHERE key = ?', 
                              (config['contact'].get('email', ''), 'contact_email'))
                cursor.execute('UPDATE config SET value = ? WHERE key = ?', 
                              (config['contact'].get('address', ''), 'contact_address'))
            
            # Migrar texto sobre a empresa
            if 'about' in config and 'text' in config['about']:
                cursor.execute('UPDATE config SET value = ? WHERE key = ?', 
                              (config['about']['text'], 'about_text'))
            
            # Migrar senha do admin
            if 'admin' in config and 'password' in config['admin']:
                cursor.execute('UPDATE config SET value = ? WHERE key = ?', 
                              (config['admin']['password'], 'admin_password'))
            
            # Migrar imagens
            if 'gallery' in config and 'images' in config['gallery']:
                for image in config['gallery']['images']:
                    cursor.execute('INSERT OR IGNORE INTO images (filename) VALUES (?)', (image,))
            
            conn.commit()
            conn.close()
            
            # Renomear o arquivo JSON para backup
            os.rename('config.json', 'config.json.bak')
            print("Migração de config.json concluída e backup criado.")
    except Exception as e:
        print(f"Erro ao migrar do JSON: {str(e)}")

# Tentar migrar dados do JSON para o SQLite
migrate_from_json()

# Obter todas as configurações do banco de dados
def load_config():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT key, value FROM config')
    config_rows = cursor.fetchall()
    
    # Consultar imagens
    cursor.execute('SELECT filename FROM images ORDER BY uploaded_at DESC')
    images = [row['filename'] for row in cursor.fetchall()]
    
    conn.close()
    
    # Criar estrutura de configuração
    config = {
        'contact': {
            'phone': '',
            'whatsapp': '',
            'email': '',
            'address': ''
        },
        'about': {
            'text': ''
        },
        'gallery': {
            'images': images
        },
        'admin': {
            'password': ''
        },
        'branding': {
            'logo': '',
            'favicon': ''
        }
    }
    
    # Preencher com os valores do banco de dados
    for row in config_rows:
        key = row['key']
        value = row['value']
        
        if key == 'contact_phone':
            config['contact']['phone'] = value
        elif key == 'contact_whatsapp':
            config['contact']['whatsapp'] = value
        elif key == 'contact_email':
            config['contact']['email'] = value
        elif key == 'contact_address':
            config['contact']['address'] = value
        elif key == 'about_text':
            config['about']['text'] = value
        elif key == 'admin_password':
            config['admin']['password'] = value
        elif key == 'logo_image':
            config['branding']['logo'] = value
        elif key == 'favicon_image':
            config['branding']['favicon'] = value
    
    return config

# Salvar configuração específica
def save_config_value(key, value):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE config SET value = ? WHERE key = ?', (value, key))
    conn.commit()
    conn.close()

# Adicionar imagem ao banco de dados
def add_image(filename, original_filename=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO images (filename, original_filename) VALUES (?, ?)', 
                  (filename, original_filename))
    conn.commit()
    conn.close()

# Remover imagem do banco de dados
def remove_image(filename):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM images WHERE filename = ?', (filename,))
    conn.commit()
    conn.close()

# Processar e redimensionar imagem
def process_image(file):
    # Gerar nome único para o arquivo
    extension = os.path.splitext(file.filename)[1].lower()
    if extension not in ['.jpg', '.jpeg', '.png', '.gif']:
        return None, "Formato de arquivo não suportado. Use JPG, PNG ou GIF."
    
    unique_filename = f"{uuid.uuid4()}{extension}"
    
    try:
        # Abrir e processar a imagem
        img = Image.open(file)
        
        # Converter para RGB se for RGBA (PNG com transparência)
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        # Redimensionar a imagem mantendo a proporção
        img.thumbnail(app.config['MAX_IMAGE_SIZE'], Image.LANCZOS)
        
        # Salvar imagem processada
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        img.save(output_path, quality=app.config['QUALITY'], optimize=True)
        
        # Criar miniatura
        img.thumbnail(app.config['THUMBNAIL_SIZE'], Image.LANCZOS)
        thumb_path = os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails', unique_filename)
        img.save(thumb_path, quality=app.config['QUALITY'], optimize=True)
        
        return unique_filename, None
    except Exception as e:
        return None, str(e)

# Função para verificar se o usuário está logado
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return jsonify({'error': 'Unauthorized', 'message': 'Login required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Rotas
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/admin')
def admin():
    return send_from_directory('.', 'admin.html')

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Bad request', 'message': 'Username and password are required'}), 400
        
        # Verificar se o username é "admin"
        if username != "admin":
            return jsonify({'error': 'Unauthorized', 'message': 'Invalid credentials'}), 401
        
        # Carregar senha do admin do banco de dados
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM config WHERE key = ?', ('admin_password',))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'error': 'Server error', 'message': 'Admin password not configured'}), 500
        
        stored_password = result['value']
        
        # Verificar se é senha em texto plano ou hash
        password_valid = False
        
        # Verificação de texto plano (para compatibilidade)
        if stored_password == password:
            password_valid = True
            # Atualizar para hash na próxima vez
            hashed_password = generate_password_hash(password)
            save_config_value('admin_password', hashed_password)
        else:
            # Verificar se é uma senha em hash
            try:
                password_valid = check_password_hash(stored_password, password)
            except Exception:
                # Se falhar a verificação do hash, provavelmente não é um hash válido
                password_valid = False
        
        if password_valid:
            session['logged_in'] = True
            session.permanent = True
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            return jsonify({'error': 'Unauthorized', 'message': 'Invalid credentials'}), 401
            
    except Exception as e:
        print(f"Erro no login: {str(e)}")
        return jsonify({'error': 'Server error', 'message': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('logged_in', None)
    return jsonify({'success': True, 'message': 'Logout successful'})

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    if request.method == 'GET':
        config = load_config()
        # Não retornar a senha
        if 'admin' in config:
            config['admin'] = {'password': '********'}
        return jsonify(config)
    elif request.method == 'POST':
        # Verificar se está autenticado para modificar configurações
        if not session.get('logged_in'):
            return jsonify({'status': 'error', 'message': 'Não autenticado'}), 401
            
        data = request.json
        
        # Atualizar configurações no banco de dados
        if 'contact' in data:
            contact = data['contact']
            if 'phone' in contact:
                save_config_value('contact_phone', contact['phone'])
            if 'whatsapp' in contact:
                save_config_value('contact_whatsapp', contact['whatsapp'])
            if 'email' in contact:
                save_config_value('contact_email', contact['email'])
            if 'address' in contact:
                save_config_value('contact_address', contact['address'])
        
        if 'about' in data and 'text' in data['about']:
            save_config_value('about_text', data['about']['text'])
        
        if 'admin' in data and 'password' in data['admin'] and data['admin']['password']:
            # Gerar hash para a nova senha
            hashed_password = generate_password_hash(data['admin']['password'])
            save_config_value('admin_password', hashed_password)
        
        return jsonify({'status': 'success'})

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected'}), 400
    
    if file:
        # Processar e redimensionar imagem
        filename, error = process_image(file)
        if error:
            return jsonify({'status': 'error', 'message': error}), 400
        
        # Adicionar ao banco de dados
        add_image(filename, file.filename)
        
        return jsonify({'status': 'success', 'filename': filename})

@app.route('/api/delete/<filename>', methods=['DELETE'])
@login_required
def delete_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    thumb_path = os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails', filename)
    
    deleted = False
    
    # Excluir arquivo principal
    if os.path.exists(file_path):
        os.remove(file_path)
        deleted = True
        
    # Excluir miniatura se existir
    if os.path.exists(thumb_path):
        os.remove(thumb_path)
        
    if deleted:
        # Remover do banco de dados
        remove_image(filename)
        
        return jsonify({'status': 'success'})
    
    return jsonify({'status': 'error', 'message': 'File not found'}), 404

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/uploads/thumbnails/<filename>')
def thumbnail_file(filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails'), filename)

@app.route('/api/images')
def list_images():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT filename FROM images ORDER BY uploaded_at DESC')
    images = [row['filename'] for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'images': images})

@app.route('/api/image-status')
def image_status():
    """Verifica o status físico das imagens no sistema"""
    # Verificar imagens no banco de dados
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT filename FROM images ORDER BY uploaded_at DESC')
    db_images = [row['filename'] for row in cursor.fetchall()]
    conn.close()
    
    # Verificar arquivos físicos
    upload_dir = app.config['UPLOAD_FOLDER']
    existing_files = []
    missing_files = []
    
    for img in db_images:
        img_path = os.path.join(upload_dir, img)
        if os.path.exists(img_path):
            existing_files.append(img)
        else:
            missing_files.append(img)
    
    # Verificar diretório físico
    if os.path.exists(upload_dir):
        physical_files = [f for f in os.listdir(upload_dir) 
                        if os.path.isfile(os.path.join(upload_dir, f)) 
                        and not f.startswith('.') 
                        and f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
    else:
        physical_files = []
    
    orphaned_files = [f for f in physical_files if f not in db_images]
    
    return jsonify({
        'db_images': db_images,
        'existing_files': existing_files,
        'missing_files': missing_files,
        'physical_files': physical_files,
        'orphaned_files': orphaned_files,
        'upload_dir': upload_dir,
        'upload_dir_exists': os.path.exists(upload_dir)
    })

@app.route('/api/db-status')
def db_status():
    """Retorna o status atual do banco de dados e sistema de arquivos"""
    try:
        # Verificar imagens no banco de dados
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT filename FROM images ORDER BY uploaded_at DESC')
        db_images = [row['filename'] for row in cursor.fetchall()]
        conn.close()
        
        # Verificar arquivos físicos
        upload_dir = app.config['UPLOAD_FOLDER']
        existing_files = []
        missing_files = []
        
        for img in db_images:
            img_path = os.path.join(upload_dir, img)
            if os.path.exists(img_path):
                existing_files.append(img)
            else:
                missing_files.append(img)
        
        # Verificar diretório físico
        if os.path.exists(upload_dir):
            physical_files = [f for f in os.listdir(upload_dir) 
                            if os.path.isfile(os.path.join(upload_dir, f)) 
                            and not f.startswith('.')
                            and not os.path.isdir(os.path.join(upload_dir, f))
                            and f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
        else:
            physical_files = []
        
        # Encontrar arquivos órfãos (existem físicamente mas não no banco)
        orphaned_files = [f for f in physical_files if f not in db_images]
        
        return jsonify({
            'images': db_images,
            'images_count': len(db_images),
            'existing_files': existing_files,
            'missing_files': missing_files,
            'orphaned_files': orphaned_files,
            'total_physical_files': len(physical_files),
            'status': 'ok' if len(missing_files) == 0 else 'inconsistent'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/repair-db', methods=['POST'])
@login_required
def repair_db():
    """Repara inconsistências no banco de dados"""
    try:
        # Obter o estado atual
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Buscar imagens no banco
        cursor.execute('SELECT filename FROM images')
        db_images = [row['filename'] for row in cursor.fetchall()]
        
        # 2. Verificar arquivos físicos
        upload_dir = app.config['UPLOAD_FOLDER']
        
        # Arquivos que estão no banco mas não existem no disco
        missing_files = []
        for img in db_images:
            if not os.path.exists(os.path.join(upload_dir, img)):
                missing_files.append(img)
        
        # 3. Verificar arquivos no disco que não estão no banco
        if os.path.exists(upload_dir):
            physical_files = [f for f in os.listdir(upload_dir) 
                            if os.path.isfile(os.path.join(upload_dir, f)) 
                            and not f.startswith('.')
                            and f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
        else:
            physical_files = []
        
        orphaned_files = [f for f in physical_files if f not in db_images]
        
        # 4. Aplicar correções
        
        # Remover registros do banco que não existem no disco
        for img in missing_files:
            cursor.execute('DELETE FROM images WHERE filename = ?', (img,))
        
        # Adicionar registros no banco para arquivos que existem no disco
        for img in orphaned_files:
            cursor.execute('INSERT INTO images (filename) VALUES (?)', (img,))
        
        conn.commit()
        
        # 5. Verificar novo estado
        cursor.execute('SELECT filename FROM images')
        new_db_images = [row['filename'] for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'status': 'success',
            'corrections': {
                'corrections': {
                    'removed_from_db': missing_files,
                    'added_to_db': orphaned_files
                }
            },
            'new_status': {
                'images_count': len(new_db_images),
                'status': 'repaired'
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# Rota para processar o upload de um novo logo
@app.route('/api/upload-logo', methods=['POST'])
@login_required
def upload_logo():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected'}), 400
    
    # Verificar extensão
    ext = os.path.splitext(file.filename)[1].lower()
    allowed_extensions = ['.png', '.jpg', '.jpeg', '.svg', '.gif']
    
    if ext not in allowed_extensions:
        return jsonify({'status': 'error', 'message': f'Formato não suportado. Use {", ".join(allowed_extensions)}'}), 400
    
    try:
        # Gerar um nome de arquivo único
        unique_filename = f"logo_{uuid.uuid4()}{ext}"
        save_path = os.path.join('static/img', unique_filename)
        
        # Processar imagem
        img = Image.open(file)
        
        # Converter imagens com transparência
        if img.mode == 'RGBA' and ext not in ['.png', '.svg']:
            img = img.convert('RGB')
        
        # Redimensionar se necessário (max 300px de largura mantendo proporção)
        max_width = 300
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.LANCZOS)
        
        # Salvar
        img.save(save_path)
        
        # Atualizar configuração no banco de dados
        save_config_value('logo_image', unique_filename)
        
        return jsonify({
            'status': 'success',
            'message': 'Logo atualizado com sucesso',
            'filename': unique_filename
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Rota para processar o upload de um novo favicon
@app.route('/api/upload-favicon', methods=['POST'])
@login_required
def upload_favicon():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected'}), 400
    
    # Verificar extensão
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.ico', '.png']:
        return jsonify({'status': 'error', 'message': 'Formato não suportado. Use .ico ou .png'}), 400
    
    try:
        # Gerar um nome de arquivo único
        unique_filename = f"favicon_{uuid.uuid4()}{ext}"
        save_path = os.path.join('static/img', unique_filename)
        
        # Processar imagem
        img = Image.open(file)
        
        # Garantir que o tamanho do favicon é adequado
        if ext == '.png':
            img = img.resize((32, 32), Image.LANCZOS)
        
        # Salvar
        img.save(save_path)
        
        # Atualizar configuração no banco de dados
        save_config_value('favicon_image', unique_filename)
        
        return jsonify({
            'status': 'success',
            'message': 'Favicon atualizado com sucesso',
            'filename': unique_filename
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9998, debug=True) 