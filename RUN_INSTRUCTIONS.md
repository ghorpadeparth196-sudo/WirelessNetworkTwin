# How to Run (Windows + VS Code)

You need two things installed first:

- **Python 3.9 or newer** - https://www.python.org/downloads/ (tick "Add Python to PATH" in the installer)
- **Node.js 18 or newer (LTS)** - https://nodejs.org/

Check them: open a terminal and run `python --version` and `node --version`.

You will use **two terminals** at the same time: one for the backend, one for the frontend.
In VS Code: open the `wireless-network-digital-twin` folder, then use **Terminal > New Terminal**.

---

## Terminal 1 - Backend (Flask)

**STEP 1:** Open a terminal.

**STEP 2:** Go to the backend folder.
```
cd backend
```

**STEP 3:** Create a virtual environment (only the first time).
```
python -m venv venv
```

**STEP 4:** Activate it.
```
venv\Scripts\activate
```
(If PowerShell says "running scripts is disabled", run this once and try again:
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.
Or use the Command Prompt (cmd) instead of PowerShell.)

**STEP 5:** Install the requirements (only the first time).
```
pip install -r requirements.txt
```

**STEP 6:** Run Flask.
```
python app.py
```
You should see: `Digital Twin API running on http://127.0.0.1:5000`.
Leave this terminal open. The SQLite database is created automatically.

Quick check: open http://127.0.0.1:5000/api/health in a browser. It should show `{"status":"ok"}`.

---

## Terminal 2 - Frontend (React + Vite)

**STEP 7:** Open another terminal (click the **+** in the VS Code terminal panel).

**STEP 8:** Go to the frontend folder and install packages (only the first time).
```
cd frontend
npm install
```

**STEP 9:** Start the frontend.
```
npm run dev
```

**STEP 10:** Open the localhost URL shown in the terminal (normally http://localhost:5173).

---

## Using the project

1. The campus, 4 access points and 25 users are already there.
2. Click **Start simulation**. Users start walking, signal values and AP loads change, alerts appear.
3. Click **Pause simulation** to freeze it, **Reset simulation** to go back to the start.
4. Drag an access point on the map to move it. Use **Turn off** in the AP table to simulate an AP failure.

## Stopping

Press `Ctrl + C` in each terminal. To run again later, repeat only STEP 2, 4, 6 (backend) and STEP 8 (`cd frontend`), 9 (frontend).

## Troubleshooting

| Problem | Fix |
|---|---|
| Red banner "Cannot reach the backend" | Terminal 1 is not running. Start it with `python app.py`. |
| `python` is not recognised | Reinstall Python and tick "Add Python to PATH", or try `py` instead of `python`. |
| Port 5000 already in use | Close the other program using it, or change the port at the bottom of `backend/app.py` and in `frontend/src/api.js`. |
| `npm install` fails | Check the internet connection and that `node --version` is 18 or higher. |
| Want a clean start (new database) | Stop the backend, delete `backend/database/digital_twin.db`, start it again. |
