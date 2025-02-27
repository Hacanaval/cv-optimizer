document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('optimizerForm');
    const fileInput = document.getElementById('cvFile');
    const cvTextarea = document.getElementById('cvText');
    const submitBtn = document.querySelector('.submit-btn');
    const btnText = document.querySelector('.btn-text');
    const loader = document.querySelector('.loader');
    const results = document.getElementById('results');
    const fileName = document.getElementById('fileName');
    const processingStatus = document.getElementById('processingStatus');
    const errorMessage = document.getElementById('errorMessage');

    // Mostrar nombre del archivo seleccionado
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            fileName.textContent = file.name;
            
            // Mostrar estado de procesamiento
            showProcessingStatus('Leyendo archivo...');
            
            const formData = new FormData();
            formData.append('file', file);

            fetch('/process_file', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                cvTextarea.value = data.text;
                hideProcessingStatus();
            })
            .catch(error => {
                showError('Error al procesar el archivo: ' + error.message);
                hideProcessingStatus();
            });
        } else {
            fileName.textContent = '';
        }
    });

    // Manejar el envío del formulario
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Validaciones
        if (!cvTextarea.value.trim()) {
            showError('Por favor, ingresa tu CV');
            return;
        }
        
        const linkedinUrl = document.getElementById('linkedinUrl').value;
        if (!linkedinUrl.includes('linkedin.com/jobs/view/')) {
            showError('Por favor, ingresa una URL válida de LinkedIn Jobs');
            return;
        }

        // Ocultar mensajes de error previos
        hideError();
        
        // Mostrar estado de procesamiento
        showProcessingStatus('Optimizando tu CV...');

        // Deshabilitar botón y mostrar loader
        setLoadingState(true);

        try {
            const formData = new FormData();
            formData.append('cv_text', cvTextarea.value);
            formData.append('linkedin_url', linkedinUrl);

            const response = await fetch('/optimize', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            // Mostrar resultados
            document.getElementById('cvEsResult').value = data.cv_es;
            document.getElementById('cvEnResult').value = data.cv_en;
            results.style.display = 'block';

            // Configurar botones de descarga
            document.querySelectorAll('.download-btn').forEach(btn => {
                btn.onclick = function() {
                    const lang = this.dataset.lang;
                    const text = lang === 'es' ? data.cv_es : data.cv_en;
                    const filename = lang === 'es' ? data.es_filename : data.en_filename;
                    
                    downloadFile(text, filename);
                };
            });

            // Ocultar estado de procesamiento
            hideProcessingStatus();

        } catch (error) {
            showError('Error: ' + error.message);
        } finally {
            setLoadingState(false);
        }
    });

    // Funciones auxiliares
    function setLoadingState(isLoading) {
        btnText.style.display = isLoading ? 'none' : 'block';
        loader.style.display = isLoading ? 'block' : 'none';
        submitBtn.disabled = isLoading;
    }

    function showProcessingStatus(message) {
        processingStatus.querySelector('.status-text').textContent = message;
        processingStatus.style.display = 'flex';
    }

    function hideProcessingStatus() {
        processingStatus.style.display = 'none';
    }

    function showError(message) {
        errorMessage.querySelector('.error-text').textContent = message;
        errorMessage.style.display = 'flex';
    }

    function hideError() {
        errorMessage.style.display = 'none';
    }

    function downloadFile(content, filename) {
        const blob = new Blob([content], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }
});