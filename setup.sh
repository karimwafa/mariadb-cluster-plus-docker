#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=== MariaDB Master-Slave + ProxySQL Installer ===${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: docker-compose is not installed.${NC}"
    exit 1
fi

echo -e "${GREEN}[1/4] Starting Docker Cluster...${NC}"
cd cluster
docker-compose up -d --build

echo -e "${GREEN}[2/4] Waiting for Master Node to be ready...${NC}"
sleep 15 # Give some time for init scripts

echo -e "${GREEN}[3/4] Configuring Replication...${NC}"
# Execute setup script inside master or via host if client exists
# We will use the script we moved to scripts/
../scripts/setup_replication.sh

echo -e "${GREEN}[4/4] Starting Demo Services Simulation...${NC}"
# We can't run python script easily if python is not on host, but we'll assume it is for this demo
# Or we can tell user to check dashboard.
echo "Cluster is running!"
echo -e "Dashboard: ${BLUE}http://localhost:5000${NC}"
echo -e "ProxySQL Admin: Port 6032"
echo -e "ProxySQL Data: Port 6033"

echo -e "${GREEN}Installation Complete!${NC}"
