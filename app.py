from flask import Flask, request, jsonify, send_file, render_template
from werkzeug.utils import secure_filename
import os
import uuid
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Create directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mp3', 'wav', 'ogg', 'm4a'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Mock subtitle generation function (replace with your actual implementation)
def generate_subtitles(file_path, target_language):
    """
    Mock function to generate subtitles
    In a real implementation, this would use:
    - Speech recognition for transcription
    - Translation services for different languages
    - Subtitle file generation
    """
    try:
        # Generate a unique ID for this processing job
        job_id = str(uuid.uuid4())
        
        # Mock processing delay
        import time
        time.sleep(2)  # Simulate processing time
        
        # Mock subtitle data for different languages
        subtitle_data = {
            'en': [
                {'start': 1.0, 'end': 4.0, 'text': 'Welcome to our subtitle generator'},
                {'start': 5.0, 'end': 8.0, 'text': 'This video demonstrates subtitle functionality'},
                {'start': 9.0, 'end': 12.0, 'text': 'You can upload your own videos'},
                {'start': 13.0, 'end': 16.0, 'text': 'And generate subtitles in multiple languages'},
                {'start': 17.0, 'end': 20.0, 'text': 'Thank you for using our service'}
            ],
            'ur': [
                {'start': 1.0, 'end': 4.0, 'text': 'ہمارے سب ٹائٹل جنریٹر میں خوش آمدید'},
                {'start': 5.0, 'end': 8.0, 'text': 'یہ ویڈیو سب ٹائٹل کی فعالیت کا مظاہرہ کرتی ہے'},
                {'start': 9.0, 'end': 12.0, 'text': 'آپ اپنی اپنی ویڈیوز اپ لوڈ کر سکتے ہیں'},
                {'start': 13.0, 'end': 16.0, 'text': 'اور متعدد زبانوں میں سب ٹائٹل تیار کر سکتے ہیں'},
                {'start': 17.0, 'end': 20.0, 'text': 'ہماری سروس استعمال کرنے کا شکریہ'}
            ],
            'es': [
                {'start': 1.0, 'end': 4.0, 'text': 'Bienvenido a nuestro generador de subtítulos'},
                {'start': 5.0, 'end': 8.0, 'text': 'Este video demuestra la funcionalidad de subtítulos'},
                {'start': 9.0, 'end': 12.0, 'text': 'Puedes subir tus propios videos'},
                {'start': 13.0, 'end': 16.0, 'text': 'Y generar subtítulos en múltiples idiomas'},
                {'start': 17.0, 'end': 20.0, 'text': 'Gracias por usar nuestro servicio'}
            ],
            'fr': [
                {'start': 1.0, 'end': 4.0, 'text': 'Bienvenue dans notre générateur de sous-titres'},
                {'start': 5.0, 'end': 8.0, 'text': 'Cette vidéo démontre la fonctionnalité des sous-titres'},
                {'start': 9.0, 'end': 12.0, 'text': 'Vous pouvez télécharger vos propres vidéos'},
                {'start': 13.0, 'end': 16.0, 'text': 'Et générer des sous-titres en plusieurs langues'},
                {'start': 17.0, 'end': 20.0, 'text': 'Merci d\'utiliser notre service'}
            ],
            'de': [
                {'start': 1.0, 'end': 4.0, 'text': 'Willkommen bei unserem Untertiteligenerator'},
                {'start': 5.0, 'end': 8.0, 'text': 'Dieses Video demonstriert Untertitefunktionalität'},
                {'start': 9.0, 'end': 12.0, 'text': 'Sie können Ihre eigenen Videos hochladen'},
                {'start': 13.0, 'end': 16.0, 'text': 'Und Untertitel in mehreren Sprachen generieren'},
                {'start': 17.0, 'end': 20.0, 'text': 'Danke, dass Sie unseren Service nutzen'}
            ],
            'pt': [
                {'start': 1.0, 'end': 4.0, 'text': 'Bem-vindo ao nosso gerador de legendas'},
                {'start': 5.0, 'end': 8.0, 'text': 'Este vídeo demonstra a funcionalidade da legenda'},
                {'start': 9.0, 'end': 12.0, 'text': 'Você pode fazer upload de seus próprios vídeos'},
                {'start': 13.0, 'end': 16.0, 'text': 'E gerar legendas em vários idiomas'},
                {'start': 17.0, 'end': 20.0, 'text': 'Obrigado por usar nosso serviço'}
            ]
        }
        
        # Get subtitles for the target language, default to English if not available
        subtitles = subtitle_data.get(target_language, subtitle_data['en'])
        
        # Create SRT file content
        srt_content = ""
        for i, subtitle in enumerate(subtitles, 1):
            start_time = format_time(subtitle['start'])
            end_time = format_time(subtitle['end'])
            srt_content += f"{i}\n{start_time} --> {end_time}\n{subtitle['text']}\n\n"
        
        # Save SRT file
        srt_filename = f"{job_id}.srt"
        srt_path = os.path.join(app.config['PROCESSED_FOLDER'], srt_filename)
        
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        # For demo purposes, we'll return the original file as "processed"
        # In a real implementation, you'd burn subtitles into the video
        processed_filename = f"{job_id}_{secure_filename(os.path.basename(file_path))}"
        processed_path = os.path.join(app.config['PROCESSED_FOLDER'], processed_filename)
        
        # Copy the original file as "processed" for demo
        import shutil
        shutil.copy2(file_path, processed_path)
        
        return {
            'success': True,
            'job_id': job_id,
            'subtitles': subtitles,
            'srt_file': srt_filename,
            'processed_file': processed_filename,
            'has_video': file_path.lower().endswith(('.mp4', '.avi', '.mov'))
        }
        
    except Exception as e:
        logger.error(f"Error generating subtitles: {str(e)}")
        return {'success': False, 'error': str(e)}

def format_time(seconds):
    """Convert seconds to SRT time format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_subtitles_route():
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'File type not allowed'})
        
        # Get target language
        target_language = request.form.get('language', 'en')
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        logger.info(f"File uploaded: {filename}, language: {target_language}")
        
        # Generate subtitles
        result = generate_subtitles(file_path, target_language)
        
        if result['success']:
            return jsonify({
                'success': True,
                'job_id': result['job_id'],
                'subtitles': result['subtitles'],
                'srt_file': result['srt_file'],
                'processed_file': result['processed_file'],
                'has_video': result['has_video'],
                'download_link': result['processed_file']
            })
        else:
            return jsonify({'success': False, 'error': result['error']})
            
    except Exception as e:
        logger.error(f"Error in generate route: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'success': False, 'error': 'File not found'})
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/video/<filename>')
def serve_video(filename):
    try:
        file_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
        if os.path.exists(file_path):
            return send_file(file_path)
        else:
            return jsonify({'success': False, 'error': 'File not found'})
    except Exception as e:
        logger.error(f"Error serving video: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/subtitle/<filename>')
def serve_subtitle(filename):
    try:
        file_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'success': False, 'error': 'File not found'})
    except Exception as e:
        logger.error(f"Error serving subtitle: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)