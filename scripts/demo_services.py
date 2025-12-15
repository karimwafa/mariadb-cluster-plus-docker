import pymysql
import time
import sys

# Configurations
DB_CONFIG = {
    'master': {'host': '127.0.0.1', 'port': 3306, 'user': 'root', 'password': 'root_password', 'db': 'app_db'},
    'slave1': {'host': '127.0.0.1', 'port': 3307, 'user': 'root', 'password': 'root_password', 'db': 'app_db'},
    'slave2': {'host': '127.0.0.1', 'port': 3308, 'user': 'root', 'password': 'root_password', 'db': 'app_db'},
    'slave3': {'host': '127.0.0.1', 'port': 3309, 'user': 'root', 'password': 'root_password', 'db': 'app_db'},
}

def get_connection(node_name):
    cfg = DB_CONFIG[node_name]
    try:
        return pymysql.connect(
            host=cfg['host'],
            port=cfg['port'],
            user=cfg['user'],
            password=cfg['password'],
            database=cfg['db'],
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=2
        )
    except Exception as e:
        print(f"Failed to connect to {node_name}: {e}")
        return None

def go_service_action():
    print("\n--- Go Service (Master -> Slave 1) ---")
    # Write
    conn_master = get_connection('master')
    if conn_master:
        with conn_master.cursor() as cursor:
            name = f"Go-User-{int(time.time())}"
            cursor.execute("INSERT INTO users (name) VALUES (%s)", (name,))
            conn_master.commit()
            print(f"[WRITE] Inserted '{name}' to Master.")
        conn_master.close()
    
    time.sleep(1) # Wait for replication
    
    # Read
    conn_slave = get_connection('slave1')
    if conn_slave:
        with conn_slave.cursor() as cursor:
            cursor.execute("SELECT * FROM users ORDER BY id DESC LIMIT 3")
            rows = cursor.fetchall()
            print(f"[READ] Data from Slave-1:")
            for row in rows:
                print(f"  - {row}")
        conn_slave.close()

def express_service_action():
    print("\n--- Express Service (Master -> Slave 2) ---")
    conn_master = get_connection('master')
    if conn_master:
        with conn_master.cursor() as cursor:
            name = f"Express-User-{int(time.time())}"
            cursor.execute("INSERT INTO users (name) VALUES (%s)", (name,))
            conn_master.commit()
            print(f"[WRITE] Inserted '{name}' to Master.")
        conn_master.close()
    
    time.sleep(1)
    
    conn_slave = get_connection('slave2')
    if conn_slave:
        with conn_slave.cursor() as cursor:
            cursor.execute("SELECT * FROM users ORDER BY id DESC LIMIT 3")
            rows = cursor.fetchall()
            print(f"[READ] Data from Slave-2:")
            for row in rows:
                print(f"  - {row}")
        conn_slave.close()

def laravel_service_action():
    print("\n--- Laravel Service (Master -> Slave 3) ---")
    conn_master = get_connection('master')
    if conn_master:
        with conn_master.cursor() as cursor:
            name = f"Laravel-User-{int(time.time())}"
            cursor.execute("INSERT INTO users (name) VALUES (%s)", (name,))
            conn_master.commit()
            print(f"[WRITE] Inserted '{name}' to Master.")
        conn_master.close()
    
    time.sleep(1)
    
    conn_slave = get_connection('slave3')
    if conn_slave:
        with conn_slave.cursor() as cursor:
            cursor.execute("SELECT * FROM users ORDER BY id DESC LIMIT 3")
            rows = cursor.fetchall()
            print(f"[READ] Data from Slave-3:")
            for row in rows:
                print(f"  - {row}")
        conn_slave.close()

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        print("Running Auto Verification...")
        go_service_action()
        time.sleep(1)
        express_service_action()
        time.sleep(1)
        laravel_service_action()
        print("\nAll Services Demonstrated Successfully.")
        return

    print("Starting Multi-Service Replication Demo...")
    while True:
        print("\nSelect Service to Simulate:")
        print("1. Go Service (Write Master -> Read Slave 1)")
        print("2. Express Service (Write Master -> Read Slave 2)")
        print("3. Laravel Service (Write Master -> Read Slave 3)")
        print("4. Exit")
        choice = input("Enter choice (1-4): ")
        
        if choice == '1':
            go_service_action()
        elif choice == '2':
            express_service_action()
        elif choice == '3':
            laravel_service_action()
        elif choice == '4':
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
