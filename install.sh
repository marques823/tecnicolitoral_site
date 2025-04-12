#!/bin/bash

# Script de instalação para o servidor Técnico Litoral
# Este script configura o servidor como um serviço systemd que
# irá iniciar automaticamente na porta 9998

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Instalador do Servidor Web Técnico Litoral${NC}"
echo "=============================================="

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Este script precisa ser executado como root (sudo).${NC}"
  echo "Por favor, execute: sudo bash install.sh"
  exit 1
fi

# Definir variáveis
SERVICE_NAME="tecnicolitoral"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
SITE_DIR="/home/tiago/tecnicolitoral_site"

# Copiar o arquivo de serviço para a pasta systemd
echo -e "\n${YELLOW}Instalando o serviço...${NC}"
cp "$SITE_DIR/tecnicolitoral.service" "$SERVICE_FILE"

# Ajustar permissões
chmod 644 "$SERVICE_FILE"

# Recarregar serviços do systemd
echo -e "\n${YELLOW}Configurando o serviço...${NC}"
systemctl daemon-reload

# Habilitar o serviço para iniciar com o sistema
systemctl enable "$SERVICE_NAME.service"

# Iniciar o serviço
echo -e "\n${YELLOW}Iniciando o servidor na porta 9998...${NC}"
systemctl start "$SERVICE_NAME.service"

# Verificar status
sleep 2
if systemctl is-active --quiet "$SERVICE_NAME.service"; then
    echo -e "\n${GREEN}Servidor instalado e rodando com sucesso na porta 9998!${NC}"
    echo -e "Acesse o site em: ${GREEN}http://10.10.10.2:9998${NC}"
    echo -e "\nComandos úteis:"
    echo -e "  ${YELLOW}sudo systemctl status $SERVICE_NAME${NC} - Verificar status"
    echo -e "  ${YELLOW}sudo systemctl restart $SERVICE_NAME${NC} - Reiniciar servidor"
    echo -e "  ${YELLOW}sudo systemctl stop $SERVICE_NAME${NC} - Parar servidor"
    echo -e "  ${YELLOW}sudo systemctl disable $SERVICE_NAME${NC} - Desabilitar início automático"
else
    echo -e "\n${RED}Erro ao iniciar o servidor. Verifique o status:${NC}"
    echo -e "${YELLOW}sudo systemctl status $SERVICE_NAME${NC}"
fi

echo -e "\n${GREEN}Instalação concluída!${NC}" 