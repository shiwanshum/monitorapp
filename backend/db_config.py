# db_config.py
DB_CONFIG = {
    'PG_MASTER_IP': "10.101.1.34",
    'PG_MASTER_PORT': 5432,
    'PG_USER': 'replica_user',
    'PG_PASS': 'replica_pass',
    'PG_DB_NAME': 'testdb',
    'PG_SLAVE1_IP': '10.101.1.34',
    'PG_SLAVE1_PORT': 5433,
    'PG_SLAVE2_IP': '10.101.1.50',
    'PG_SLAVE2_PORT': 5432,
    'PG_SLAVE2_DB_NAME': 'psql_db',
    'PG_SLAVE2_USER': 'admin',
    'PG_SLAVE2_PASS': 'admin123',


    'MYSQL_MASTER_IP': '10.101.1.32',
    'MYSQL_MASTER_PORT': 3307,
    'MYSQL_USER': 'root',
    'MYSQL_PASS': 'tei12345',
    'MYSQL_DB_NAME': 'testdb',
    'MYSQL_SLAVE1_IP': '10.101.1.32',
    'MYSQL_SLAVE1_PORT': 3308,
    'MYSQL_SLAVE2_IP': '10.101.1.50',
    'MYSQL_SLAVE2_PORT': 3306,
    'MYSQL_SLAVE2_DB_NAME': 'mysql_db',
    'MYSQL_SLAVE2_USER': 'admin',
    'MYSQL_SLAVE2_PASS': 'admin123',
}
