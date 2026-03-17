from flask import Flask, render_template_string, jsonify, request
import os
import socket
import platform
import datetime
import json
import re

app = Flask(__name__)

def get_real_platform_info():
    """Get actual OS info from container - SAFE VERSION"""
    try:
        # Method 1: Read /etc/os-release (most reliable for Linux containers)
        if os.path.exists('/etc/os-release'):
            os_info = {}
            with open('/etc/os-release', 'r', encoding='utf-8') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        os_info[key] = value.strip('"')
            
            name = os_info.get('PRETTY_NAME', os_info.get('NAME', 'Linux'))
            version = os_info.get('VERSION_ID', '')
            return f"{name} {version}".strip()
    except Exception as e:
        print(f"Note: Could not read /etc/os-release: {e}")
    
    # Method 2: Simple Python detection
    try:
        return f"{platform.system()} {platform.release()}"
    except:
        return "Linux Container"

def get_container_id():
    """Get container ID - SAFE VERSION without subprocess"""
    # Try multiple sources
    container_id = os.environ.get('HOSTNAME', '')
    
    # Check cgroup for Docker/container ID
    try:
        if os.path.exists('/proc/self/cgroup'):
            with open('/proc/self/cgroup', 'r', encoding='utf-8') as f:
                content = f.read()
                for line in content.split('\n'):
                    if any(x in line for x in ['docker', 'containerd', 'ecs', 'kubepods']):
                        parts = line.strip().split('/')
                        if len(parts) > 2:
                            id_part = parts[-1]
                            # Look for container ID pattern
                            match = re.search(r'([a-f0-9]{12,64})', id_part)
                            if match:
                                return match.group(0)[:12]  # First 12 chars
                            else:
                                # Return last part
                                return id_part[:12]
    except Exception as e:
        print(f"Note: Could not read cgroup: {e}")
    
    return container_id if container_id and container_id != 'localhost' else socket.gethostname()

def detect_environment():
    """Detect where the app is running"""
    # Check for AWS ECS - use environment variable
    if os.environ.get('ENVIRONMENT') == 'AWS ECS Fargate':
        return "AWS ECS Fargate", "#FF9900", "🚀"
    
    # Check for AWS ECS metadata
    if os.environ.get('ECS_CONTAINER_METADATA_URI'):
        return "AWS ECS Fargate", "#FF9900", "🚀"
    
    # Check for Docker
    if os.path.exists('/.dockerenv'):
        return "Docker Container", "#007bff", "🐳"
    
    # Check cgroup
    try:
        if os.path.exists('/proc/self/cgroup'):
            with open('/proc/self/cgroup', 'r', encoding='utf-8') as f:
                if 'docker' in f.read() or 'containerd' in f.read():
                    return "Docker Container", "#007bff", "🐳"
    except:
        pass
    
    # Default to local
    return "Local Development", "#6c757d", "💻"

