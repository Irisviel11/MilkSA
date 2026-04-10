# MilkSA — Price Cap Panic

A small economic management game built for Streamlit.

You are the manager of a milk company. Each turn, you choose:
- production
- sale price

Demand is elastic. After a few turns, the government imposes a price cap. At first the cap sits above the market price. Then it falls by 10% each turn until it sinks below production cost. The game ends only when the dairy is bankrupt.

## Files

- `streamlit_app.py` — browser version for Streamlit deployment
- `game_logic.py` — shared simulation logic
- `logo.png` — app logo
- `desktop_milgame.py` — optional local Tkinter desktop build
- `.streamlit/config.toml` — Streamlit theme
- `requirements.txt` — dependencies

## Run locally

From the repository root:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Deploy on Streamlit Community Cloud

1. Push the repository to GitHub.
2. In Streamlit Community Cloud, choose the repository and set the entrypoint file to `streamlit_app.py`.
3. Pick the Python version you want in Advanced settings.
4. Deploy.

## Notes

- The browser version is the one intended for public deployment.
- The desktop Tkinter file is included only as an extra local version.
