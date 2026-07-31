import os
import pickle
import logging

import numpy as np
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

# ---------------------------------------------------------------
# Logging (App Runner / most platforms capture stdout automatically)
# ---------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("heart-disease-app")

app = Flask(__name__)
CORS(app)  # allow other origins to call /api/predict — tighten with origins=[...] if needed

# ---------------------------------------------------------------
# Load model and column names once at startup
# ---------------------------------------------------------------
MODEL_PATH = os.path.join(os.path.dirname(__file__), "Heart_Disease_model.pkl")
COLUMNS_PATH = os.path.join(os.path.dirname(__file__), "Heart_Disease_columns.pkl")

try:
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    with open(COLUMNS_PATH, "rb") as f:
        columns = pickle.load(f)
    logger.info("Model and columns loaded successfully. Features: %s", columns)
except Exception:
    logger.exception("Failed to load model/columns at startup")
    raise


def build_input_array(source):
    """Validate + convert a dict-like source into a model-ready array.
    Returns (array, error_message). error_message is None on success."""
    input_data = []
    for col in columns:
        value = source.get(col)
        if value is None or value == "":
            return None, f"Missing field: {col}"
        try:
            input_data.append(float(value))
        except (TypeError, ValueError):
            return None, f"Invalid value for field '{col}': must be a number"
    return np.array(input_data).reshape(1, -1), None


def run_prediction(input_array):
    prediction = int(model.predict(input_array)[0])
    probability = None
    if hasattr(model, "predict_proba"):
        probability = round(float(model.predict_proba(input_array)[0][1]) * 100, 2)
    return prediction, probability


# ---------------------------------------------------------------
# Health check — required by load balancers / App Runner
# ---------------------------------------------------------------
@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


# ---------------------------------------------------------------
# Page routes (HTML)
# ---------------------------------------------------------------
@app.route("/")
def landing():
    return render_template("index.html")


@app.route("/predict", methods=["GET"])
def predict_form():
    return render_template("form.html", columns=columns)


@app.route("/predict", methods=["POST"])
def predict():
    input_array, error = build_input_array(request.form)
    if error:
        logger.warning("Form validation failed: %s", error)
        return render_template("form.html", columns=columns, error=error), 400

    try:
        prediction, probability = run_prediction(input_array)
    except Exception:
        logger.exception("Prediction failed")
        return render_template(
            "form.html", columns=columns,
            error="Something went wrong while generating the prediction. Please try again."
        ), 500

    return render_template(
        "result.html",
        has_disease=bool(prediction == 1),
        probability=probability
    )


# ---------------------------------------------------------------
# REST API route (JSON)
# ---------------------------------------------------------------
@app.route("/api/predict", methods=["POST"])
def api_predict():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    input_array, error = build_input_array(data)
    if error:
        return jsonify({"error": error}), 400

    try:
        prediction, probability = run_prediction(input_array)
    except Exception:
        logger.exception("API prediction failed")
        return jsonify({"error": "Internal error while generating prediction"}), 500

    return jsonify({
        "prediction": prediction,
        "risk": "high" if prediction == 1 else "low",
        "confidence_percent": probability
    })


# ---------------------------------------------------------------
# Friendly error handlers (no raw tracebacks leaked to clients)
# ---------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(e):
    logger.exception("Unhandled server error")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
