import os
import uuid
from PIL import Image
from .db import add_image, remove_image

def create_upload_dirs(base_dir='uploads'):
    """Cria diretórios para upload de imagens"""
    os.makedirs(base_dir, exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'thumbnails'), exist_ok=True)
    return base_dir

def process_image(file, upload_dir='uploads', max_size=(1200, 1200), thumb_size=(300, 300), quality=85):
    """Processa e redimensiona uma imagem enviada"""
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
        img.thumbnail(max_size, Image.LANCZOS)
        
        # Salvar imagem processada
        output_path = os.path.join(upload_dir, unique_filename)
        img.save(output_path, quality=quality, optimize=True)
        
        # Criar miniatura
        img.thumbnail(thumb_size, Image.LANCZOS)
        thumb_path = os.path.join(upload_dir, 'thumbnails', unique_filename)
        img.save(thumb_path, quality=quality, optimize=True)
        
        # Adicionar ao banco de dados
        add_image(unique_filename, file.filename)
        
        return unique_filename, None
    except Exception as e:
        return None, str(e)

def delete_image(filename, upload_dir='uploads'):
    """Remove uma imagem do sistema de arquivos e do banco de dados"""
    file_path = os.path.join(upload_dir, filename)
    thumb_path = os.path.join(upload_dir, 'thumbnails', filename)
    
    deleted_file = False
    deleted_thumb = False
    
    # Excluir arquivo principal
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            deleted_file = True
            print(f"Arquivo removido: {file_path}")
        except Exception as e:
            print(f"Erro ao remover arquivo {file_path}: {str(e)}")
    else:
        print(f"Arquivo não encontrado: {file_path}")
        
    # Excluir miniatura se existir
    if os.path.exists(thumb_path):
        try:
            os.remove(thumb_path)
            deleted_thumb = True
            print(f"Miniatura removida: {thumb_path}")
        except Exception as e:
            print(f"Erro ao remover miniatura {thumb_path}: {str(e)}")
    else:
        print(f"Miniatura não encontrada: {thumb_path}")
        
    # Se removeu pelo menos um dos arquivos ou se ambos não existem,
    # remover do banco de dados para garantir consistência
    if deleted_file or deleted_thumb or (not os.path.exists(file_path) and not os.path.exists(thumb_path)):
        # Remover do banco de dados
        from .db import remove_image, get_db_connection
        
        # Verificar se a imagem existe no banco antes de tentar remover
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM images WHERE filename = ?', (filename,))
        count = cursor.fetchone()['count']
        conn.close()
        
        if count > 0:
            remove_image(filename)
            print(f"Imagem removida do banco de dados: {filename}")
            return True
        else:
            print(f"Imagem não encontrada no banco de dados: {filename}")
            return False
    
    return deleted_file or deleted_thumb 