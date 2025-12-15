import time
import pymysql
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# Configuring DB Connections (Exposed Ports from Docker)
DB_CONFIG = {
    'master': {'host': '127.0.0.1', 'port': 3306, 'user': 'root', 'password': 'root_password', 'db': 'app_db'},
    'slave1': {'host': '127.0.0.1', 'port': 3307, 'user': 'root', 'password': 'root_password', 'db': 'app_db'},
    'slave2': {'host': '127.0.0.1', 'port': 3308, 'user': 'root', 'password': 'root_password', 'db': 'app_db'},
    'slave3': {'host': '127.0.0.1', 'port': 3309, 'user': 'root', 'password': 'root_password', 'db': 'app_db'},
    'proxysql': {'host': '127.0.0.1', 'port': 6033, 'user': 'laravel_user', 'password': 'laravel_pass', 'db': None}, # Data Port
}

def get_db_connection(config_name):
    cfg = DB_CONFIG[config_name]
    try:
        conn = pymysql.connect(
            host=cfg['host'],
            port=cfg['port'],
            user=cfg['user'],
            password=cfg['password'],
            database=cfg['db'],
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=1
        )
        return conn
    except Exception as e:
        print(f"Error connecting to {config_name}: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def status():
    # Helper to check a node
    def check_node(name):
        conn = get_db_connection(name)
        if not conn:
            return {'status': 'down', 'lag': 'N/A', 'role': 'Unknown'}
        
        if name == 'proxysql':
             return {'status': 'up', 'role': 'Load Balancer'}

        status_info = {'status': 'up', 'lag': 0, 'role': 'Master' if name == 'master' else 'Slave'}
        
        try:
            with conn.cursor() as cursor:
                # If slave, get replication lag
                if name != 'master':
                    cursor.execute("SHOW SLAVE STATUS")
                    slave_status = cursor.fetchone()
                    if slave_status:
                         # Seconds_Behind_Master can be None if replication stopped
                        lag = slave_status.get('Seconds_Behind_Master')
                        io_run = slave_status.get('Slave_IO_Running')
                        sql_run = slave_status.get('Slave_SQL_Running')
                        
                        status_info['io_thread'] = io_run
                        status_info['sql_thread'] = sql_run
                        status_info['lag'] = lag if lag is not None else 'Stopped'
                        
                        if io_run == 'No' or sql_run == 'No':
                            status_info['status'] = 'issues'
        except Exception:
            status_info['status'] = 'error'
        finally:
            conn.close()
        
        return status_info

    nodes = {
        'master': check_node('master'),
        'slave1': check_node('slave1'),
        'slave2': check_node('slave2'),
        'slave3': check_node('slave3'),
        'slave3': check_node('slave3'),
        'proxysql': check_node('proxysql')
    }
    return jsonify(nodes)

@app.route('/api/test/<service>')
def test_service(service):
    # Simulate the Service Logic
    master_conn = get_db_connection('master')
    if not master_conn:
        return jsonify({'error': 'Master DB Down'}), 500

    slave_mapping = {
        'go': ('slave1', 'Go Service'),
        'express': ('slave2', 'Express Service'),
        'laravel': ('slave3', 'Laravel Service')
    }
    
    if service not in slave_mapping:
        return jsonify({'error': 'Invalid Service'}), 400

    slave_key, service_name = slave_mapping[service]
    timestamp = int(time.time())
    user_name = f"{service_name}-User-{timestamp}"

    # Write to Master
    try:
        with master_conn.cursor() as cursor:
            cursor.execute("INSERT INTO users (name) VALUES (%s)", (user_name,))
            master_conn.commit()
    except Exception as e:
        return jsonify({'error': f"Write Failed: {str(e)}"}), 500
    finally:
        master_conn.close()

    # Wait briefly for replication
    time.sleep(0.5)

    # Read from Slave
    slave_conn = get_db_connection(slave_key)
    read_data = []
    slave_status = "Connected"
    
    if slave_conn:
        try:
            with slave_conn.cursor() as cursor:
                cursor.execute("SELECT id, name, created_at FROM users ORDER BY id DESC LIMIT 5")
                read_data = cursor.fetchall()
        except Exception as e:
            slave_status = f"Read Failed: {str(e)}"
        finally:
            slave_conn.close()
    else:
        slave_status = "Connection Failed"

    return jsonify({
        'service': service_name,
        'write_status': 'Success',
        'inserted_data': user_name,
        'read_source': slave_key,
        'read_status': slave_status,
        'data': read_data
    })

@app.route('/api/browse/<node>')
def browse_node(node):
    port_map = {
        'master': 3306,
        'slave1': 3307,
        'slave2': 3308,
        'slave3': 3309
    }
    
    if node not in port_map:
        return jsonify({'error': 'Invalid node'}), 400
        
    try:
        conn = pymysql.connect(
            host='127.0.0.1',
            port=port_map[node],
            user='root',
            password='root_password',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        data = {}
        with conn.cursor() as cursor:
            # Get list of databases to ignore
            ignored_dbs = "'information_schema', 'mysql', 'performance_schema', 'sys'"
            cursor.execute(f"SHOW DATABASES WHERE `Database` NOT IN ({ignored_dbs})")
            databases = [row['Database'] for row in cursor.fetchall()]
            
            for db_name in databases:
                data[db_name] = {}
                cursor.execute(f"USE {db_name}")
                cursor.execute("SHOW TABLES")
                tables = [list(row.values())[0] for row in cursor.fetchall()]
                
                for table in tables:
                    try:
                        cursor.execute(f"SELECT * FROM {table} LIMIT 5")
                        rows = cursor.fetchall()
                        data[db_name][table] = rows
                    except Exception as table_err:
                        data[db_name][table] = [] # Skip invalid tables
                    
        conn.close()
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
