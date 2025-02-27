import os
import docx
import PyPDF2
from werkzeug.utils import secure_filename

class FileProcessor:
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}

    @staticmethod
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in FileProcessor.ALLOWED_EXTENSIONS

    @staticmethod
    def extract_text_from_docx(file_path):
        """Extrae texto de un archivo DOCX."""
        try:
            doc = docx.Document(file_path)
            full_text = []
            for para in doc.paragraphs:
                if para.text.strip():  # Solo añade párrafos no vacíos
                    full_text.append(para.text)
            return '\n'.join(full_text)
        except Exception as e:
            print(f"Error procesando archivo DOCX: {e}")
            return None

    @staticmethod
    def extract_text_from_pdf(file_path):
        """Extrae texto de un archivo PDF."""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = []
                for page in pdf_reader.pages:
                    text.append(page.extract_text())
                return '\n'.join(text)
        except Exception as e:
            print(f"Error procesando archivo PDF: {e}")
            return None

    @staticmethod
    def get_file_extension(filename):
        """Obtiene la extensión del archivo."""
        return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

    @staticmethod
    def save_temp_file(file):
        """Guarda un archivo temporal y retorna su ruta."""
        try:
            # Crear directorio temporal si no existe
            temp_dir = os.path.join(os.getcwd(), 'temp_uploads')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Guardar archivo
            filename = secure_filename(file.filename)
            temp_path = os.path.join(temp_dir, filename)
            file.save(temp_path)
            return temp_path
        except Exception as e:
            print(f"Error guardando archivo temporal: {e}")
            return None

    @staticmethod
    def process_file(file):
        """Procesa un archivo y extrae su texto."""
        try:
            if not file or not FileProcessor.allowed_file(file.filename):
                raise ValueError("Tipo de archivo no permitido")

            # Guardar archivo temporalmente
            temp_path = FileProcessor.save_temp_file(file)
            if not temp_path:
                raise ValueError("Error al guardar archivo temporal")

            try:
                # Obtener extensión del archivo
                extension = FileProcessor.get_file_extension(file.filename)
                
                # Procesar según el tipo de archivo
                if extension == 'txt':
                    with open(temp_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                elif extension == 'pdf':
                    text = FileProcessor.extract_text_from_pdf(temp_path)
                elif extension in ['doc', 'docx']:
                    text = FileProcessor.extract_text_from_docx(temp_path)
                else:
                    raise ValueError(f"Formato de archivo no soportado: {extension}")

                if text is None:
                    raise ValueError("No se pudo extraer texto del archivo")

                return text.strip()

            finally:
                # Limpiar archivo temporal
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        except Exception as e:
            raise Exception(f"Error procesando archivo: {str(e)}")