#!/bin/bash

# Ensure necessary directories exist for volumes
mkdir -p "${PWD}/postgres_data"
mkdir -p "${PWD}/mysql_data"

# Check if pg_hba.conf and mysql.conf exist in the current directory
if [ ! -f "${PWD}/pg_hba.conf" ]; then
    echo "pg_hba.conf not found in $(pwd). Please provide the file."
    exit 1
fi

if [ ! -f "${PWD}/mysql.conf" ]; then
    echo "mysql.conf not found in $(pwd). Please provide the file."
    exit 1
fi

# Create the Docker network db_network if it doesn't already exist
echo "Creating Docker network 'db_network'..."
docker network inspect db_network > /dev/null 2>&1 || \
  docker network create db_network

# Run PostgreSQL container
echo "Running PostgreSQL container..."
docker run -d \
  --name postgresdb \
  --network db_network \
  --restart unless-stopped \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=admin123 \
  -e POSTGRES_DB=psql_db \
  -p 5432:5432 \
  -v "${PWD}/pg_hba.conf:/etc/postgresql/postgresql.conf.d/pg_hba.conf" \
  -v "${PWD}/postgres_data:/var/lib/postgresql/data" \
  postgres:17 \
  bash -c "docker-entrypoint.sh postgres && \
  sleep 10 && \
  psql -U admin -d psql_db -c \"GRANT ALL PRIVILEGES ON DATABASE psql_db TO admin;\""

# Set environment variables for MySQL root password
MYSQL_ROOT_PASSWORD="root123"

# Run MySQL container
echo "Running MySQL container..."
docker run -d \
  --name mysqldb \
  --network db_network \
  -e MYSQL_ROOT_PASSWORD=$MYSQL_ROOT_PASSWORD \
  -e MYSQL_DATABASE=mysql_db \
  -e MYSQL_USER=admin \
  -e MYSQL_PASSWORD=admin123 \
  -p 3306:3306 \
  -v "${PWD}/mysql.conf:/etc/mysql/mysql.cnf" \
  -v "${PWD}/mysql_data:/var/lib/mysql" \
  --restart unless-stopped \
  mysql:8.0.43 \
  bash -c "docker-entrypoint.sh mysqld && \
  sleep 10 && \
  mysql -u root -p$MYSQL_ROOT_PASSWORD -e \"GRANT ALL PRIVILEGES ON *.* TO 'admin'@'%';\" && \
  mysql -u root -p$MYSQL_ROOT_PASSWORD -e \"ALTER USER 'admin'@'%' IDENTIFIED BY 'admin123';\" && \
  mysql -u root -p$MYSQL_ROOT_PASSWORD -e \"FLUSH PRIVILEGES;\""

# Run CloudBeaver container
echo "Running CloudBeaver container..."
docker run -d \
  --name cloudbeaver \
  --network db_network \
  -e CB_SERVER_HOST=0.0.0.0 \
  -e CB_SERVER_PORT=8080 \
  -p 8080:8080 \
  --restart unless-stopped \
  dbeaver/cloudbeaver:latest

# Sleep for a while to make sure containers have initialized
echo "Waiting for containers to initialize..."
sleep 10

# Create the docker-compose.yml based on the `docker run` commands
echo "Generating docker-compose.yml..."

cat <<EOF > docker-compose.yml
version: '3.8'

networks:
  db_network:
    driver: bridge

services:
  postgresdb:
    image: postgres:17
    container_name: postgresdb
    environment:
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: admin123
      POSTGRES_DB: psql_db
    ports:
      - "5432:5432"
    volumes:
      - "${PWD}/pg_hba.conf:/etc/postgresql/postgresql.conf.d/pg_hba.conf"
      - "${PWD}/postgres_data:/var/lib/postgresql/data"
    networks:
      - db_network
    entrypoint: >
      bash -c "docker-entrypoint.sh postgres && 
      sleep 10 && 
      psql -U admin -d psql_db -c \"GRANT ALL PRIVILEGES ON DATABASE psql_db TO admin;\""

  mysqldb:
    image: mysql:latest
    container_name: mysqldb
    environment:
      MYSQL_ROOT_PASSWORD: root123
      MYSQL_DATABASE: mysql_db
      MYSQL_USER: admin
      MYSQL_PASSWORD: admin123
    ports:
      - "3306:3306"
    volumes:
      - "${PWD}/mysql.conf:/etc/mysql/mysql.cnf"
      - "${PWD}/mysql_data:/var/lib/mysql"
    networks:
      - db_network
    entrypoint: >
      bash -c "docker-entrypoint.sh mysqld && 
      sleep 10 && 
      mysql -u root -p\$MYSQL_ROOT_PASSWORD -e \"GRANT ALL PRIVILEGES ON *.* TO 'admin'@'%';\" && 
      mysql -u root -p\$MYSQL_ROOT_PASSWORD -e \"ALTER USER 'admin'@'%' IDENTIFIED BY 'admin123';\" && 
      mysql -u root -p\$MYSQL_ROOT_PASSWORD -e \"FLUSH PRIVILEGES;\""

  cloudbeaver:
    image: dbeaver/cloudbeaver:latest
    container_name: cloudbeaver
    environment:
      CB_SERVER_HOST: 0.0.0.0
      CB_SERVER_PORT: 8080
    ports:
      - "8080:8080"
    networks:
      - db_network

volumes:
  postgres_data:
  mysql_data:
EOF

# Print confirmation
echo "Docker Compose file generated successfully as 'docker-compose.yml'."

# Check the status of the containers
echo "Checking the status of the containers..."
docker ps

echo "Deployment complete. You can now use 'docker-compose.yml' for future deployments."



sudo docker run -d \
  --name mysqldb \
  --network db_network \
  -e MYSQL_ROOT_PASSWORD=root123 \
  -e MYSQL_DATABASE=mysql_db \
  -e MYSQL_USER=admin \
  -e MYSQL_PASSWORD=admin123 \
  -p 3306:3306 \
  -v "${PWD}/mysql.conf:/etc/mysql/mysql.cnf" \
  -v "${PWD}/mysql_data:/var/lib/mysql" \
  --restart unless-stopped \
  mysql:8.0.43 \
  bash -c "docker-entrypoint.sh mysqld && \
  sleep 10 && \
  mysql -u root -proot123 -e \"GRANT ALL PRIVILEGES ON *.* TO 'admin'@'%';\" && \
  mysql -u root -proot123 -e \"ALTER USER 'admin'@'%' IDENTIFIED BY 'admin123';\" && \
  mysql -u root -proot123 -e \"FLUSH PRIVILEGES;\""