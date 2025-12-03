import http.server
import socketserver
import os
import signal
import sys
from datetime import datetime

PORT = 8181

class SimpleHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        # Получаем информацию о деплое
        deploy_time = os.environ.get('DEPLOY_TIME', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        student_name = "dik"
        
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>DevOps Lab #2</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
                .container {{ max-width: 800px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; backdrop-filter: blur(10px); }}
                .success {{ color: #4CAF50; font-weight: bold; font-size: 1.2em; }}
                .info {{ background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px; margin: 10px 0; }}
                .deploy-info {{ color: #FFD700; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>DevOps Laboratory Work #2 22801089089</h1>
                
                <div class="info">
                    <p><strongStudent:</strong> {student_name}</p>
                    <p><strong>Deployment Time:</strong> <span class="deploy-info">{deploy_time}</span></p>
                </div>
                
                <p class="success">Successfully deployed via GitHub Actions + Systemd Service!</p>
                
                <div class="info">
                    <p><strong>Deployment Method:</strong> GitHub Actions CD Pipeline</p>
                    <p><strong>Runtime:</strong> Python + Systemd Service</p>
                    <p><strong>App URL:</strong> http://app.{student_name}.course.prafdin.ru</p>
                    <p><strong>Port:</strong> {PORT}</p>
                </div>
                
                <p>This page updates automatically when you create a new release in GitHub.</p>
                
                <div style="margin-top: 30px; padding: 15px; background: rgba(0,0,0,0.3); border-radius: 8px;">
                    <h3>System Information:</h3>
                    <p><strong>Server Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Python Version:</strong> 3.x</p>
                    <p><strong>Service:</strong> systemd managed</p>
                </div>
            </div>
        </body>
        </html>
        '''
        
        self.wfile.write(html_content.encode())
    
    def log_message(self, format, *args):
        # Кастомное логирование
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {format % args}")

def signal_handler(signum, frame):
    print(f"\nReceived signal {signum}, shutting down gracefully...")
    sys.exit(0)

def main():
    # Регистрируем обработчики сигналов для graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # systemd stop
    
    with socketserver.TCPServer(("", PORT), SimpleHandler) as httpd:
        print(f"Server started at http://0.0.0.0:{PORT}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Service is running via systemd")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped by user")
        except Exception as e:
            print(f"\nServer error: {e}")
        finally:
            print("Server shutdown complete")

if __name__ == '__main__':
    main()