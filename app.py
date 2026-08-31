import io
import os
from pathlib import Path

import numpy as np
import pandas as pd
from flask import Flask, flash, jsonify, redirect, render_template, request, send_file, url_for
from thermo import Chemical


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "fluids.csv"
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "local-development-key-change-before-deploying")

PROPERTY_MAP = {
    "Molar Heat Capacity (J/mol/K)": "Cpm",
    "Molar Enthalpy (J/mol)": "Hm",
    "Molar Entropy (J/mol/K)": "Sm",
    "Molar Gibbs Energy (J/mol)": "Gm",
    "Heat Capacity (J/kg/K)": "Cp",
    "Enthalpy (J/kg)": "H",
    "Entropy (J/kg/K)": "S",
    "Gibbs Energy (J/kg)": "G",
    "Molecular Weight (g/mol)": "MW",
    "Melting Temperature (K)": "Tm",
    "Boiling Temperature (K)": "Tb",
    "Dielectric Constant / Relative Permittivity (Dimensionless)": "permittivity",
    "Absolute Permittivity (F/m)": "absolute_permittivity",
    "Density (kg/m^3)": "rho",
    "Molar Density (mol/m^3)": "rhom",
    "Viscosity (Pa*s)": "mu",
    "Thermal Conductivity (W/m/K)": "k",
    "Vapor Pressure (Pa)": "Psat",
}

ADDITIONAL_PROPERTY_MAP = {
    "Surface Tension (N/m)": "sigma",
    "Prandtl Number (Dimensionless)": "Pr",
    "Thermal Diffusivity (m^2/s)": "alpha",
    "Kinematic Viscosity (m^2/s)": "nu",
    "Compressibility Factor (Dimensionless)": "Z",
    "Liquid Molar Volume (m^3/mol)": "Vml",
    "Heat of Vaporization (J/kg)": "Hvap",
}

SUPPORTED_PROPERTY_MAP = {**PROPERTY_MAP, **ADDITIONAL_PROPERTY_MAP}


def load_fluids():
    """Load the immutable default list. Browser customizations never write here."""
    return pd.read_csv(DATABASE_PATH, dtype={"cas_number": str}).sort_values(
        "name", key=lambda values: values.str.lower()
    )


def safe_property(chemical, attribute):
    try:
        value = getattr(chemical, attribute)
        if value is None or not np.isfinite(float(value)):
            return None
        return float(value)
    except (AttributeError, TypeError, ValueError, OverflowError):
        return None


def is_liquid(chemical):
    try:
        return str(chemical.phase).lower().strip() in {"l", "liquid"}
    except Exception:
        return False


def calculate(fluid_rows, temperatures, pressure, properties, liquid_only):
    rows = []
    warnings = []

    for fluid in fluid_rows:
        points_found = 0
        for temperature in temperatures:
            try:
                chemical = Chemical(fluid.cas_number, T=float(temperature), P=pressure)
                if liquid_only and not is_liquid(chemical):
                    continue

                row = {
                    "Fluid": fluid.name,
                    "Temperature (K)": float(temperature),
                    "Pressure (Pa)": pressure,
                }
                for label in properties:
                    row[label] = safe_property(chemical, SUPPORTED_PROPERTY_MAP[label])
                rows.append(row)
                points_found += 1
            except Exception as exc:
                warnings.append(f"{fluid.name} at {temperature:.2f} K could not be calculated: {exc}")

        if points_found == 0:
            warnings.append(f"No liquid-state points were found for {fluid.name} in the selected range.")

    return pd.DataFrame(rows), warnings


def parse_form(form, fluids):
    mode = form.get("mode", "range")
    unit = form.get("unit", "K")
    selected_cas = form.getlist("fluids")
    selected_labels = form.getlist("fluid_labels")
    properties = form.getlist("properties")

    if mode not in {"range", "single"}:
        raise ValueError("Choose a valid calculation mode.")
    if unit not in {"K", "C"}:
        raise ValueError("Choose Kelvin or Celsius.")
    if not selected_cas:
        raise ValueError("Select at least one fluid.")
    if len(selected_cas) > 10:
        raise ValueError("Select no more than 10 fluids at a time.")
    if not properties or any(item not in SUPPORTED_PROPERTY_MAP for item in properties):
        raise ValueError("Select at least one valid property.")
    if len(properties) > 20:
        raise ValueError("Select no more than 20 properties at a time.")

    pressure = float(form.get("pressure", ""))
    start = float(form.get("start_temperature", ""))
    if not np.isfinite(pressure) or pressure <= 0:
        raise ValueError("Pressure must be a positive number.")
    if unit == "C":
        start += 273.15
    if not np.isfinite(start) or start < 0:
        raise ValueError("Temperature cannot be below absolute zero.")

    if mode == "single":
        temperatures = np.array([start])
        liquid_only = False
    else:
        end = float(form.get("end_temperature", ""))
        points = int(form.get("points", ""))
        if unit == "C":
            end += 273.15
        if not np.isfinite(end) or end < 0:
            raise ValueError("End temperature cannot be below absolute zero.")
        if end <= start:
            raise ValueError("End temperature must be greater than start temperature.")
        if not 2 <= points <= 100:
            raise ValueError("Number of points must be between 2 and 100.")
        temperatures = np.linspace(start, end, points)
        liquid_only = True

    defaults = {str(row.cas_number): row for row in fluids.itertuples(index=False)}
    fluid_records = []
    for index, cas_number in enumerate(selected_cas):
        cas_number = str(cas_number).strip()
        if cas_number in defaults:
            record = defaults[cas_number]._asdict()
        else:
            try:
                chemical = Chemical(cas_number)
            except Exception as exc:
                raise ValueError(f"The custom fluid {cas_number} is not valid.") from exc
            record = {
                "formula": chemical.formula,
                "name": chemical.ID or cas_number,
                "cas_number": str(chemical.CAS),
                "molecular_weight": safe_property(chemical, "MW"),
                "melting_temp_K": safe_property(chemical, "Tm"),
                "boiling_temp_K": safe_property(chemical, "Tb"),
            }
        if index < len(selected_labels) and selected_labels[index].strip():
            record["name"] = selected_labels[index].strip()[:100]
        fluid_records.append(record)

    fluid_rows = pd.DataFrame(fluid_records)

    return mode, unit, fluid_rows.itertuples(index=False), temperatures, pressure, properties, liquid_only


