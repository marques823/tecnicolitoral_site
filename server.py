#!/usr/bin/env python3
import http.server
import socketserver
import os
import socket
import argparse
import json
import cgi
import base64
from urllib.parse import parse_qs, urlparse

# Parsing dos argumentos de linha de comando
parser = argparse.ArgumentParser(description='Servidor web para o site da Técnico Litoral')
parser.add_argument('-p', '--port', type=int, default=9998, help='Porta para o servidor (padrão: 9998)')
parser.add_argument('-a', '--address', type=str, default='0.0.0.0', help='Endereço IP para o servidor (padrão: 0.0.0.0 - todas as interfaces)')
args = parser.parse_args()

# Configurações do servidor
HOST = args.address
PORT = args.port
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(DIRECTORY, 'uploads')
CONFIG_FILE = os.path.join(DIRECTORY, 'config.json')

# Criar diretório de uploads se não existir
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Carregar configuração
def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "contact": {
                "phone": "",
                "whatsapp": "",
                "email": "",
                "address": ""
            },
            "about": {
                "text": ""
            },
            "gallery": {
                "images": []
            },
            "admin": {
                "password": "admin123"  # Senha padrão
            }
        }

# Salvar configuração
def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
        self.config = load_config()

    def check_auth(self):
        auth_header = self.headers.get('Authorization')
        if not auth_header:
            print("No auth header")
            return False
        
        try:
            auth_type, auth_string = auth_header.split(' ')
            if auth_type.lower() != 'basic':
                print("Invalid auth type:", auth_type)
                return False
            
            decoded = base64.b64decode(auth_string).decode('utf-8')
            username, password = decoded.split(':')
            print(f"Auth attempt - Username: {username}, Password: {password}")
            print(f"Expected password: {self.config.get('admin', {}).get('password', 'admin123')}")
            
            # Verificar se a senha está correta
            expected_password = self.config.get('admin', {}).get('password', 'admin123')
            if username == 'admin' and password == expected_password:
                print("Authentication successful")
                return True
            else:
                print("Authentication failed - Username or password incorrect")
                return False
        except Exception as e:
            print("Auth error:", str(e))
            return False

    def do_GET(self):
        print(f"GET request for: {self.path}")
        
        # Tratar rotas especiais
        if self.path == '/admin' or self.path == '/admin/':
            self.path = '/admin.html'
            return super().do_GET()
        elif self.path == '/':
            self.path = '/index.html'
            return super().do_GET()
        elif self.path == '/api/config':
            if not self.check_auth():
                self.send_response(401)
                self.send_header('WWW-Authenticate', 'Basic realm="Admin Area"')
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': 'Authentication required'}).encode())
                return
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(self.config).encode())
        else:
            # Para arquivos estáticos, verificar se é uma imagem da galeria
            if self.path.startswith('/uploads/'):
                file_path = os.path.join(DIRECTORY, self.path[1:])
                if os.path.exists(file_path):
                    self.send_response(200)
                    self.send_header('Content-type', 'image/jpeg')
                    with open(file_path, 'rb') as f:
                        self.wfile.write(f.read())
                    return
            return super().do_GET()

    def do_POST(self):
        if self.path == '/api/config':
            if not self.check_auth():
                self.send_response(401)
                self.send_header('WWW-Authenticate', 'Basic realm="Admin Area"')
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': 'Authentication required'}).encode())
                return

            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            config = json.loads(post_data.decode('utf-8'))
            save_config(config)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'success'}).encode())
        elif self.path == '/api/upload':
            if not self.check_auth():
                self.send_response(401)
                self.send_header('WWW-Authenticate', 'Basic realm="Admin Area"')
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': 'Authentication required'}).encode())
                return

            try:
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST'}
                )
                
                if 'file' not in form:
                    raise ValueError('Nenhum arquivo enviado')
                
                file_item = form['file']
                if not file_item.filename:
                    raise ValueError('Nome do arquivo inválido')
                
                # Criar diretório de uploads se não existir
                if not os.path.exists(UPLOAD_DIR):
                    os.makedirs(UPLOAD_DIR)
                
                # Salvar arquivo
                file_path = os.path.join(UPLOAD_DIR, file_item.filename)
                with open(file_path, 'wb') as f:
                    f.write(file_item.file.read())
                
                # Atualizar configuração
                config = load_config()
                if file_item.filename not in config['gallery']['images']:
                    config['gallery']['images'].append(file_item.filename)
                    save_config(config)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success'}).encode())
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_DELETE(self):
        if self.path.startswith('/api/delete/'):
            if not self.check_auth():
                self.send_response(401)
                self.send_header('WWW-Authenticate', 'Basic realm="Admin Area"')
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': 'Authentication required'}).encode())
                return

            try:
                filename = self.path.split('/')[-1]
                file_path = os.path.join(UPLOAD_DIR, filename)
                
                if os.path.exists(file_path):
                    os.remove(file_path)
                    
                    # Atualizar configuração
                    config = load_config()
                    if filename in config['gallery']['images']:
                        config['gallery']['images'].remove(filename)
                        save_config(config)
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'status': 'success'}).encode())
                else:
                    raise FileNotFoundError('Arquivo não encontrado')
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

# Criar e iniciar o servidor
try:
    with socketserver.TCPServer((HOST, PORT), Handler) as httpd:
        host_ip = socket.gethostbyname(socket.gethostname())
        print(f"Servidor iniciado!")
        print(f"Acesse o site localmente em: http://localhost:{PORT}")
        print(f"Acesse o site na rede local em: http://{host_ip}:{PORT}")
        print(f"Acesse o site na rede local (IP específico): http://10.10.10.2:{PORT}")
        print(f"Acesse o painel administrativo em: http://localhost:{PORT}/admin")
        print("Usuário: admin")
        print("Senha padrão: admin123")
        print("Pressione Ctrl+C para encerrar o servidor")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor encerrado.")
except OSError as e:
    print(f"Erro ao iniciar o servidor: {e}")
    print(f"Verifique se a porta {PORT} já está em uso.")
    print("Tente uma porta diferente com: python3 server.py --port NUMERO_DA_PORTA") 