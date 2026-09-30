# ExoDetect deployment

This folder is the minimal runtime application. It contains the trained model but no training data.

## Run locally

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install .
python -m streamlit run app.py
```

Open `http://localhost:8501`.

## Deploy to Render

1. Put the contents of this folder in a GitHub repository.
2. In Render, create a **Web Service** from that repository and select the **Free** plan.
3. Render reads `render.yaml`. If prompted manually, use:
   - Build command: `pip install -r requirements.txt && pip install .`
   - Start command: `streamlit run app.py --server.address 0.0.0.0 --server.port $PORT`

The trained model at `models/triage.joblib` must remain in the repository.

## Notes

MAST retrieval requires outbound network access and can be slow. In the app, leave **All sectors** unchecked for a fast one-sector retrieval. Render Free instances sleep after inactivity and do not retain uploaded files after restart.
