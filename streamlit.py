# streamlit.py
import streamlit as st
import os
import sys
import io
import json  # Añadimos la importación explícita de json
from pathlib import Path

# Agregar la carpeta 'src/' al path de Python
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# Importar funciones necesarias desde job_cv_optimizer y file_processor
try:
    from job_cv_optimizer import (
        optimize_cv_with_gemini,
        clean_filename,
        build_custom_json,
        guardar_en_dataframe
    )
    from file_processor import FileProcessor
except ImportError as e:
    st.error("Error al importar módulos. Asegúrate de que los archivos job_cv_optimizer.py y file_processor.py estén en la carpeta src/.")
    st.error(f"Detalles del error: {str(e)}")
    st.stop()

# Clase auxiliar para adaptar UploadedFile de Streamlit a FileProcessor
class StreamlitFileAdapter:
    def __init__(self, uploaded_file):
        self.uploaded_file = uploaded_file
        self.filename = uploaded_file.name  # Nombre del archivo desde UploadedFile
        self.file_content = uploaded_file.read()  # Contenido del archivo

    def save(self, path):
        """Guarda el contenido del archivo en el path especificado."""
        with open(path, "wb") as f:
            f.write(self.file_content)

# Aplicar estilos personalizados con CSS
st.markdown(
    """
    <style>
        /* Contenedor Principal */
        .main-container {
            background-color: #f8f9fa;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            max-width: 800px;
            margin: 0 auto;
        }
        
        /* Título */
        .title {
            text-align: center;
            font-size: 34px;
            font-weight: bold;
            color: #4A56E2;
            margin-bottom: 20px;
        }

        /* Tarjeta de información */
        .info-box {
            background-color: #F5F7FF;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #4A56E2;
            margin-bottom: 20px;
        }

        .info-title {
            font-size: 20px;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }

        .info-text {
            font-size: 16px;
            color: #555;
            margin-bottom: 15px;
        }

        .info-list {
            padding-left: 20px;
            font-size: 16px;
            color: #555;
            margin-bottom: 15px;
        }

        .info-emphasis {
            font-style: italic;
            color: #666;
            font-size: 16px;
        }

        /* Botón de optimización y descarga */
        .stButton > button {
            background-color: #4A56E2;
            color: white;
            font-size: 18px;
            font-weight: bold;
            border-radius: 8px;
            padding: 12px;
            width: 100%;
            border: none;
            margin-top: 20px;
        }

        .stButton > button:hover {
            background-color: #3949ab;
        }

        /* Input field */
        .stTextInput > div > div > input {
            border-radius: 6px;
            padding: 12px;
            font-size: 16px;
            border: 1px solid #ccc;
        }

        /* Text area */
        .stTextArea > div > textarea {
            border-radius: 6px;
            padding: 12px;
            font-size: 16px;
            border: 1px solid #ccc;
        }

        /* Subtítulos */
        h3 {
            font-size: 18px;
            color: #333;
            margin-top: 20px;
            margin-bottom: 10px;
        }

        /* Placeholder text */
        .stTextArea > div > textarea::placeholder,
        .stTextInput > div > div > input::placeholder {
            color: #888;
            font-size: 16px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Contenedor principal
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Título de la aplicación
st.markdown('<h1 class="title">CV Optimizer</h1>', unsafe_allow_html=True)

# Sección de información general
st.markdown(
    '<div class="info-box">'
    '<p class="info-title">CV Optimizer</p>'
    '<p class="info-text">Optimiza tu hoja de vida para maximizar la compatibilidad con la vacante seleccionada, reorganizando y resaltando tus experiencias y habilidades existentes.</p>'
    '<p class="info-title">Formato Recomendado</p>'
    '<ul class="info-list">'
    '<li>Texto simple sin diseños o plantillas complejas</li>'
    '<li>Sin tablas, imágenes o elementos gráficos</li>'
    '<li>Estructura clara: Experiencia, Educación, Habilidades</li>'
    '</ul>'
    '<p class="info-emphasis">Un formato limpio facilita la lectura por sistemas ATS y mejora la optimización.</p>'
    '</div>',
    unsafe_allow_html=True
)

# Sección para manejar el CV
st.subheader("Tu CV")

# Permitir subir archivo (TXT, PDF, Word)
uploaded_file = st.file_uploader("Subir CV (PDF, Word o TXT)", type=["txt", "pdf", "doc", "docx"])

# Área de texto para pegar manualmente (inicialmente vacía)
cv_text = st.text_area("Pega aquí tu CV en formato texto...", height=150, value="")

# Si se sube un archivo, procesarlo y mostrar el texto en el área de texto
if uploaded_file is not None:
    try:
        # Adaptar el objeto UploadedFile para que FileProcessor pueda procesarlo
        file_adapter = StreamlitFileAdapter(uploaded_file)
        
        # Procesar el archivo subido con FileProcessor
        cv_text = FileProcessor.process_file(file_adapter)
        if cv_text:
            # Actualizar el área de texto con el contenido extraído
            st.session_state['cv_text'] = cv_text
            cv_text = st.text_area("Pega aquí tu CV en formato texto...", height=150, value=cv_text, key="cv_text_area")
        else:
            st.error("No se pudo extraer texto del archivo subido.")
    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
elif 'cv_text' in st.session_state:
    # Mantener el texto del área de texto si ya se ha subido un archivo
    cv_text = st.text_area("Pega aquí tu CV en formato texto...", height=150, value=st.session_state['cv_text'], key="cv_text_area")

# Sección para ingresar la URL de LinkedIn
st.subheader("URL de LinkedIn")
linkedin_url = st.text_input("Pega aquí la URL de la vacante en LinkedIn", value="")

# Botón de optimización
if st.button("Optimizar CV", help="Generar un CV optimizado para esta vacante"):
    if not cv_text.strip():
        st.error("Por favor, pega tu CV en el campo de texto o sube un archivo.")
    elif not linkedin_url.strip():
        st.error("Por favor, ingresa la URL de LinkedIn.")
    else:
        try:
            # Usar datos dummy directamente (eliminando el scraping con Selenium)
            vacancy_data = {
                "Título del puesto": "Data Scientist",
                "Enlace de la vacante": linkedin_url if linkedin_url else "https://ejemplo.com/vacante",
                "Nombre de la empresa": "Tech Global",
                "Información del trabajo": "Buscamos un Data Scientist con experiencia en Python y Machine Learning para trabajar remoto.",
                "Requisitos": "Experiencia en Python, Pandas, Machine Learning, trabajo remoto, inglés fluido.",
                "Palabras clave": ["Python", "Machine Learning", "Data Science", "Remote", "English"],
                "Nombre del reclutador": "NA",
                "Correo electrónico": "NA",
                "WhatsApp": "NA",
                "Salario": "NA",
                "Horario laboral": "Tiempo completo",
                "Modalidad de trabajo": "Remoto",
                "Ubicación": "NA",
                "Beneficios": "NA"
            }

            # Optimizar el CV con Gemini
            st.info("Optimizando CV con inteligencia artificial...")
            cv_es, cv_en = optimize_cv_with_gemini(vacancy_data, cv_text)

            # Guardar la información en historial
            try:
                custom_json = build_custom_json(vacancy_data)
                guardar_en_dataframe(custom_json)
            except Exception as e:
                st.warning(f"Error al guardar el historial: {str(e)}")
                custom_json = vacancy_data  # Usar datos sin procesar si falla

            # Generar nombres de archivo dinámicos
            job_title = clean_filename(vacancy_data["Título del puesto"])
            company_name = clean_filename(vacancy_data["Nombre de la empresa"])
            filename_base = f"{job_title}-{company_name}"

            # Guardar archivos localmente
            try:
                with open(f"{filename_base}_es.txt", "w", encoding="utf-8") as f:
                    f.write(cv_es)
                with open(f"{filename_base}_en.txt", "w", encoding="utf-8") as f:
                    f.write(cv_en)
                with open(f"{filename_base}.json", "w", encoding="utf-8") as f:
                    json.dump(custom_json, f, ensure_ascii=False, indent=4)
            except Exception as e:
                st.warning(f"Error al guardar archivos localmente: {str(e)}")

            # Mostrar los resultados en la pantalla
            st.success("CV optimizado con éxito!")

            st.subheader("Versión en Español")
            st.text_area("CV Optimizado en Español", cv_es, height=250)

            st.subheader("Versión en Inglés")
            st.text_area("CV Optimizado en Inglés", cv_en, height=250)

            # Permitir descargar los archivos
            st.download_button(
                label="Descargar CV en Español (TXT)",
                data=cv_es,
                file_name=f"{filename_base}_es.txt",
                mime="text/plain"
            )
            st.download_button(
                label="Descargar CV en Inglés (TXT)",
                data=cv_en,
                file_name=f"{filename_base}_en.txt",
                mime="text/plain"
            )

        except Exception as e:
            st.error(f"Error durante la optimización: {str(e)}")

# Cierra el contenedor principal
st.markdown('</div>', unsafe_allow_html=True)