def display_results(results, unit):
    displayed = results.copy()
    temperature_label = "Temperature (K)"
    if unit == "C":
        displayed["Temperature (°C)"] = displayed["Temperature (K)"] - 273.15
        displayed = displayed.drop(columns="Temperature (K)")
        columns = list(displayed.columns)
        columns.insert(1, columns.pop(columns.index("Temperature (°C)")))
        displayed = displayed[columns]
        temperature_label = "Temperature (°C)"

    displayed = displayed.round(5)
    return displayed, temperature_label


def make_chart_data(displayed, temperature_label, properties):
    charts = []
    if len(displayed) < 2:
        return charts

    for prop in properties:
        traces = []
        for fluid_name, group in displayed.groupby("Fluid"):
            valid = group[[temperature_label, prop]].dropna()
            if len(valid) >= 2:
                traces.append({
                    "name": fluid_name,
                    "x": valid[temperature_label].tolist(),
                    "y": valid[prop].tolist(),
                })
        if traces:
            charts.append({"property": prop, "temperature_label": temperature_label, "traces": traces})
    return charts


@app.route("/", methods=["GET", "POST"])
def index():
    fluids = load_fluids()
    context = {
        "fluids": fluids.to_dict("records"),
        "properties": list(PROPERTY_MAP),
        "property_catalog": [
            {"label": label, "is_default": label in PROPERTY_MAP}
            for label in SUPPORTED_PROPERTY_MAP
        ],
        "form": request.form,
        "results": None,
        "charts": [],
        "warnings": [],
        "error": None,
    }

    if request.method == "POST":
        try:
            parsed = parse_form(request.form, fluids)
            mode, unit, fluid_rows, temperatures, pressure, properties, liquid_only = parsed
            results, warnings = calculate(
                fluid_rows, temperatures, pressure, properties, liquid_only
            )
            if results.empty:
                raise ValueError("No results were available for these inputs. Try a different temperature range.")
            displayed, temperature_label = display_results(results, unit)
            context["results"] = displayed.to_dict("records")
            context["columns"] = displayed.columns.tolist()
            context["charts"] = make_chart_data(displayed, temperature_label, properties) if mode == "range" else []
            context["warnings"] = warnings
        except (ValueError, TypeError) as exc:
            context["error"] = str(exc)
        except Exception:
            app.logger.exception("Unexpected calculation error")
            context["error"] = "The calculation could not be completed. Please check the inputs and try again."

    return render_template("index.html", **context)


@app.post("/api/fluids/validate")
def validate_fluid():
    data = request.get_json(silent=True) or {}
    identifier = str(data.get("identifier", "")).strip()
    display_name = str(data.get("name", "")).strip()
    if not identifier:
        return jsonify(error="Enter a chemical name or CAS number."), 400
    if len(identifier) > 100 or len(display_name) > 100:
        return jsonify(error="Fluid names and identifiers must be 100 characters or fewer."), 400
    try:
        chemical = Chemical(identifier)
        return jsonify({
            "formula": chemical.formula,
            "name": (display_name or chemical.ID or identifier)[:100],
            "cas_number": str(chemical.CAS),
            "molecular_weight": safe_property(chemical, "MW"),
            "melting_temp_K": safe_property(chemical, "Tm"),
            "boiling_temp_K": safe_property(chemical, "Tb"),
        })
    except Exception:
        return jsonify(error="That chemical could not be found. Try a valid name or CAS number."), 400


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/export")
def export_results():
    try:
        fluids = load_fluids()
        mode, unit, fluid_rows, temperatures, pressure, properties, liquid_only = parse_form(request.form, fluids)
        results, _ = calculate(fluid_rows, temperatures, pressure, properties, liquid_only)
        if results.empty:
            raise ValueError("No results are available to export.")
        displayed, _ = display_results(results, unit)
        output = io.BytesIO(displayed.to_csv(index=False).encode("utf-8"))
        return send_file(output, mimetype="text/csv", as_attachment=True, download_name="thermodynamic-results.csv")
    except (ValueError, TypeError) as exc:
        flash(str(exc), "error")
        return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
