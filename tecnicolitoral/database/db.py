import sqlite3
import os
import json

# Obter o diretório raiz do projeto
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_FILE = os.path.join(ROOT_DIR, 'tecnicolitoral.db')

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
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
        filename TEXT NOT NULL UNIQUE,
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
        'about_text': 'A Técnico Litoral é uma empresa especializada em soluções de segurança eletrônica e automação, atendendo clientes residenciais e empresariais na região do litoral.',
        'admin_password': 'admin123'
    }
    
    # Verificar se já existem configurações
    for key, value in default_config.items():
        cursor.execute('SELECT value FROM config WHERE key = ?', (key,))
        if not cursor.fetchone():
            cursor.execute('INSERT INTO config (key, value) VALUES (?, ?)', (key, value))
    
    conn.commit()
    conn.close()

def migrate_from_json():
    config_file = os.path.join(ROOT_DIR, 'config.json')
    config_backup = os.path.join(ROOT_DIR, 'config.json.bak')
    
    if not os.path.exists(config_file):
        return False
        
    try:
        with open(config_file, 'r') as f:
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
                cursor.execute('''
                INSERT OR IGNORE INTO images (filename) 
                VALUES (?)
                ''', (image,))
        
        conn.commit()
        conn.close()
        
        # Renomear arquivo original para backup
        os.rename(config_file, config_backup)
        print(f"Migração de {config_file} concluída e backup criado em {config_backup}.")
        return True
    
    except Exception as e:
        print(f"Erro ao migrar do JSON: {str(e)}")
        return False

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
        'logo_image': '',
        'favicon_image': ''
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
            config['logo_image'] = value
        elif key == 'favicon_image':
            config['favicon_image'] = value
    
    return config

def save_config_value(key, value):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE config SET value = ? WHERE key = ?', (value, key))
    conn.commit()
    conn.close()

def add_image(filename, original_filename=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR IGNORE INTO images (filename, original_filename) 
    VALUES (?, ?)
    ''', (filename, original_filename))
    conn.commit()
    conn.close()

def remove_image(filename):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM images WHERE filename = ?', (filename,))
    conn.commit()
    conn.close()

def get_images():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT filename FROM images ORDER BY uploaded_at DESC')
    images = [row['filename'] for row in cursor.fetchall()]
    conn.close()
    return images

def check_db_consistency(upload_dir='uploads'):
    """Verifica e corrige inconsistências entre o banco de dados e o sistema de arquivos"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Obter todas as imagens do banco de dados
    cursor.execute('SELECT id, filename FROM images')
    db_images = cursor.fetchall()
    
    # Verificar arquivos físicos
    missing_files = []
    for img in db_images:
        img_path = os.path.join(upload_dir, img['filename'])
        if not os.path.exists(img_path):
            missing_files.append((img['id'], img['filename']))
    
    # Obter todos os arquivos no diretório de uploads
    filesystem_images = []
    if os.path.exists(upload_dir):
        for filename in os.listdir(upload_dir):
            if os.path.isfile(os.path.join(upload_dir, filename)):
                # Ignorar arquivos ocultos e não-imagens
                if not filename.startswith('.') and filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    filesystem_images.append(filename)
    
    # Encontrar imagens no sistema de arquivos mas não no banco de dados
    db_filenames = [img['filename'] for img in db_images]
    orphaned_files = [f for f in filesystem_images if f not in db_filenames]
    
    # Informações de diagnóstico
    print(f"Total de imagens no banco de dados: {len(db_images)}")
    print(f"Total de imagens no sistema de arquivos: {len(filesystem_images)}")
    print(f"Imagens ausentes no sistema de arquivos: {len(missing_files)}")
    print(f"Imagens órfãs no sistema de arquivos: {len(orphaned_files)}")
    
    # Corrigir inconsistências
    corrections = {
        'removed_from_db': [],
        'added_to_db': []
    }
    
    # 1. Remover registros de imagens ausentes no sistema de arquivos
    for img_id, filename in missing_files:
        cursor.execute('DELETE FROM images WHERE id = ?', (img_id,))
        corrections['removed_from_db'].append(filename)
    
    # 2. Adicionar registros para imagens órfãs no sistema de arquivos
    for filename in orphaned_files:
        cursor.execute('INSERT INTO images (filename) VALUES (?)', (filename,))
        corrections['added_to_db'].append(filename)
    
    # Salvar alterações
    conn.commit()
    conn.close()
    
    # Retornar informações sobre as correções realizadas
    return {
        'missing_files': [f for _, f in missing_files],
        'orphaned_files': orphaned_files,
        'corrections': corrections
    } 