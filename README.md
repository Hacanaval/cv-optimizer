# CV Optimizer

CV Optimizer es una aplicación web que optimiza hojas de vida para vacantes específicas de LinkedIn, utilizando IA para generar versiones personalizadas en español e inglés.

## 🚀 Características

- Interfaz web moderna e intuitiva
- Procesamiento de CV en múltiples formatos (PDF, Word, TXT)
- Scraping automático de ofertas de LinkedIn
- Optimización del CV usando IA (Gemini)
- Generación de versiones en español e inglés
- Seguimiento de aplicaciones en CSV
- Formato compatible con sistemas ATS

## 📋 Requisitos Previos

- Python 3.8 o superior
- Navegador web moderno
- API Key de Google Gemini
- Conexión a Internet

## 🛠️ Instalación

1. Clonar el repositorio:

git clone https://github.com/Hacanaval/cv-optimizer.git
cd cv-optimizer

2. Crear y activar entorno virtual:
#### Activarlo en Mac/Linux
source venv/bin/activate  

#### Activarlo en Windows
venv\Scripts\activate

3. Instalar dependencias:

pip install -r requirements.txt

4. Configurar variables de entorno:
   - Crear archivo `.env` en la raíz del proyecto
   - Añadir tu API key de Gemini:
     ```
     GEMINI_API_KEY=tu_api_key_aquí
     ```

## 💻 Uso

1. Iniciar la aplicación:

python src/app.py

2. Abrir en el navegador:
http://localhost:5000

3. Usar la aplicación:
   - Subir o pegar el CV en formato texto
   - Ingresar URL de LinkedIn Jobs
   - Hacer clic en "Optimizar CV"
   - Descargar versiones optimizadas

## 📁 Estructura del Proyecto
v-optimizer/
├── src/ # Código fuente
│ ├── app.py # Aplicación Flask
│ ├── job_cv_optimizer.py # Lógica principal
│ ├── file_processor.py # Procesamiento de archivos
│ ├── static/ # Archivos estáticos
│ └── templates/ # Plantillas HTML
├── data/ # Datos
│ ├── raw/ # Datos sin procesar
│ └── processed/ # Datos procesados
├── tests/ # Pruebas unitarias
└── notebooks/ # Jupyter notebooks

## 🔒 Seguridad

- No compartir el archivo `.env` ni la API Key
- Los datos procesados se guardan localmente
- Las credenciales y datos sensibles están protegidos

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo `LICENSE` para detalles.

## 👥 Autor

Hacanaval