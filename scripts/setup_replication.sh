#!/bin/bash
# setup_replication.sh

echo "Waiting for Master to be ready..."
until docker exec db-master mysqladmin -u root -proot_password ping &>/dev/null; do
  echo "Master not ready, waiting..."
  sleep 3
done
echo "Master is UP."
sleep 5


# Get Master Status
MASTER_STATUS=$(docker exec db-master mysql -u root -proot_password -e "SHOW MASTER STATUS\G")
LOG_FILE=$(echo "$MASTER_STATUS" | grep "File:" | awk '{print $2}')
POS=$(echo "$MASTER_STATUS" | grep "Position:" | awk '{print $2}')

echo "Master is at File: $LOG_FILE, Position: $POS"

if [ -z "$LOG_FILE" ]; then
    echo "Error: Could not get master status"
    exit 1
fi

configure_slave() {
    SLAVE_NAME=$1
    echo "Configuring $SLAVE_NAME..."
    docker exec $SLAVE_NAME mysql -u root -proot_password -e "STOP SLAVE; CHANGE MASTER TO MASTER_HOST='db-master', MASTER_USER='replicator', MASTER_PASSWORD='replica_pass', MASTER_LOG_FILE='$LOG_FILE', MASTER_LOG_POS=$POS; START SLAVE;"
    echo "$SLAVE_NAME configured."
}

configure_slave db-slave-1
configure_slave db-slave-2
configure_slave db-slave-3

echo "Replication setup complete."
