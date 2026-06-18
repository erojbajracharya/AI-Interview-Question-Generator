[README (1).md](https://github.com/user-attachments/files/28805806/README.1.md)

# AI-Interview-Question-Generator

An end-to-end platform for automated resume screening and AI-powered interview question generation. This project uses a Flask backend, a React (Vite) frontend, and MySQL for persistent storage, leveraging Google's Gemini AI for parsing and evaluation.

## 🚀 Key Features

- **Automated Resume Parsing:** Converts PDF resumes to Markdown and extracts structured data (skills, experience) using Gemini AI.
- **Dynamic Resume Screening:** Screens candidates against job roles using a weighted matching algorithm.
- **AI-Powered Question Generation:** Generates tailored interview questions based on the candidate's profile and the selected job role.
- **API Key Rotation:** Supports multiple Gemini API keys to handle rate limits seamlessly.
- **Interview Simulation & Grading:** Conducts mock interviews and provides automated grading with detailed feedback.
- **Persistent History:** Saves candidate profiles, sessions, and evaluation reports in a MySQL database.
- **Reusable Question Pool:** Seeds and maintains a pool of high-quality questions for various roles and difficulties.

## 🛠️ Tech Stack

- **Backend:** Python, Flask, Flask-CORS, Google GenAI SDK, PyMuPDF4LLM, MySQL Connector, NumPy.
- **Frontend:** React 19, Vite, Lucide React (Icons).
- **Database:** MySQL.
- **AI Model:** Google Gemini (gemini-3-flash-preview).

---

## ⚙️ Setup & Installation

### Prerequisites
- **Python 3.10+**
- **Node.js v20+**
- **MySQL Server** (Running locally or accessible via network)

### 1. Database Setup
1.  Ensure MySQL is running.
2.  The database `ai_interview_db` and its tables are automatically created on first run by `db_helper.py`.
3.  **Important:** Open `db_helper.py` and update the `DB_CONFIG` dictionary with your MySQL `user` and `password`.
    ```python
    DB_CONFIG = {
        "host": "localhost",
        "user": "root",
        "password": "YOUR_PASSWORD_HERE",
        "database": "ai_interview_db"
    }
    ```

### 2. Backend Setup
1.  Navigate to the project root:
    ```powershell
    cd AI-Interview-Question-Generator
    ```
2.  Create and activate a virtual environment:
    ```powershell
    python -m venv venv
    .\venv\Scripts\activate  # Windows
    # source venv/bin/activate  # Linux/macOS
    ```
3.  Install dependencies:
    ```powershell
    pip install -r requirements.txt
    ```
4.  Configure environment variables. Create a `.env` file in the root:
    ```env
    AI_GEN_API_KEYS=key1,key2,key3
    ```
    *(You can provide one or more comma-separated Gemini API keys for rotation.)*

### 3. Frontend Setup
1.  Navigate to the `frontend` directory:
    ```powershell
    cd frontend
    ```
2.  Install dependencies:
    ```powershell
    npm install
    ```

---

## 🏃 Running the Application

### Start the Backend
From the root directory (with venv activated), you can initialize your API keys directly in the terminal and start the server:

```powershell
# Set your Gemini API key(s)
$env:AI_GEN_API_KEYS = "your_api_key_here"

# Run the Flask server
python app.py
```

*(Note: If you have multiple keys for rotation, separate them with commas: `"key1,key2"`. Alternatively, you can still use a `.env` file as described in the setup section.)*

The backend will start on `http://localhost:5000`. It will also initialize the database and seed default questions.

### Start the Frontend
From the `frontend` directory:
```powershell
npm run dev
```
Open the provided URL (typically `http://localhost:5173`) in your browser.

---

## 📂 Project Structure

- `app.py`: Main Flask entry point and API routes.
- `resume_parser.py`: Logic for PDF conversion and AI parsing.
- `resume_screener.py`: Algorithm for candidate screening.
- `question_generator.py`: Logic for AI question generation.
- `db_helper.py`: MySQL database operations and schema management.
- `api_rotator.py`: Manages rotation between multiple Gemini API keys.
- `frontend/`: React application code.
- `temp_uploads/`: Temporary storage for uploaded resumes.

---

## 📋 API Sanity Check

You can verify the backend is running by visiting:
- `http://localhost:5000/api/roles` - Returns available job roles.
- `http://localhost:5000/api/history` - Returns past interview sessions.

---

