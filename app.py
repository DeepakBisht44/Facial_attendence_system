from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import os
import json
import csv
from datetime import datetime

app = Flask(__name__, static_folder='.', template_folder='.')
CORS(app)

# Configuration
PYTHON_CMD = 'py -3.10'
PYTHON_FOLDER = './python/'
DATASET = './dataset'
ENCODINGS = os.path.join(PYTHON_FOLDER, 'encodings.pkl')
STUDENTS_CSV = './students.csv'
ATTENDANCE_CSV = './attendance.csv'
RESULT_JSON = './result.json'

# Ensure necessary files exist
for file_path in [STUDENTS_CSV, ATTENDANCE_CSV]:
    if not os.path.exists(file_path):
        open(file_path, 'w').close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/add-student', methods=['POST'])
def add_student():
    """Add a new student"""
    try:
        data = request.json
        student_id = data.get('id', '').strip()
        name = data.get('name', '').strip()
        samples = data.get('samples', 20)
        
        print(f"\n{'='*60}")
        print(f"ADD STUDENT REQUEST")
        print(f"{'='*60}")
        print(f"Student ID: {student_id}")
        print(f"Name: {name}")
        print(f"Samples: {samples}")
        
        if not student_id or not name:
            print("ERROR: ID and name required")
            return jsonify({'success': False, 'error': 'ID and name required'}), 400
        
        # Check if register.py exists
        register_path = os.path.join(PYTHON_FOLDER, 'register.py')
        if not os.path.exists(register_path):
            print(f"ERROR: register.py not found at {register_path}")
            return jsonify({
                'success': False,
                'error': f'register.py not found at {register_path}'
            }), 500
        
        print(f"✓ register.py found at: {register_path}")
        
        # Build command
        register_cmd = f'{PYTHON_CMD} "{register_path}" {student_id} "{name}" {samples}'
        print(f"Command: {register_cmd}")
        print(f"{'='*60}\n")
        
        # Run register.py
        print("Executing register.py...")
        register_result = subprocess.run(
            register_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        print(f"\n{'='*60}")
        print(f"REGISTER.PY OUTPUT:")
        print(f"{'='*60}")
        print(f"Return code: {register_result.returncode}")
        print(f"\nSTDOUT:\n{register_result.stdout}")
        if register_result.stderr:
            print(f"\nSTDERR:\n{register_result.stderr}")
        print(f"{'='*60}\n")
        
        if register_result.returncode != 0:
            return jsonify({
                'success': False,
                'error': 'Failed to capture images',
                'details': register_result.stderr or register_result.stdout
            }), 500
        
        # Auto encode database
        print("Starting database encoding...")
        encode_path = os.path.join(PYTHON_FOLDER, 'encode_db.py')
        encode_cmd = f'{PYTHON_CMD} "{encode_path}" "{DATASET}" "{ENCODINGS}"'
        print(f"Encode command: {encode_cmd}")
        
        encode_result = subprocess.run(
            encode_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        print(f"\nENCODE_DB.PY OUTPUT:")
        print(f"Return code: {encode_result.returncode}")
        print(f"STDOUT: {encode_result.stdout}")
        if encode_result.stderr:
            print(f"STDERR: {encode_result.stderr}")
        
        print(f"\n{'='*60}")
        print(f"✓ STUDENT ADDED SUCCESSFULLY")
        print(f"{'='*60}\n")
        
        return jsonify({
            'success': True,
            'message': f'Student {name} added successfully',
            'id': student_id,
            'name': name
        })
        
    except subprocess.TimeoutExpired:
        print("ERROR: Operation timeout")
        return jsonify({'success': False, 'error': 'Operation timeout'}), 408
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/recognize', methods=['POST'])
def recognize():
    """Perform face recognition and mark attendance"""
    try:
        print(f"\n{'='*60}")
        print(f"RECOGNITION REQUEST")
        print(f"{'='*60}\n")
        
        # Auto encode database first
        encode_path = os.path.join(PYTHON_FOLDER, 'encode_db.py')
        encode_cmd = f'{PYTHON_CMD} "{encode_path}" "{DATASET}" "{ENCODINGS}"'
        subprocess.run(encode_cmd, shell=True, timeout=60)
        
        # Run recognition
        recognize_path = os.path.join(PYTHON_FOLDER, 'recognize.py')
        recognize_cmd = f'{PYTHON_CMD} "{recognize_path}" "{ENCODINGS}" 0.35'
        print(f"Command: {recognize_cmd}")
        
        recognize_result = subprocess.run(
            recognize_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print(f"\nRECOGNIZE.PY OUTPUT:")
        print(f"Return code: {recognize_result.returncode}")
        print(f"STDOUT:\n{recognize_result.stdout}")
        if recognize_result.stderr:
            print(f"STDERR:\n{recognize_result.stderr}")
        
        if recognize_result.returncode != 0:
            return jsonify({
                'success': False,
                'error': 'Recognition failed',
                'details': recognize_result.stderr or recognize_result.stdout
            }), 500
        
        # Read result.json
        if os.path.exists(RESULT_JSON):
            with open(RESULT_JSON, 'r') as f:
                result_data = json.load(f)
            
            # Get student name from students.csv
            student_name = 'Unknown'
            if os.path.exists(STUDENTS_CSV):
                with open(STUDENTS_CSV, 'r') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if row and row[0] == result_data.get('id', ''):
                            student_name = row[1] if len(row) > 1 else 'Unknown'
                            break
            
            print(f"✓ Recognition successful: {student_name}\n")
            
            return jsonify({
                'success': True,
                'id': result_data.get('id', ''),
                'name': student_name,
                'time': result_data.get('time', ''),
                'distance': result_data.get('distance', '')
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No face detected or recognized'
            }), 404
            
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Operation timeout'}), 408
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/students', methods=['GET'])
def get_students():
    """Get list of all students"""
    try:
        students = []
        if os.path.exists(STUDENTS_CSV):
            with open(STUDENTS_CSV, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row and len(row) >= 2:
                        students.append({
                            'id': row[0],
                            'name': row[1]
                        })
        return jsonify(students)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/attendance', methods=['GET'])
def get_attendance():
    """Get attendance records"""
    try:
        records = []
        if os.path.exists(ATTENDANCE_CSV):
            with open(ATTENDANCE_CSV, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row and len(row) >= 4:
                        records.append({
                            'id': row[0],
                            'name': row[1],
                            'time': row[2],
                            'distance': row[3]
                        })
        return jsonify(records)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export', methods=['GET'])
def export_data():
    """Export attendance data"""
    try:
        if os.path.exists(ATTENDANCE_CSV):
            return send_file(
                ATTENDANCE_CSV,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'attendance_{datetime.now().strftime("%Y%m%d")}.csv'
            )
        else:
            return jsonify({'error': 'No attendance data found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/save-image', methods=['POST'])
def save_image():
    """Save captured image from frontend"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image provided'}), 400
        
        image = request.files['image']
        student_id = request.form.get('student_id')
        index = request.form.get('index')
        
        # Create student folder
        student_folder = os.path.join(DATASET, student_id)
        os.makedirs(student_folder, exist_ok=True)
        
        # Save image
        image_path = os.path.join(student_folder, f"{student_id}_{index}.jpg")
        image.save(image_path)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/finalize-registration', methods=['POST'])
def finalize_registration():
    """Finalize student registration after images are captured"""
    try:
        data = request.json
        student_id = data.get('id')
        name = data.get('name')
        
        # Add to students.csv
        student_exists = False
        students = []
        
        if os.path.exists(STUDENTS_CSV):
            with open(STUDENTS_CSV, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row and row[0] == student_id:
                        student_exists = True
                        students.append([student_id, name])
                    else:
                        students.append(row)
        
        if not student_exists:
            students.append([student_id, name])
        
        with open(STUDENTS_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(students)
        
        # Encode database
        encode_path = os.path.join(PYTHON_FOLDER, 'encode_db.py')
        encode_cmd = f'{PYTHON_CMD} "{encode_path}" "{DATASET}" "{ENCODINGS}"'
        encode_result = subprocess.run(
            encode_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        print(f"Encoding completed with return code: {encode_result.returncode}")
        
        return jsonify({
            'success': True,
            'message': f'Student {name} registered successfully'
        })
        
    except Exception as e:
        print(f"Error in finalize_registration: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system statistics"""
    try:
        # Count students
        student_count = 0
        if os.path.exists(STUDENTS_CSV):
            with open(STUDENTS_CSV, 'r') as f:
                student_count = sum(1 for line in f if line.strip())
        
        # Count attendance records
        attendance_count = 0
        if os.path.exists(ATTENDANCE_CSV):
            with open(ATTENDANCE_CSV, 'r') as f:
                attendance_count = sum(1 for line in f if line.strip())
        
        # Check if database is encoded
        database_ready = os.path.exists(ENCODINGS)
        
        return jsonify({
            'students': student_count,
            'attendance_records': attendance_count,
            'database_ready': database_ready,
            'dataset_path': DATASET
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(DATASET, exist_ok=True)
    os.makedirs(PYTHON_FOLDER, exist_ok=True)
    
    print("=" * 50)
    print("🚀 FRAS Web Server Starting...")
    print("=" * 50)
    print(f"📁 Dataset: {DATASET}")
    print(f"📄 Students CSV: {STUDENTS_CSV}")
    print(f"📊 Attendance CSV: {ATTENDANCE_CSV}")
    print(f"🐍 Python folder: {PYTHON_FOLDER}")
    print("=" * 50)
    print("🌐 Open your browser and go to: http://localhost:5000")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)