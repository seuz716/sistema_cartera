#!/bin/bash
# Script de Arraque Profesional - DevOps Senior
# Inicia el sistema ERP Cartera con un solo click

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}>>> Iniciando Sistema de Cartera ERP (Docker Engine)...${NC}"

# 1. Verificar Docker
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}[ERROR] El motor de Docker no está en ejecución. Por favor, inícielo.${NC}"
    exit 1
fi

# 2. Levantar los servicios con Docker Compose
echo -e "${BLUE}>>> Construyendo y levantando contenedores (Producción)...${NC}"
docker compose up -d --build

# 3. Validar estado de los servicios
echo -e "${BLUE}>>> Validando salud de los contenedores...${NC}"
sleep 5
WEB_STATUS=$(docker inspect -f '{{.State.Running}}' sistema-cartera-web)
DB_STATUS=$(docker inspect -f '{{.State.Running}}' sistema-cartera-db)

if [ "$WEB_STATUS" = "true" ] && [ "$DB_STATUS" = "true" ]; then
    echo -e "${GREEN}[OK] Sistema Cartera operativo.${NC}"
else
    echo -e "${RED}[ERROR] Algunos servicios no iniciaron correctamente.${NC}"
    docker compose logs --tail=20
    exit 1
fi

# 4. Obtener IP Local
IP_LOCAL=$(hostname -I | awk '{print $1}')
if [ -z "$IP_LOCAL" ]; then
    IP_LOCAL="localhost"
fi

URL_SISTEMA="http://$IP_LOCAL:8000"

echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}  SISTEMA CARTERA LISTO PARA USAR EN: ${NC}"
echo -e "${BLUE}  $URL_SISTEMA${NC}"
echo -e "${GREEN}==================================================${NC}"

# 5. Intentar abrir el navegador automáticamente (compatible con Linux GUI)
if command -v xdg-open > /dev/null; then
    xdg-open "$URL_SISTEMA" 2>/dev/null &
elif command -v open > /dev/null; then
    open "$URL_SISTEMA" 2>/dev/null &
fi

echo -e "${BLUE}Presiona cualquier tecla para cerrar esta ventana o Ctrl+C.${NC}"
read -n 1 -s
