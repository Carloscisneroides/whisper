import os
import whisper
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

print("Cargando modelo large-v3... (puede tardar un momento)")
model = whisper.load_model("large-v3")
print("Modelo listo.")

HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Whisper Transcriptor</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #0f0f0f;
      color: #f0f0f0;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .card {
      background: #1a1a1a;
      border: 1px solid #2a2a2a;
      border-radius: 16px;
      padding: 40px;
      width: 100%;
      max-width: 640px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    }
    h1 {
      font-size: 1.6rem;
      font-weight: 700;
      margin-bottom: 6px;
      color: #fff;
    }
    p.subtitle {
      color: #888;
      font-size: 0.9rem;
      margin-bottom: 32px;
    }
    .upload-area {
      border: 2px dashed #333;
      border-radius: 12px;
      padding: 40px 20px;
      text-align: center;
      cursor: pointer;
      transition: border-color 0.2s, background 0.2s;
      position: relative;
    }
    .upload-area:hover, .upload-area.drag-over {
      border-color: #6c63ff;
      background: #1e1b2e;
    }
    .upload-area input[type="file"] {
      position: absolute;
      inset: 0;
      opacity: 0;
      cursor: pointer;
      width: 100%;
      height: 100%;
    }
    .upload-icon { font-size: 2.5rem; margin-bottom: 12px; }
    .upload-area .label { color: #aaa; font-size: 0.95rem; }
    .upload-area .label span { color: #6c63ff; font-weight: 600; }
    .file-name {
      margin-top: 16px;
      font-size: 0.85rem;
      color: #6c63ff;
      min-height: 20px;
    }
    button {
      margin-top: 24px;
      width: 100%;
      padding: 14px;
      background: #6c63ff;
      color: #fff;
      border: none;
      border-radius: 10px;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s, opacity 0.2s;
    }
    button:hover:not(:disabled) { background: #574fd6; }
    button:disabled { opacity: 0.5; cursor: not-allowed; }
    .status {
      margin-top: 20px;
      font-size: 0.88rem;
      color: #888;
      text-align: center;
      min-height: 22px;
    }
    .result-box {
      margin-top: 24px;
      background: #111;
      border: 1px solid #2a2a2a;
      border-radius: 10px;
      padding: 20px;
      display: none;
    }
    .result-box h2 {
      font-size: 0.85rem;
      color: #666;
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 12px;
    }
    .result-text {
      color: #e0e0e0;
      line-height: 1.7;
      font-size: 0.95rem;
      white-space: pre-wrap;
    }
    .copy-btn {
      margin-top: 16px;
      width: auto;
      padding: 8px 18px;
      background: #222;
      border: 1px solid #333;
      color: #aaa;
      font-size: 0.82rem;
      font-weight: 500;
      border-radius: 7px;
    }
    .copy-btn:hover { background: #2a2a2a; color: #fff; }
    .spinner {
      display: inline-block;
      width: 16px; height: 16px;
      border: 2px solid #ffffff44;
      border-top-color: #fff;
      border-radius: 50%;
      animation: spin 0.7s linear infinite;
      vertical-align: middle;
      margin-right: 8px;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>
  <div class="card">
    <h1>🎙️ Whisper Transcriptor</h1>
    <p class="subtitle">Modelo: <strong>large-v3</strong> &mdash; Transcripción automática en español</p>

    <div class="upload-area" id="uploadArea">
      <input type="file" id="audioFile" accept=".mp3,.wav,.m4a,.ogg,.flac,.webm" />
      <div class="upload-icon">📁</div>
      <div class="label">Arrastra tu archivo aquí o <span>haz clic para seleccionar</span></div>
    </div>
    <div class="file-name" id="fileName"></div>

    <button id="transcribeBtn" disabled>Transcribir</button>
    <div class="status" id="status"></div>

    <div class="result-box" id="resultBox">
      <h2>Transcripción</h2>
      <div class="result-text" id="resultText"></div>
      <button class="copy-btn" id="copyBtn">Copiar texto</button>
    </div>
  </div>

  <script>
    const fileInput = document.getElementById('audioFile');
    const fileNameEl = document.getElementById('fileName');
    const transcribeBtn = document.getElementById('transcribeBtn');
    const statusEl = document.getElementById('status');
    const resultBox = document.getElementById('resultBox');
    const resultText = document.getElementById('resultText');
    const copyBtn = document.getElementById('copyBtn');
    const uploadArea = document.getElementById('uploadArea');

    fileInput.addEventListener('change', () => {
      if (fileInput.files[0]) {
        fileNameEl.textContent = '✓ ' + fileInput.files[0].name;
        transcribeBtn.disabled = false;
      }
    });

    uploadArea.addEventListener('dragover', e => { e.preventDefault(); uploadArea.classList.add('drag-over'); });
    uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('drag-over'));
    uploadArea.addEventListener('drop', e => {
      e.preventDefault();
      uploadArea.classList.remove('drag-over');
      const file = e.dataTransfer.files[0];
      if (file) {
        fileInput.files = e.dataTransfer.files;
        fileNameEl.textContent = '✓ ' + file.name;
        transcribeBtn.disabled = false;
      }
    });

    transcribeBtn.addEventListener('click', async () => {
      const file = fileInput.files[0];
      if (!file) return;

      transcribeBtn.disabled = true;
      resultBox.style.display = 'none';
      statusEl.innerHTML = '<span class="spinner"></span>Transcribiendo con modelo large-v3...';

      const formData = new FormData();
      formData.append('audio', file);

      try {
        const res = await fetch('/transcribe', { method: 'POST', body: formData });
        const data = await res.json();

        if (data.error) {
          statusEl.textContent = '❌ Error: ' + data.error;
        } else {
          statusEl.textContent = '✅ Listo';
          resultText.textContent = data.text;
          resultBox.style.display = 'block';
        }
      } catch (err) {
        statusEl.textContent = '❌ Error de conexión';
      } finally {
        transcribeBtn.disabled = false;
      }
    });

    copyBtn.addEventListener('click', () => {
      navigator.clipboard.writeText(resultText.textContent);
      copyBtn.textContent = '¡Copiado!';
      setTimeout(() => copyBtn.textContent = 'Copiar texto', 2000);
    });
  </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "audio" not in request.files:
        return jsonify({"error": "No se recibió archivo"}), 400

    file = request.files["audio"]
    if file.filename == "":
        return jsonify({"error": "Archivo vacío"}), 400

    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)

    processed_path = path + "_processed.wav"

    try:
        # Preprocesar audio: mono, 16kHz, normalizar volumen, reducir ruido leve
        ret = os.system(
            f'ffmpeg -y -i "{path}" -af "loudnorm,highpass=f=80,lowpass=f=8000" -ar 16000 -ac 1 "{processed_path}" -loglevel error'
        )
        audio_to_transcribe = processed_path if ret == 0 and os.path.exists(processed_path) else path

        result = model.transcribe(
            audio_to_transcribe,
            language="es",
            beam_size=5,
            best_of=5,
            temperature=0,
            condition_on_previous_text=True,
            word_timestamps=True,
            initial_prompt=(
                "Transcripción de audiencia judicial en español. "
                "Participantes: juez, abogado, fiscal, demandante, demandado, testigo, secretario. "
                "Términos frecuentes: auto, sentencia, resolución, expediente, diligencia, notificación, "
                "apelación, recurso, amparo, tutela, demanda, contestación, prueba, testimonio, "
                "peritaje, incidente, providencia, decreto, juzgado, tribunal, magistrado, "
                "parte actora, parte demandada, acto administrativo, nulidad, prescripción."
            ),
        )
        return jsonify({"text": result["text"].strip()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        os.remove(path)
        if os.path.exists(processed_path):
            os.remove(processed_path)

if __name__ == "__main__":
    app.run(port=3001, debug=False)
