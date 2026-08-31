# Thermodynamic Fluids Explorer — Flask MVP

A web version of the desktop thermodynamics app. It supports single-state and liquid-only temperature-range calculations, multiple fluids and properties, CSV downloads, interactive Plotly charts, and browser-local fluid customization.

## Run locally

```bash
cd flask_web_mvp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app run --debug
```

Open <http://127.0.0.1:5000>.

Plotly is bundled locally, so calculations and charts work without an internet connection.

Public requests are limited to 10 fluids and 100 temperature points to keep scientific calculations responsive on small hosting instances.

Suggestions, bug reports, and incorrect-result reports are submitted from the browser to Formspree. The form includes optional contact information, optional disclosed browser diagnostics, and a spam honeypot; feedback is not written to the Flask server filesystem.

## Production command

```bash
gunicorn app:app
```

The 16 records in this folder's independent `fluids.csv` are immutable defaults. Added fluids, hidden defaults, and drag-and-drop ordering are stored in the browser's `localStorage`, so every browser gets its own customized list and no fluid-management action writes to CSV. “Reset to all defaults” clears those customizations. Clearing browser site data also resets the list.

Property customization works the same way: users can add from a validated supported catalog, hide default properties, search, drag to reorder, and reset the list. Each browser stores its property choices and ordering locally.
