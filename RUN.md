# How to Run ScholarGraph

Follow these steps every time you want to run the project.

## 1. Start the backend

Open a terminal (PowerShell or Command Prompt) and run:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Leave this terminal open.** You should see:
- `Uvicorn running on http://0.0.0.0:8000`
- `Application startup complete.`

- **If you don't have a venv yet:**  
  `python -m venv .venv` then run the commands above.  
  Install deps first: `pip install -r requirements.txt`

## 2. Start the frontend

Open a **second** terminal and run:

```powershell
cd frontend
npm install
npm run dev
```

**Leave this terminal open.** You should see:
- `Local: http://localhost:3000` (or `http://localhost:3001` if 3000 is in use)

## 3. Open the app

In your browser go to: **http://localhost:3000**

- Use **Upload** to add documents (backend must be running).
- API docs: **http://localhost:8000/docs**

## Quick checklist

| Step            | Command / URL |
|-----------------|---------------|
| Terminal 1      | `cd backend` → activate venv → `uvicorn main:app --reload --host 0.0.0.0 --port 8000` |
| Terminal 2      | `cd frontend` → `npm run dev` |
| Open in browser | http://localhost:3000 |
| Backend API     | http://localhost:8000/docs |

If upload says "make sure backend is running", the backend is not running or not on port 8000—go back to step 1.
