# Thermodynamic Fluids Explorer — Flask MVP

A web version of the desktop thermodynamics app. It supports liquid-only temperature-range and fixed-temperature pressure-range calculations, multiple fluids and properties, CSV downloads, interactive Plotly charts, and browser-local customization.

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

Pressure inputs and results support pascals and atmospheres, with live conversion of entered values when units change. The reserved `temperature_pressure_surface` calculation mode and disabled interface option provide the framework for a future simultaneous temperature/pressure sweep with 3D Plotly surfaces.

Plotly data points support click-to-pin annotations. A pinned label shows the fluid, axis value, and property value until the same point is clicked again.

After a successful calculation with graphable results, the page scrolls to the first graph once Plotly finishes rendering it. The behavior respects the browser's reduced-motion preference.

The calculator remembers its mode, units, numeric inputs, selected fluids, and selected properties in browser `localStorage`. Reloading restores that state, while “Reset calculation selections” clears only calculator state and preserves customized fluid/property lists.

Suggestions, bug reports, and incorrect-result reports are submitted from the browser to Formspree. The form includes optional contact information, optional disclosed browser diagnostics, and a spam honeypot; feedback is not written to the Flask server filesystem.

## Production command

```bash
gunicorn app:app
```

The 16 records in this folder's independent `fluids.csv` are immutable defaults. Added fluids, hidden defaults, and drag-and-drop ordering are stored in the browser's `localStorage`, so every browser gets its own customized list and no fluid-management action writes to CSV. “Reset to all defaults” clears those customizations. Clearing browser site data also resets the list.

Property customization works the same way: users can add from a validated supported catalog, hide default properties, search, drag to reorder, and reset the list. Each browser stores its property choices and ordering locally.

Mass-basis heat capacity, enthalpy, entropy, Gibbs energy, molecular weight, melting temperature, and boiling temperature remain supported catalog options but are not included in the default property list.
