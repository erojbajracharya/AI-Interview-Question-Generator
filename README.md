# Project Title

A brief description of what this project does and who it's for

# AI‑Interview‑Question‑Generator – README (Windows Setup)

## Overview
This repository provides a Flask backend and a Vite + React frontend for generating AI‑powered interview questions. The steps below let you get the project up‑and‑running on a new Windows laptop.

---

## 1️⃣ Clone / copy the repository
```powershell
# Choose a location, e.g. D:\code
cd D:\code
# If you have a remote repository
git clone https://github.com/your-username/AI-Interview-Question-Generator.git   # replace with your fork
# Or simply copy the folder if you already have it locally
```

## 2️⃣ Install Python (3.10 + recommended)
- Download from https://www.python.org/downloads/windows/
- **Check “Add Python to PATH”** during installation.

## 3️⃣ Create & activate a virtual environment
```powershell
cd AI-Interview-Question-Generator
python -m venv venv
.\venv\Scripts\activate   # PowerShell
# (or `venv\Scripts\activate.bat` from cmd)
```

## 4️⃣ Install backend dependencies
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```
> Packages include `google-genai, spacy, PyPDF2, mysql-connector-python, numpy, Flask, Flask‑CORS, python‑dotenv`.

## 5️⃣ (Optional) Download the spaCy English model
```powershell
python -m spacy download en_core_web_sm
```

## 6️⃣ Set environment variables
Create a **`.env`** file in the project root (next to `app.py`) with:
```
GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE
```
Or set it directly in PowerShell:
```powershell
$env:GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"
```

## 7️⃣ Start the Flask backend
```powershell
python app.py
```
You should see:
```
Starting Flask Backend server on http://localhost:5000
 * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
```
Leave this terminal open.

## 8️⃣ Install Node.js (v20 + recommended)
- Download from https://nodejs.org/en/download/
- Ensure **Add to PATH** is selected.

## 9️⃣ Install frontend dependencies
```powershell
cd frontend
npm install
```

## 🔟 Run the Vite dev server
```powershell
npm run dev
```
You’ll see something like:
```
  VITE v8.0.12  ready in 420 ms

  ➜  Local:   http://127.0.0.1:5173/
  ➜  Network: http://192.168.1.12:5173/
```
Open the **Local** URL in a browser. The UI talks to the backend at `http://localhost:5000`.

---

### Quick sanity‑check
1. Visit `http://localhost:5000/api/roles` → JSON list of job roles.
2. In the UI, upload a sample resume (e.g., `sample-resume-samyam-data-scientist.pdf`) and click **Start Interview**.
3. Verify you receive generated questions.

If both succeed, the project is fully functional on the new laptop.

---

#### 📋 Checklist (tick as you complete)
- [ ] Clone / copy repo
- [ ] Install Python 3.10+
- [ ] `python -m venv venv && .\venv\Scripts\activate`
- [ ] `pip install -r requirements.txt`
- [ ] (optional) `python -m spacy download en_core_web_sm`
- [ ] Create `.env` with `GEMINI_API_KEY` (or set `$env:GEMINI_API_KEY`)
- [ ] `python app.py` (backend running)
- [ ] Install Node.js v20+
- [ ] `cd frontend && npm install`
- [ ] `npm run dev` (frontend running)
- [ ] Verify API (`/api/roles`) and UI workflow

---

### Troubleshooting hints
| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `pip` can’t find a package | Old pip / missing wheel | Run `python -m pip install --upgrade pip` then reinstall |
| `ImportError: No module named spacy` after install | spaCy model not downloaded | Run `python -m spacy download en_core_web_sm` |
| Frontend “fetch failed” (CORS) | Backend not running or wrong port | Ensure `python app.py` is active on **5000** |
| “No API key” error from `/api/interview/start` | `GEMINI_API_KEY` missing / typo | Double‑check `.env` file or `$env:GEMINI_API_KEY` value |

---

*Feel free to open an issue or contact the maintainer if any step fails.*
