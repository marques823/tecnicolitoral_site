#!/usr/bin/env python3
"""
Inicializa a aplicação Técnico Litoral
"""
from tecnicolitoral.app import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9998, debug=True)
