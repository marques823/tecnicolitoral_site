from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for, make_response
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import datetime

from tecnicolitoral.database.db import init_db, migrate_from_json, load_config, save_config_value, get_db_connection, get_images, check_db_consistency
from tecnicolitoral.database.image_handler import create_upload_dirs, process_image, delete_image

# Obter o diretório raiz do projeto
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
app.secret_key = 'tecnicolitoral_secret_key'  # Chave secreta para sessões
app.config['UPLOAD_FOLDER'] = os.path.join(ROOT_DIR, 'uploads')
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=1)
app.config['MAX_IMAGE_SIZE'] = (1200, 1200)  # Tamanho máximo das imagens (largura, altura)
app.config['THUMBNAIL_SIZE'] = (300, 300)    # Tamanho das miniaturas
app.config['QUALITY'] = 85                   # Qualidade de compressão JPEG (0-100)

# Inicializar diretórios e banco de dados
create_upload_dirs(app.config['UPLOAD_FOLDER'])
init_db()
migrate_from_json()

# Decorator para verificar autenticação
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return jsonify({'status': 'error', 'message': 'Não autenticado'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Rotas
@app.route('/')
def index():
    return send_from_directory(ROOT_DIR, 'index.html')

@app.route('/admin')
def admin():
    return send_from_directory(ROOT_DIR, 'admin.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    config = load_config()
    
    if username == 'admin':
        # Verificar se a senha está em texto plano ou em hash
        stored_password = config['admin']['password']
        if stored_password == password:
            # Senha em texto plano
            session.permanent = True
            session['logged_in'] = True
            return jsonify({'status': 'success'})
        elif check_password_hash(stored_password, password):
            # Senha em hash
            session.permanent = True
            session['logged_in'] = True
            return jsonify({'status': 'success'})
    
    return jsonify({'status': 'error', 'message': 'Credenciais inválidas'}), 401

@app.route('/api/logout')
def logout():
    session.pop('logged_in', None)
    return jsonify({'status': 'success'})

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
        filename, error = process_image(
            file, 
            upload_dir=app.config['UPLOAD_FOLDER'],
            max_size=app.config['MAX_IMAGE_SIZE'],
            thumb_size=app.config['THUMBNAIL_SIZE'],
            quality=app.config['QUALITY']
        )
        
        if error:
            return jsonify({'status': 'error', 'message': error}), 400
        
        return jsonify({'status': 'success', 'filename': filename})

@app.route('/api/delete/<filename>', methods=['DELETE'])
@login_required
def delete_file(filename):
    if delete_image(filename, app.config['UPLOAD_FOLDER']):
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'File not found'}), 404

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/uploads/thumbnails/<filename>')
def thumbnail_file(filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails'), filename)

@app.route('/api/db-status')
@login_required
def db_status():
    """Rota para verificar o estado atual do banco de dados"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Obter informações das configurações
    cursor.execute('SELECT COUNT(*) as count FROM config')
    config_count = cursor.fetchone()['count']
    
    # Obter informações das imagens
    cursor.execute('SELECT COUNT(*) as count FROM images')
    images_count = cursor.fetchone()['count']
    
    # Listar todas as imagens
    images = get_images()
    
    # Verificar arquivos físicos
    existing_files = []
    missing_files = []
    
    for img in images:
        img_path = os.path.join(app.config['UPLOAD_FOLDER'], img)
        thumb_path = os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails', img)
        
        if os.path.exists(img_path):
            existing_files.append(img)
        else:
            missing_files.append(img)
    
    conn.close()
    
    return jsonify({
        'config_entries': config_count,
        'images_count': images_count,
        'images': images,
        'existing_files': existing_files,
        'missing_files': missing_files,
        'db_path': os.path.abspath(os.path.join(ROOT_DIR, 'tecnicolitoral.db')),
        'upload_dir': os.path.abspath(app.config['UPLOAD_FOLDER'])
    })

@app.route('/api/repair-db', methods=['POST'])
@login_required
def repair_db():
    """Rota para corrigir inconsistências no banco de dados"""
    result = check_db_consistency(app.config['UPLOAD_FOLDER'])
    
    # Após a correção, atualizar o status
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Obter informações das configurações
    cursor.execute('SELECT COUNT(*) as count FROM config')
    config_count = cursor.fetchone()['count']
    
    # Obter informações das imagens
    cursor.execute('SELECT COUNT(*) as count FROM images')
    images_count = cursor.fetchone()['count']
    
    conn.close()
    
    return jsonify({
        'success': True,
        'corrections': result,
        'new_status': {
            'config_entries': config_count,
            'images_count': images_count,
            'images': get_images()
        }
    })

# Verificar diretórios e permissões ao iniciar a aplicação
print(f"Diretório raiz: {ROOT_DIR}")
print(f"Diretório de uploads: {app.config['UPLOAD_FOLDER']}")
print(f"Base de dados: {os.path.join(ROOT_DIR, 'tecnicolitoral.db')}")

# Verificar permissões
upload_dir = app.config['UPLOAD_FOLDER']
thumb_dir = os.path.join(upload_dir, 'thumbnails')

# Garantir que os diretórios existam
if not os.path.exists(upload_dir):
    print(f"Criando diretório de uploads: {upload_dir}")
    os.makedirs(upload_dir, exist_ok=True)

if not os.path.exists(thumb_dir):
    print(f"Criando diretório de miniaturas: {thumb_dir}")
    os.makedirs(thumb_dir, exist_ok=True)

# Definir permissões corretas
try:
    import stat
    os.chmod(upload_dir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)  # 775
    os.chmod(thumb_dir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)  # 775
    print("Permissões de diretórios configuradas com sucesso")
except Exception as e:
    print(f"Erro ao definir permissões: {str(e)}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9998, debug=True) 