# Posture Monitor

A real-time computer vision application that monitors desk posture using a webcam and alerts users when poor posture is sustained.

## Tech Stack

- Python
- OpenCV
- MediaPipe
- NumPy
- Streamlit + Plotly (analytics dashboard)

## Features

- Real-time posture monitoring
- Calibration-based tracking
- Slouch detection
- Forward head posture detection
- Desktop + sound notifications
- Session logging and an analytics dashboard (score trends, good/bad %, most frequent issues)

## Usage

```bash
pip install -r requirements.txt

# Run the live monitor (press C to calibrate, B after a break, Q to quit)
python src/app.py

# View session history in the dashboard
streamlit run src/dashboard.py
```
