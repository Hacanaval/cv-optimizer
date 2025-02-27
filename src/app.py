from flask import Flask, render_template, request, jsonify, send_file
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from file_processor import FileProcessor
from job_cv_optimizer import scrape_linkedin_vacancy_with_selenium, optimize_cv_with_gemini, clean_filename, build_custom_json, guardar_en_dataframe

app = Flask(__name__)

# Configuraciones
UPLOAD_FOLDER = 'temp_uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# Asegurarse que existe el directorio de uploads
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def save_to_history(cv_original, cv_es, cv_en, vacancy_data):
    try:
        history_file = 'optimization_history.json'
        
        if os.path.exists(history_file):
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        else:
            history = []
        
        new_record = {
            'fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'empresa': vacancy_data.get("Nombre de la empresa", "NA"),
            'puesto': vacancy_data.get("Título del puesto", "NA"),
            'linkedin_url': vacancy_data.get("Enlace de la vacante", "NA"),
            'cv_original': cv_original,
            'cv_es': cv_es,
            'cv_en': cv_en
        }
        
        history.append(new_record)
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=4)
            
    except Exception as e:
        print(f"Error guardando histórico: {e}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process_file', methods=['POST'])
def process_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    try:
        text = FileProcessor.process_file(file)
        return jsonify({'text': text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/optimize', methods=['POST'])
def optimize():
    try:
        cv_text = request.form.get('cv_text')
        linkedin_url = request.form.get('linkedin_url')
        
        if not cv_text:
            return jsonify({'error': 'No se proporcionó el texto del CV'}), 400
        
        if not linkedin_url:
            return jsonify({'error': 'No se proporcionó la URL de LinkedIn'}), 400
        
        with open("input_cv.txt", "w", encoding="utf-8") as f:
            f.write(cv_text)
        
        vacancy_data = scrape_linkedin_vacancy_with_selenium(linkedin_url)
        
        if vacancy_data is None:
            return jsonify({'error': 'No se pudo extraer información de LinkedIn'}), 400
            
        cv_es, cv_en = optimize_cv_with_gemini(vacancy_data, cv_text)
        
        save_to_history(cv_text, cv_es, cv_en, vacancy_data)
        
        job_title = clean_filename(vacancy_data["Título del puesto"])
        company_name = clean_filename(vacancy_data["Nombre de la empresa"])
        
        # Generar nombres de archivo para TXT
        es_filename = f"{job_title}-{company_name}_es.txt"
        en_filename = f"{job_title}-{company_name}_en.txt"
        
        # Guardar archivos TXT
        with open(es_filename, "w", encoding="utf-8") as f:
            f.write(cv_es)
        with open(en_filename, "w", encoding="utf-8") as f:
            f.write(cv_en)
        
        # Guardar información de la vacante
        custom_json = build_custom_json(vacancy_data)
        json_filename = f"{job_title}-{company_name}.json"
        
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(custom_json, f, ensure_ascii=False, indent=4)
        
        guardar_en_dataframe(custom_json)
            
        return jsonify({
            'success': True,
            'cv_es': cv_es,
            'cv_en': cv_en,
            'es_filename': es_filename,
            'en_filename': en_filename,
            'vacancy_data': vacancy_data
        })
        
    except Exception as e:
        import traceback
        print("Error detallado:", traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'El archivo es demasiado grande. Tamaño máximo: 16MB'}), 413

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Error interno del servidor'}), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Recurso no encontrado'}), 404

if __name__ == '__main__':
    app.run(debug=True)