def get_system_stats():
    """Get system stats - SAFE VERSION without subprocess"""
    try:
        # Get CPU count
        cpu_count = os.cpu_count() or 1
        
        # Try to get memory info from /proc/meminfo (Linux)
        memory_info = "N/A"
        try:
            if os.path.exists('/proc/meminfo'):
                with open('/proc/meminfo', 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('MemTotal:'):
                            mem_kb = int(line.split()[1])
                            memory_info = f"{mem_kb // 1024} MB"
                            break
        except Exception as e:
            print(f"Note: Could not read meminfo: {e}")
            # For ECS Fargate, use typical values
            if os.environ.get('ENVIRONMENT') == 'AWS ECS Fargate':
                memory_info = "512 MB (Fargate task)"
            else:
                memory_info = "Unknown"
        
        return {
            'cpu_count': cpu_count,
            'memory': memory_info,
            'disk_usage': 'Container filesystem'
        }
    except Exception as e:
        print(f"Error getting system stats: {e}")
        # Return safe defaults for ECS
        return {
            'cpu_count': '1',
            'memory': '512 MB',
            'disk_usage': 'Container storage'
        }

def get_deployment_status():
    """Get assignment progress status - SAFE VERSION"""
    env_name, _, _ = detect_environment()
    
    # For ECS, we know these are true if environment is detected
    is_ecs = env_name == "AWS ECS Fargate"
    
    return {
        'docker_built': True,  # If we're running, Docker was built
        'ecr_pushed': is_ecs,  # Assuming ECR push if on AWS
        'ecs_running': is_ecs,
        'app_accessible': True  # If we're here, app is accessible
    }

@app.route('/')
def home():
    try:
        # Get all info
        env_name, env_color, env_icon = detect_environment()
        platform_info = get_real_platform_info()
        container_id = get_container_id()
        system_stats = get_system_stats()
        deployment = get_deployment_status()
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate progress
        completed = sum(deployment.values())
        total = len(deployment)
        progress_percent = int((completed / total) * 100) if total > 0 else 0
        
        # HTML template
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Container System Info - AWS Assignment</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                    color: #333;
                }}
                
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 20px;
                    padding: 40px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                }}
                
                .header {{
                    text-align: center;
                    margin-bottom: 40px;
                    border-bottom: 3px solid #667eea;
                    padding-bottom: 20px;
                }}
                
                h1 {{
                    color: #2d3748;
                    font-size: 2.8rem;
                    margin-bottom: 10px;
                }}
                
                .tagline {{
                    color: #718096;
                    font-size: 1.2rem;
                    margin-bottom: 20px;
                }}
                
                .environment-badge {{
                    display: inline-block;
                    background: {env_color};
                    color: white;
                    padding: 12px 30px;
                    border-radius: 50px;
                    font-size: 1.4rem;
                    font-weight: 600;
                    margin: 20px 0;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.2);
                }}
                
                .dashboard {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 25px;
                    margin-bottom: 40px;
                }}
                
                .card {{
                    background: #f8f9fa;
                    border-radius: 15px;
                    padding: 25px;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                    transition: transform 0.3s ease;
                }}
                
                .card:hover {{
                    transform: translateY(-5px);
                }}
                
                .card h2 {{
                    color: #2d3748;
                    font-size: 1.5rem;
                    margin-bottom: 20px;
                    padding-bottom: 10px;
                    border-bottom: 2px solid #cbd5e0;
                }}
                
                .info-grid {{
                    display: grid;
                    gap: 15px;
                }}
                
                .info-item {{
                    display: flex;
                    justify-content: space-between;
                    padding: 10px 0;
                    border-bottom: 1px solid #e2e8f0;
                }}
                
                .info-item:last-child {{
                    border-bottom: none;
                }}
                
                .label {{
                    color: #4a5568;
                    font-weight: 500;
                }}
                
                .value {{
                    color: #2d3748;
                    font-weight: 600;
                    font-family: 'Courier New', monospace;
                    text-align: right;
                    max-width: 60%;
                    word-break: break-all;
                }}
                
                .progress-section {{
                    grid-column: 1 / -1;
                }}
                
                .progress-bar {{
                    background: #e2e8f0;
                    border-radius: 10px;
                    height: 20px;
                    margin: 20px 0;
                    overflow: hidden;
                }}
                
                .progress-fill {{
                    height: 100%;
                    background: linear-gradient(90deg, #48bb78, #38a169);
                    border-radius: 10px;
                    width: {progress_percent}%;
                    transition: width 0.5s ease;
                }}
                
                .step-list {{
                    display: grid;
                    gap: 15px;
                    margin-top: 20px;
                }}
                
                .step {{
                    display: flex;
                    align-items: center;
                    padding: 15px;
                    background: #f7fafc;
                    border-radius: 10px;
                    border-left: 4px solid #cbd5e0;
                }}
                
                .step.completed {{
                    border-left-color: #48bb78;
                    background: #f0fff4;
                }}
                
                .step-icon {{
                    font-size: 1.5rem;
                    margin-right: 15px;
                }}
                
                .step-content {{
                    flex: 1;
                }}
                
                .step-title {{
                    font-weight: 600;
                    color: #2d3748;
                }}
                
                .step-status {{
                    color: #718096;
                    font-size: 0.9rem;
                }}
                
                .timestamp {{
                    text-align: center;
                    margin-top: 30px;
                    padding: 15px;
                    background: #edf2f7;
                    border-radius: 10px;
                    color: #4a5568;
                }}
                
                .api-links {{
                    display: flex;
                    justify-content: center;
                    gap: 15px;
                    margin-top: 30px;
                    flex-wrap: wrap;
                }}
                
                .api-link {{
                    padding: 10px 20px;
                    background: #667eea;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    transition: background 0.3s;
                }}
                
                .api-link:hover {{
                    background: #5a67d8;
                }}
                
                .refresh-note {{
                    text-align: center;
                    margin-top: 20px;
                    color: #667eea;
                    font-weight: 500;
                    font-size: 0.9rem;
                }}
                
                @media (max-width: 768px) {{
                    .dashboard {{
                        grid-template-columns: 1fr;
                    }}
                    
                    .container {{
                        padding: 20px;
                    }}
                    
                    h1 {{
                        font-size: 2rem;
                    }}
                }}
            </style>
            <script>
                // Update time every second
                function updateTime() {{
                    const now = new Date();
                    const timeStr = now.toLocaleString();
                    document.querySelectorAll('.time-display').forEach(el => {{
                        el.textContent = timeStr;
                    }});
                }}
                
                // Auto-refresh every 30 seconds
                setTimeout(() => {{
                    window.location.reload();
                }}, 30000);
                
                // Initialize
                updateTime();
                setInterval(updateTime, 1000);
            </script>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📦 AWS Container Deployment</h1>
                    <p class="tagline">Docker → ECR → ECS Fargate Assignment Demo</p>
                    <div class="environment-badge">
                        {env_icon} {env_name}
                    </div>
                    <p class="time-display">{current_time}</p>
                </div>
                
                <div class="dashboard">
                    <div class="card">
                        <h2>📊 System Information</h2>
                        <div class="info-grid">
                            <div class="info-item">
                                <span class="label">Environment:</span>
                                <span class="value">{env_name}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">Container ID:</span>
                                <span class="value">{container_id}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">Hostname:</span>
                                <span class="value">{socket.gethostname()}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">Platform:</span>
                                <span class="value">{platform_info}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">Architecture:</span>
                                <span class="value">{platform.machine()}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">Python Version:</span>
                                <span class="value">{platform.python_version()}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">CPU Cores:</span>
                                <span class="value">{system_stats['cpu_count']}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">Memory:</span>
                                <span class="value">{system_stats['memory']}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">Client IP:</span>
                                <span class="value">{request.remote_addr}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">In Container:</span>
                                <span class="value">{"✅ Yes" if env_name in ["Docker Container", "AWS ECS Fargate"] else "❌ No"}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card progress-section">
                        <h2>✅ Assignment Progress</h2>
                        <p>Completed {completed} of {total} steps ({progress_percent}%)</p>
                        
                        <div class="progress-bar">
                            <div class="progress-fill"></div>
                        </div>
                        
                        <div class="step-list">
                            <div class="step {'completed' if deployment['docker_built'] else ''}">
                                <div class="step-icon">
                                    {'✅' if deployment['docker_built'] else '⏳'}
                                </div>
                                <div class="step-content">
                                    <div class="step-title">1. Build Docker Container</div>
                                    <div class="step-status">Create and test container locally</div>
                                </div>
                            </div>
                            
                            <div class="step {'completed' if deployment['ecr_pushed'] else ''}">
                                <div class="step-icon">
                                    {'✅' if deployment['ecr_pushed'] else '⏳'}
                                </div>
                                <div class="step-content">
                                    <div class="step-title">2. Push to Amazon ECR</div>
                                    <div class="step-status">Upload container image to AWS</div>
                                </div>
                            </div>
                            
                            <div class="step {'completed' if deployment['ecs_running'] else ''}">
                                <div class="step-icon">
                                    {'✅' if deployment['ecs_running'] else '⏳'}
                                </div>
                                <div class="step-content">
                                    <div class="step-title">3. Run on ECS Fargate</div>
                                    <div class="step-status">Deploy container serverlessly</div>
                                </div>
                            </div>
                            
                            <div class="step {'completed' if deployment['app_accessible'] else ''}">
                                <div class="step-icon">
                                    {'✅' if deployment['app_accessible'] else '⏳'}
                                </div>
                                <div class="step-content">
                                    <div class="step-title">4. Access Application</div>
                                    <div class="step-status">Publicly accessible via URL</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="timestamp">
                    <p>🔄 Page auto-refreshes every 30 seconds</p>
                    <p>Current server time: <span class="time-display">{current_time}</span></p>
                </div>
                
                <div class="api-links">
                    <a href="/health" class="api-link" target="_blank">Health Check</a>
                    <a href="/api/metadata" class="api-link" target="_blank">Metadata API</a>
                    <a href="/api/status" class="api-link" target="_blank">Status API</a>
                </div>
                
                <div class="refresh-note">
                    ⚡ Real-time updates • Container ID: {container_id}
                </div>
            </div>
        </body>
        </html>
        '''
        return html
    except Exception as e:
        # If anything fails, return a simple error page
        return f'''
        <html>
        <body style="font-family: Arial; padding: 20px;">
            <h1>🚀 Docker System Info App</h1>
            <h2>Running on AWS ECS Fargate</h2>
            <p>App is running successfully in container!</p>
            <p>Some features may be limited in container environment.</p>
            <p>Error details (for debugging): {str(e)}</p>
            <hr>
            <p><a href="/health">Health Check</a> | <a href="/api/metadata">Metadata</a></p>
        </body>
        </html>
        '''

@app.route('/health')
def health_check():
    """Health check endpoint for Docker/ECS"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'service': 'container-info-app',
        'environment': detect_environment()[0]
    })

@app.route('/api/metadata')
def api_metadata():
    """JSON API endpoint for metadata"""
    try:
        env_name, env_color, env_icon = detect_environment()
        
        return jsonify({
            'environment': env_name,
            'container_id': get_container_id(),
            'hostname': socket.gethostname(),
            'platform': get_real_platform_info(),
            'architecture': platform.machine(),
            'python_version': platform.python_version(),
            'timestamp': datetime.datetime.now().isoformat(),
            'client_ip': request.remote_addr,
            'in_container': env_name in ["Docker Container", "AWS ECS Fargate"]
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.datetime.now().isoformat()
        })

@app.route('/api/status')
def api_status():
    """JSON API endpoint for deployment status"""
    try:
        deployment = get_deployment_status()
        completed = sum(deployment.values())
        total = len(deployment)
        
        return jsonify({
            'steps': deployment,
            'completed': completed,
            'total': total,
            'progress_percent': int((completed / total) * 100) if total > 0 else 0,
            'timestamp': datetime.datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.datetime.now().isoformat()
        })

# Note: In production, Gunicorn runs the app
# This is only for running with: python main.py
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)