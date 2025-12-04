# app.py
import http.server
import socketserver
import os
import signal
import sys
from datetime import datetime
import psycopg2
from psycopg2 import pool
import json
import time

PORT = 8181

# Конфигурация БД из переменных окружения
DB_CONFIG = {
    'host': os.environ.get('DATABASE_HOST', 'localhost'),
    'port': os.environ.get('DATABASE_PORT', 5432),
    'database': os.environ.get('DATABASE_NAME', 'devopsdb'),
    'user': os.environ.get('DATABASE_USER', 'devopsuser'),
    'password': os.environ.get('DATABASE_PASSWORD', 'devopspass')
}

# Пул соединений
connection_pool = None

def init_database():
    """Инициализация БД и создание таблиц если их нет"""
    global connection_pool
    
    # Ждем пока БД станет доступной
    max_retries = 10
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Создаем таблицу посещений
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS visits (
                    id SERIAL PRIMARY KEY,
                    visit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    client_ip VARCHAR(50),
                    user_agent TEXT,
                    path VARCHAR(255)
                )
            ''')
            
            # Создаем таблицу студентов (пример данных)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    group_name VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Добавляем тестовые данные если таблица пуста
            cursor.execute("SELECT COUNT(*) FROM students")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO students (name, group_name) VALUES 
                    ('Роман Дик', 'DevOps-1'),
                    ('Алексей Петров', 'DevOps-2'),
                    ('Мария Сидорова', 'DevOps-1')
                """)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Создаем пул соединений
            connection_pool = psycopg2.pool.SimpleConnectionPool(
                1, 10, **DB_CONFIG
            )
            
            print(f"Database initialized successfully on {DB_CONFIG['host']}:{DB_CONFIG['port']}")
            return True
            
        except psycopg2.OperationalError as e:
            if i < max_retries - 1:
                print(f"Database not ready, retrying... ({i+1}/{max_retries})")
                time.sleep(3)
            else:
                print(f"Failed to connect to database: {e}")
                return False

def log_visit(client_ip, user_agent, path):
    """Логируем посещение в БД"""
    if connection_pool:
        try:
            conn = connection_pool.getconn()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO visits (client_ip, user_agent, path) VALUES (%s, %s, %s)",
                (client_ip, user_agent, path)
            )
            conn.commit()
            cursor.close()
            connection_pool.putconn(conn)
        except Exception as e:
            print(f"Error logging visit: {e}")

def get_visit_count():
    """Получаем общее количество посещений"""
    if connection_pool:
        try:
            conn = connection_pool.getconn()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM visits")
            count = cursor.fetchone()[0]
            cursor.close()
            connection_pool.putconn(conn)
            return count
        except Exception as e:
            print(f"Error getting visit count: {e}")
    return 0

def get_students():
    """Получаем список студентов"""
    if connection_pool:
        try:
            conn = connection_pool.getconn()
            cursor = conn.cursor()
            cursor.execute("SELECT name, group_name FROM students ORDER BY id")
            students = cursor.fetchall()
            cursor.close()
            connection_pool.putconn(conn)
            return students
        except Exception as e:
            print(f"Error getting students: {e}")
    return []

class DevOpsHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Логируем посещение
        client_ip = self.client_address[0]
        user_agent = self.headers.get('User-Agent', 'Unknown')
        log_visit(client_ip, user_agent, self.path)
        
        # Получаем данные из БД
        visit_count = get_visit_count()
        students = get_students()
        
        # Формируем HTML
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        deploy_time = os.environ.get('DEPLOY_TIME', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        student_name = "dik"
        
        # Форматируем список студентов
        students_html = ''
        for name, group in students:
            students_html += f'<li>{name} ({group})</li>'
        
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>DevOps Lab #4 - Docker Compose + PostgreSQL</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
                .container {{ max-width: 1000px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; backdrop-filter: blur(10px); }}
                .success {{ color: #4CAF50; font-weight: bold; font-size: 1.2em; }}
                .info {{ background: rgba(255,255,255,0.2); padding: 20px; border-radius: 10px; margin: 15px 0; }}
                .db-info {{ background: rgba(0,255,0,0.1); border-left: 5px solid #4CAF50; }}
                .stats {{ display: flex; justify-content: space-between; margin: 20px 0; }}
                .stat-box {{ background: rgba(255,255,255,0.15); padding: 15px; border-radius: 8px; text-align: center; flex: 1; margin: 0 10px; }}
                h2 {{ color: #FFD700; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>DevOps Laboratory Work #4 123456789</h1>
                <h2>Docker Compose + PostgreSQL + Volumes</h2>
                
                <div class="info">
                    <p><strong>Student:</strong> {student_name}</p>
                    <p><strong>Deployment Time:</strong> {deploy_time}</p>
                    <p><strong>Application ID:</strong> {os.environ.get('HOSTNAME', 'N/A')}</p>
                </div>
                
                <div class="info db-info">
                    <h3>Database Statistics</h3>
                    <div class="stats">
                        <div class="stat-box">
                            <h4>Total Visits</h4>
                            <p style="font-size: 2em; margin: 10px 0;">{visit_count}</p>
                        </div>
                        <div class="stat-box">
                            <h4>Students in DB</h4>
                            <p style="font-size: 2em; margin: 10px 0;">{len(students)}</p>
                        </div>
                        <div class="stat-box">
                            <h4>Database</h4>
                            <p>PostgreSQL 15</p>
                            <p>Host: {DB_CONFIG['host']}</p>
                        </div>
                    </div>
                </div>
                
                <div class="info">
                    <h3>Students List (from PostgreSQL)</h3>
                    <ul>
                        {students_html if students_html else '<li>No students found or DB not connected</li>'}
                    </ul>
                </div>
                
                <div class="info">
                    <h3>Docker Compose Stack</h3>
                    <p><strong>Containers:</strong> Python App + PostgreSQL + pgAdmin</p>
                    <p><strong>Volumes:</strong> postgres_data (persistent storage)</p>
                    <p><strong>Network:</strong> Internal bridge network</p>
                    <p><strong>Ports:</strong> 8181 (App), 5432 (DB internal), 8080 (pgAdmin)</p>
                </div>
                
                <div class="info">
                    <h3>Deployment Info</h3>
                    <p>This application is deployed using:</p>
                    <ul>
                        <li>Docker Compose for multi-container orchestration</li>
                        <li>PostgreSQL with Docker Volume for data persistence</li>
                        <li>GitHub Actions CI/CD Pipeline</li>
                        <li>Automatic deployment on release</li>
                    </ul>
                </div>
                
                <p class="success">Application is running with PostgreSQL persistence!</p>
                <p>Refresh the page to increase visit counter (data saved in DB).</p>
            </div>
        </body>
        </html>
        '''
        
        self.wfile.write(html_content.encode('utf-8'))

def signal_handler(signum, frame):
    print(f"\nReceived signal {signum}, shutting down gracefully...")
    if connection_pool:
        connection_pool.closeall()
    sys.exit(0)

def main():
    # Инициализируем БД
    if not init_database():
        print("Starting without database connection...")
    
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    with socketserver.TCPServer(("", PORT), DevOpsHandler) as httpd:
        print(f"Server started at http://0.0.0.0:{PORT}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
        print("Running in Docker Compose stack")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped by user")
        finally:
            if connection_pool:
                connection_pool.closeall()

if __name__ == '__main__':
    main()