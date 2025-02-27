import json
import os
import re
import time
import datetime
import pandas as pd
from bs4 import BeautifulSoup

# Selenium y webdriver-manager para scraping
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import google.generativeai as genai

# Asegurar que los directorios existan
os.makedirs("data/raw", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)

# Configurar la API key de Gemini (desde variable de entorno o .env)
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except KeyError:
    from dotenv import load_dotenv
    load_dotenv()
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def clean_filename(text):
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'\s+', '_', text)
    return text.lower()

def translate_to_spanish(text):
    # Aquí se debería integrar una API real de traducción.
    return text

def detect_idioma(text):
    if "Job Description:" in text or "Responsibilities" in text:
        return "inglés"
    return "español"

def load_prompt():
    try:
        with open("data/raw/cv_prompt.txt", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print("Error al leer cv_prompt.txt:", e)
        return ""

def fallback_postprocess(raw_text):
    return {
        "Información___del___trabajo": raw_text,
        "Responsabilidades": None,
        "Requisitos": None,
        "Beneficios": None
    }

def postprocess_job_text(raw_text):
    prompt = f"""
Eres un experto en extracción de información de ofertas de empleo. Tu tarea es analizar el siguiente texto de una vacante y devolver únicamente un JSON válido, sin comentarios adicionales. El JSON debe tener exactamente las siguientes claves en español:
- "Información___del___trabajo": Un resumen conciso (máximo 200 palabras) de la descripción general del empleo.
- "Responsabilidades": Una lista (array de strings) con las principales responsabilidades.
- "Requisitos": Una lista (array de strings) con los requisitos del puesto.
- "Beneficios": Un string con la descripción de los beneficios ofrecidos, o null si no se mencionan.
Texto de la vacante:
{raw_text}
"""
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        debug_text = response.text.strip()
        print("Respuesta de postprocesamiento:", debug_text)
        # Limpiar delimitadores si existen
        cleaned_text = debug_text
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[len("```json"):].strip()
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3].strip()
        result_json = json.loads(cleaned_text)
        return result_json
    except Exception as e:
        print("Error en postprocesamiento con Gemini:", e)
        print("Usando fallback heurístico...")
        return fallback_postprocess(raw_text)

