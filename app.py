
import json
import joblib
import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Risk Alert Classifier",
    page_icon="🛡️",
    layout="wide"
)
st.markdown("""
<style>
.stApp{background:linear-gradient(135deg,#f4f7fb 0%,#eef3f8 100%);color:#172033}.block-container{max-width:1200px;padding-top:2rem;padding-bottom:3rem}.hero{background:linear-gradient(135deg,#102a43,#1f4e79 55%,#2b6cb0);padding:2rem 2.2rem;border-radius:18px;margin-bottom:1.5rem;box-shadow:0 12px 30px rgba(16,42,67,.18);color:white}.hero h1{margin:0;font-size:2.25rem;font-weight:750}.hero p{margin:.55rem 0 0;color:#dbeafe;font-size:1rem}h2,h3{color:#102a43!important}div[data-testid="stForm"]{background:white;padding:1.4rem 1.5rem 1.2rem;border:1px solid #dbe5ef;border-radius:16px;box-shadow:0 8px 24px rgba(31,78,121,.08)}div[data-baseweb="input"]>div,div[data-baseweb="select"]>div{border-radius:10px;border-color:#cbd8e6;background:#fbfdff}button[kind="primary"]{width:100%;min-height:48px;border-radius:10px;border:none;background:linear-gradient(90deg,#1f4e79,#2b6cb0);color:white;font-weight:700;font-size:1rem;box-shadow:0 7px 16px rgba(43,108,176,.25)}div[data-testid="stMetric"]{background:white;border:1px solid #dbe5ef;border-radius:14px;padding:1rem 1.2rem;box-shadow:0 7px 20px rgba(31,78,121,.07)}div[data-testid="stMetricLabel"]{color:#5b7083;font-weight:600}div[data-testid="stMetricValue"]{color:#102a43;font-weight:750}div[data-testid="stAlert"]{border-radius:12px}.footer-note{text-align:center;color:#718096;font-size:.82rem;margin-top:2rem}
</style>
""",unsafe_allow_html=True)


st.markdown("""
<div class="hero"><h1>🛡️ Risk Alert Classifier</h1><p>Enter customer details below to estimate the probability of High Risk.</p></div>
""", unsafe_allow_html=True)


MODEL_PATH = "Model/model.joblib"
SCHEMA_PATH = "Output/input_schema.json"

@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)

@st.cache_data
def load_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as file:
        return json.load(file)

try:
    model = load_model()
    schema = load_schema()
except Exception as error:
    st.error(f"Could not load model or schema: {error}")
    st.stop()

st.subheader("📋 Customer Information")

input_values = {}

with st.form("risk_prediction_form"):

    columns = st.columns(2)

    for index, (feature, config) in enumerate(schema.items()):

        with columns[index % 2]:

            if config["type"] == "numeric":

                min_value = float(config["min"])
                max_value = float(config["max"])
                default_value = float(config["default"])

                # Ensure valid input bounds
                if max_value <= min_value:
                    min_value = default_value - 1
                    max_value = default_value + 1

                default_value = min(
                    max(default_value, min_value),
                    max_value
                )

                input_values[feature] = st.number_input(
                    feature.replace("_", " ").title(),
                    min_value=min_value,
                    max_value=max_value,
                    value=default_value
                )

            else:
                choices = config.get("choices", [])

                if not choices:
                    choices = [config.get("default", "Unknown")]

                default = config.get("default", choices[0])

                if default not in choices:
                    choices.insert(0, default)

                input_values[feature] = st.selectbox(
                    feature.replace("_", " ").title(),
                    options=choices,
                    index=choices.index(default)
                )

    submitted = st.form_submit_button(
        "Predict Risk",
        type="primary"
    )

if submitted:

    input_df = pd.DataFrame(
        [input_values],
        columns=list(schema.keys())
    )

    try:
        probabilities = model.predict_proba(input_df)[0]
        high_risk_probability = float(probabilities[1])

        predicted_class = int(
            high_risk_probability >= 0.5
        )

        st.subheader("📊 Prediction Result")

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "High Risk Probability",
                f"{high_risk_probability:.2%}"
            )

        with col2:
            st.metric(
                "Low Risk Probability",
                f"{probabilities[0]:.2%}"
            )

        if predicted_class == 1:
            st.error("Predicted Risk Status: HIGH RISK")
        else:
            st.success("Predicted Risk Status: LOW RISK")

        st.caption(
            "This prediction uses a 0.5 probability threshold. "
            "Validate the model and threshold before making real "
            "credit or financial decisions."
        )

    except Exception as error:
        st.error(f"Prediction failed: {error}")

st.markdown("""<div class="footer-note">Risk Alert Classifier • Model-based prediction • Review predictions before making financial decisions.</div>""", unsafe_allow_html=True)
