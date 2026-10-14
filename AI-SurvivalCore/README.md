# AI Survival Core

AI Survival Core is a Streamlit simulation dashboard for exploring facility resource allocation, storm scenarios, and recovery behavior. All readings are simulated; this is not a certified safety-control system.

## What it includes

- An incident-command dashboard with readiness, resource capacity, service health, and a prioritized simulated response.
- Five fault scenarios, including a compound disaster, with explainable power and CPU allocation decisions.
- One-step and guided recovery controls, an auditable recovery timeline, and CSV exports.
- A scenario lab that compares readiness, essential-service protection, and power allocation across simulations.
- Sensor plausibility checks driven by simulated time, so repeated recovery cycles behave consistently regardless of UI speed.

## Run locally

Python 3.13 is recommended.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open `http://localhost:8501`.

## Deploy with Docker

```sh
docker build -t ai-survival-core .
docker run --rm --name ai-survival-core -p 8501:8501 ai-survival-core
```

The image runs as a non-root user, exposes port `8501`, disables Streamlit telemetry, and includes a health check at `/_stcore/health`. Open `http://localhost:8501` after the container starts.

For a container platform, publish this image and route traffic to port `8501`. The app already listens on `0.0.0.0`, runs headlessly, and keeps its Streamlit error details private in production.

## Deploy to Streamlit Community Cloud

Connect this repository in Streamlit Community Cloud, select `app.py` as the main file, and deploy. The root `requirements.txt` installs the app dependencies. Keep credentials out of the repository; configure any future secrets in the hosting provider's secrets manager.

## Deployment checks

The included GitHub Actions workflow verifies the dashboard and core simulation on every push and pull request. Run the same checks locally before releasing:

```sh
python -m pip install pytest mypy
python -m pytest -q
python -m mypy app.py core --ignore-missing-imports --follow-imports=skip
```

## Tests

Install the test runner separately, then run:

```sh
python -m pip install pytest
python -m pytest -q
```
