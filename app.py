import os
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

KIE_API_KEY = os.getenv('KIE_API_KEY')
KIE_API_BASE_URL = os.getenv('KIE_API_BASE_URL', 'https://api.kie.ai')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/create-task', methods=['POST'])
def create_task():
    """Gọi API Create Task của KIE.AI"""
    try:
        data = request.json
        prompt = data.get('prompt')
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        if not KIE_API_KEY:
            return jsonify({'error': 'KIE_API_KEY not configured'}), 500
        
        # Gọi KIE.AI Create Task API
        headers = {
            'Authorization': f'Bearer {KIE_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'prompt': prompt,
            'model': 'seedance-2.0'
        }
        
        response = requests.post(
            f'{KIE_API_BASE_URL}/tasks/create',
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code not in [200, 201]:
            return jsonify({'error': f'Failed to create task: {response.text}'}), response.status_code
        
        task_data = response.json()
        task_id = task_data.get('task_id') or task_data.get('id')
        
        if not task_id:
            return jsonify({'error': 'No task_id in response'}), 500
        
        return jsonify({'task_id': task_id, 'status': 'created'}), 200
    
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request timeout'}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Connection error to KIE.AI'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-task/<task_id>', methods=['GET'])
def get_task(task_id):
    """Polling Get Task từ KIE.AI"""
    try:
        if not KIE_API_KEY:
            return jsonify({'error': 'KIE_API_KEY not configured'}), 500
        
        headers = {
            'Authorization': f'Bearer {KIE_API_KEY}'
        }
        
        response = requests.get(
            f'{KIE_API_BASE_URL}/tasks/{task_id}',
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            return jsonify({'error': f'Failed to get task: {response.text}'}), response.status_code
        
        task_data = response.json()
        status = task_data.get('status')
        video_url = task_data.get('video_url')
        
        return jsonify({
            'task_id': task_id,
            'status': status,
            'video_url': video_url
        }), 200
    
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request timeout'}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Connection error to KIE.AI'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
