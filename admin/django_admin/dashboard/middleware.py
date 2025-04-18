from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
import re

class AdminStyleMiddleware(MiddlewareMixin):
    """
    Middleware para injetar estilos personalizados nas páginas do Admin Django.
    """
    def process_response(self, request, response):
        # Verificar se é uma página do admin
        if request.path.startswith('/admin/django/') and 'text/html' in response.get('Content-Type', ''):
            # CSS completo para substituir os estilos originais
            css = '''
            <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap" rel="stylesheet">
            <style>
                /* Reset básico */
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                /* Estilos base */
                body {
                    margin: 0;
                    padding: 0;
                    font-family: "Roboto", Arial, sans-serif;
                    color: #333;
                    background: #f8f8f8;
                    line-height: 1.5;
                }
                
                /* Cabeçalho */
                #header {
                    background: #417690;
                    color: white;
                    overflow: hidden;
                    padding: 10px 20px;
                }
                
                #branding h1 {
                    margin: 0;
                    font-weight: 300;
                    font-size: 24px;
                    color: #f5dd5d;
                }
                
                #user-tools {
                    float: right;
                    padding: 0;
                    margin: 0;
                    font-weight: 300;
                    font-size: 11px;
                    letter-spacing: 0.5px;
                    text-transform: uppercase;
                    text-align: right;
                }
                
                #user-tools a {
                    color: #fff;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.25);
                }
                
                #user-tools a:hover {
                    color: #f5dd5d;
                    border-bottom-color: #f5dd5d;
                    text-decoration: none;
                }
                
                /* Container e conteúdo */
                #container {
                    background: white;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                    margin: 20px;
                }
                
                #content {
                    padding: 20px;
                }
                
                /* Títulos */
                h1, h2, h3, h4, h5 {
                    color: #333;
                    font-weight: 500;
                    margin-bottom: 15px;
                }
                
                h1 {
                    font-size: 20px;
                }
                
                /* Links */
                a, a:visited {
                    color: #417690;
                    text-decoration: none;
                }
                
                a:hover {
                    color: #205067;
                    text-decoration: underline;
                }
                
                /* Breadcrumbs */
                div.breadcrumbs {
                    background: #417690;
                    padding: 10px 20px;
                    border: none;
                    color: white;
                }
                
                div.breadcrumbs a {
                    color: #f5dd5d;
                }
                
                div.breadcrumbs a:hover {
                    color: white;
                }
                
                /* Mensagens */
                ul.messagelist {
                    padding: 0;
                    margin: 0 0 10px 0;
                }
                
                ul.messagelist li {
                    padding: 10px 10px 10px 30px;
                    margin: 0 0 10px 0;
                    background: #dfd;
                    color: #333;
                    border-radius: 3px;
                }
                
                /* Botões */
                .button, input[type=submit], input[type=button], .submit-row input {
                    background: #417690;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 15px;
                    cursor: pointer;
                    margin: 2px 0;
                }
                
                .button:hover, input[type=submit]:hover, input[type=button]:hover, .submit-row input:hover {
                    background: #205067;
                }
                
                .button.default, input[type=submit].default, .submit-row input.default {
                    background: #417690;
                    font-weight: bold;
                }
                
                /* Módulos e tabelas */
                .module {
                    margin-bottom: 20px;
                    background: white;
                    border-radius: 3px;
                    border: 1px solid #ddd;
                }
                
                .module h2, .module caption {
                    background: #417690;
                    color: white;
                    padding: 8px 10px;
                    font-size: 14px;
                    margin: 0;
                    border-radius: 3px 3px 0 0;
                }
                
                table {
                    width: 100%;
                    border-collapse: collapse;
                }
                
                td, th {
                    padding: 8px;
                    border-bottom: 1px solid #eee;
                    vertical-align: top;
                    line-height: 1.3;
                }
                
                th {
                    font-weight: 600;
                    text-align: left;
                    background: #f8f8f8;
                    color: #333;
                }
                
                tr:nth-child(even) {
                    background: #f9f9f9;
                }
                
                /* Formulários */
                form {
                    margin: 0;
                    padding: 0;
                }
                
                fieldset {
                    border: none;
                    margin: 0;
                    padding: 0;
                }
                
                .form-row {
                    padding: 8px 12px;
                    border-bottom: 1px solid #eee;
                }
                
                label {
                    display: block;
                    margin-bottom: 4px;
                    color: #333;
                    font-weight: 500;
                }
                
                input, textarea, select {
                    padding: 6px 8px;
                    margin: 2px 0;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    font-family: "Roboto", Arial, sans-serif;
                    font-size: 13px;
                    box-sizing: border-box;
                }
                
                input:focus, textarea:focus, select:focus {
                    border-color: #417690;
                    outline: none;
                }
                
                /* Dashboard */
                .dashboard .module table td a {
                    display: block;
                    padding: 4px;
                }
                
                /* Fix para inputs e botões */
                .aligned label {
                    width: 160px;
                }
                
                .aligned .form-row input,
                .aligned .form-row textarea,
                .aligned .form-row select {
                    width: 300px;
                }
                
                /* Sobreescrevendo estilos principais */
                #header #branding h1 {
                    color: #f5dd5d !important;
                }
                
                .module h2, .module caption, .inline-group h2 {
                    background: #417690 !important;
                    color: white !important;
                }
                
                .button, input[type=submit], input[type=button], .submit-row input {
                    background: #417690 !important;
                    color: white !important;
                }
                
                .button:hover, input[type=submit]:hover, input[type=button]:hover, .submit-row input:hover {
                    background: #205067 !important;
                }
                
                div.breadcrumbs {
                    background: #417690 !important;
                }
                
                /* Assegurando que todos os textos sejam legíveis */
                body, p, label, .form-row, td, th {
                    color: #333 !important;
                }
                
                a, th a {
                    color: #417690 !important;
                }
                
                a:hover, th a:hover {
                    color: #205067 !important;
                }
                
                #content h1 {
                    color: #333 !important;
                }
            </style>
            '''
            
            # Processar a resposta para:
            # 1. Adicionar nosso CSS
            # 2. Se possível, remover links para arquivos CSS problemáticos
            content_str = response.content.decode('utf-8')
            
            # Adicionar nosso CSS antes de </head>
            content_str = content_str.replace('</head>', f'{css}</head>')
            
            # Substituir o conteúdo modificado
            response.content = content_str.encode('utf-8')
            
        return response 