def scrape_linkedin_vacancy_with_selenium(job_detail_url):
    print("Extrayendo información de la vacante usando Selenium...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    try:
        driver.get(job_detail_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        
        title_element = soup.find("h1")
        title = title_element.get_text().strip() if title_element else "NA"
        
        company_element = soup.find("a", {"data-tracking-control-name": "public_jobs_topcard-org-name"})
        company_name = company_element.get_text().strip() if company_element else "NA"
        
        description_element = soup.find("div", class_="description__text")
        description = description_element.get_text().strip() if description_element else "NA"
        
        requirements = "NA"
        criteria_elements = soup.select(".description__job-criteria-list li")
        if criteria_elements:
            req_list = []
            for criteria in criteria_elements:
                header = criteria.find(class_="description__job-criteria-subheader")
                text_el = criteria.find(class_="description__job-criteria-text")
                if header and text_el:
                    req_list.append(f"{header.get_text().strip()}: {text_el.get_text().strip()}")
            if req_list:
                requirements = "\n- " + "\n- ".join(req_list)
        
        keywords = []
        if description != "NA" and requirements != "NA":
            combined_text = description + " " + requirements
            common_keywords = ["python", "machine learning", "data science", "remote", "english", "skills", "experience"]
            for word in combined_text.lower().split():
                if word in common_keywords and word.capitalize() not in keywords:
                    keywords.append(word.capitalize())
        if not keywords:
            keywords = ["Python", "Machine Learning", "Data Science", "Remote", "English"]

        vacancy_data = {
            "Título del puesto": title,
            "Enlace de la vacante": job_detail_url,
            "Nombre de la empresa": company_name,
            "Información del trabajo": description,
            "Requisitos": requirements,
            "Palabras clave": keywords,
            "Nombre del reclutador": "NA",
            "Correo electrónico": "NA",
            "WhatsApp": "NA",
            "Salario": "NA",
            "Horario laboral": "Tiempo completo",
            "Modalidad de trabajo": "Remoto",
            "Ubicación": "NA",
            "Beneficios": "NA"
        }
        print("Datos extraídos:", vacancy_data)
        return vacancy_data
    except Exception as e:
        print("Error durante el scraping con Selenium:", e)
        return None
    finally:
        driver.quit()

def optimize_cv_with_gemini(vacancy_data, cv_description):
    print("Optimizando el CV con Gemini 2.0 Flash...")
    prompt = f"""
Eres un asistente experto en optimización de currículums. Toma la siguiente hoja de vida base:
{cv_description}

Y la siguiente información de la vacante:
Título del puesto: {vacancy_data["Título del puesto"]}
Nombre de la empresa: {vacancy_data["Nombre de la empresa"]}
Información del trabajo: {vacancy_data["Información del trabajo"]}
Requisitos: {vacancy_data["Requisitos"]}
Responsabilidades: { " ".join(vacancy_data.get("Palabras clave", [])) }

Optimiza la hoja de vida para que se alinee perfectamente con esta vacante, resaltando las habilidades, experiencia y logros relevantes. No inventes información; conserva los datos personales (nombre, correo, LinkedIn, teléfono) sin cambios. 

Genera dos versiones:
1. Una versión en español que comience con: 
"Hoja de Vida Optimizada para {vacancy_data['Título del puesto']} – {vacancy_data['Nombre de la empresa']} – Versión en Español"
2. Una versión en inglés que comience con:
"Optimized Resume for {vacancy_data['Título del puesto']} – {vacancy_data['Nombre de la empresa']} – English Version"

Asegúrate de reestructurar la experiencia profesional y resaltar las secciones clave (Perfil Profesional, Habilidades, Experiencia Profesional, Educación, Idiomas) de forma que sean compatibles con sistemas ATS.
"""
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        optimized_text = response.text.strip()
        print("Respuesta de optimización:", optimized_text)
        
        if "Hoja de Vida Optimizada para" in optimized_text and "Optimized Resume for" in optimized_text:
            parts = optimized_text.split("Optimized Resume for")
            optimized_cv_es = parts[0].strip()
            optimized_cv_en = "Optimized Resume for" + parts[1].strip()
        else:
            optimized_cv_es = optimized_text
            optimized_cv_en = optimized_text
            
        if optimized_cv_es.strip() == cv_description.strip():
            print("Advertencia: La versión optimizada en español es idéntica al CV base.")
        return optimized_cv_es, optimized_cv_en
    except Exception as e:
        print(f"Error al optimizar el CV con Gemini: {e}")
        return optimize_cv_manual(vacancy_data, cv_description)

def optimize_cv_manual(vacancy_data, cv_description):
    print("Usando optimización manual como respaldo...")
    optimized_cv_es = f"""Hoja de Vida Optimizada para {vacancy_data["Título del puesto"]} – {vacancy_data["Nombre de la empresa"]} – Versión en Español

{cv_description}
"""
    optimized_cv_en = f"""Optimized Resume for {vacancy_data["Título del puesto"]} – {vacancy_data["Nombre de la empresa"]} – English Version

{cv_description}
"""
    return optimized_cv_es, optimized_cv_en

def build_custom_json(vacancy_data):
    fecha_solicitud = datetime.datetime.now().strftime("%d-%m-%Y")
    idioma_input = detect_idioma(vacancy_data["Información del trabajo"])
    idioma_publicacion = "inglés" if idioma_input == "inglés" else "español"
    
    if vacancy_data["Información del trabajo"] != "NA":
        processed = postprocess_job_text(vacancy_data["Información del trabajo"])
    else:
        processed = {
            "Información___del___trabajo": None,
            "Responsabilidades": None,
            "Requisitos": None,
            "Beneficios": None
        }
    
    custom_json = {
        "Fecha___de___la___solicitud": fecha_solicitud,
        "Enlace___de___la___vacante": vacancy_data.get("Enlace de la vacante", "NA"),
        "Idioma___de___la___publicación": idioma_publicacion,
        "Título___del___puesto": vacancy_data.get("Título del puesto", "NA"),
        "Nombre___de___la___empresa": vacancy_data.get("Nombre de la empresa", "NA"),
        "Nombre___del___reclutador": vacancy_data.get("Nombre del reclutador", "NA"),
        "Correo___electrónico": vacancy_data.get("Correo electrónico", "NA"),
        "WhatsApp": vacancy_data.get("WhatsApp", "NA"),
        "Información___del___trabajo": processed.get("Información___del___trabajo", vacancy_data.get("Información del trabajo", "NA")),
        "Responsabilidades": processed.get("Responsabilidades", None),
        "Requisitos": processed.get("Requisitos", None),
        "Salario": vacancy_data.get("Salario", None),
        "Horario___laboral": vacancy_data.get("Horario laboral", None),
        "Modalidad___de___trabajo": vacancy_data.get("Modalidad de trabajo", None),
        "Ubicación": vacancy_data.get("Ubicación", None),
        "Beneficios": processed.get("Beneficios", None)
    }
    return custom_json

def guardar_en_dataframe(custom_json, csv_filename="data/processed/jobs.CSV"):
    df_nueva = pd.DataFrame([custom_json])
    if os.path.exists(csv_filename):
        df_existente = pd.read_csv(csv_filename)
        df_final = pd.concat([df_existente, df_nueva], ignore_index=True)
    else:
        df_final = df_nueva
    df_final.to_csv(csv_filename, index=False)
    print(f"Datos almacenados en el DataFrame y guardados en {csv_filename}.")

def main():
    print("Iniciando el proceso de procesamiento de vacantes...")
    job_detail_url = "https://www.linkedin.com/jobs/view/4119032958"
    
    vacancy_data = scrape_linkedin_vacancy_with_selenium(job_detail_url)
    
    if vacancy_data is None:
        print("No se pudo extraer la información de la vacante. Se utilizarán datos dummy (todo NA).")
        vacancy_data = {
            "Título del puesto": "NA",
            "Enlace de la vacante": "NA",
            "Nombre de la empresa": "NA",
            "Información del trabajo": "NA",
            "Requisitos": "NA",
            "Palabras clave": [],
            "Nombre del reclutador": "NA",
            "Correo electrónico": "NA",
            "WhatsApp": "NA",
            "Salario": "NA",
            "Horario laboral": "NA",
            "Modalidad de trabajo": "NA",
            "Ubicación": "NA",
            "Beneficios": "NA"
        }
    
    try:
        with open("data/raw/input_cv.txt", "r", encoding="utf-8") as f:
            cv_description = f.read()
    except Exception as e:
        print("Error al leer input_cv.txt:", e)
        cv_description = ""

    if vacancy_data["Información del trabajo"] == "NA":
        cv_es = cv_description
        cv_en = cv_description
    else:
        cv_es, cv_en = optimize_cv_with_gemini(vacancy_data, cv_description)
    
    custom_json = build_custom_json(vacancy_data)
    guardar_en_dataframe(custom_json)
    
    job_title = clean_filename(vacancy_data["Título del puesto"])
    company_name = clean_filename(vacancy_data["Nombre de la empresa"])
    
    # Crear nombres de archivo con rutas completas
    output_dir = "data/processed"
    filename_base = os.path.join(output_dir, f"{job_title}-{company_name}")
    
    try:
        with open(f"{filename_base}_es.txt", "w", encoding="utf-8") as f:
            f.write(cv_es)
        with open(f"{filename_base}_en.txt", "w", encoding="utf-8") as f:
            f.write(cv_en)
        with open(f"{filename_base}.json", "w", encoding="utf-8") as f:
            json.dump(custom_json, f, ensure_ascii=False, indent=4)
        
        print(f"Proceso completado exitosamente. Archivos generados en {output_dir}/")
    except Exception as e:
        print("Error al guardar los archivos:", e)

if __name__ == "__main__":
    main()