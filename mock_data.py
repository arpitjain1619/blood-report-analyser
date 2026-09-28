# Fake data used only when MOCK_AI=true — lets us test the app's structure
# (detection, categorization, response shape) without real API calls.
# Each report type owns its biomarkers AND its advice together.
# Advice mirrors the real structured shape: {summary, findings: [{name, advice}]}.

MOCK_REPORTS = {
    "blood": {
        "biomarkers": {
            "Total Leukocyte Count": {"value": 13.8, "unit": "x10^3/uL", "printed_range": "4.0-11.0"},
            "RBC Count": {"value": 4.85, "unit": "million/uL", "printed_range": "4.2-5.9"},
            "Hemoglobin": {"value": 10.6, "unit": "g/dL", "printed_range": "13.0-17.0"},
            "Hematocrit": {"value": 38.2, "unit": "%", "printed_range": "40.0-50.0"},
            "MCV": {"value": 84.1, "unit": "fL", "printed_range": "80.0-100.0"},
            "MCH": {"value": 28.0, "unit": "pg", "printed_range": "27.0-33.0"},
            "MCHC": {"value": 33.1, "unit": "g/dL", "printed_range": "32.0-36.0"},
            "RDW-CV": {"value": 13.0, "unit": "%", "printed_range": "11.5-14.5"},
            "Platelet Count": {"value": 128, "unit": "x10^3/uL", "printed_range": "150-450"},
            "Neutrophils": {"value": 62, "unit": "%", "printed_range": "40-70"},
            "Lymphocytes": {"value": 28, "unit": "%", "printed_range": "20-45"},
            "Monocytes": {"value": 6, "unit": "%", "printed_range": "2-10"},
            "Eosinophils": {"value": 3, "unit": "%", "printed_range": "1-6"},
            "Basophils": {"value": 1, "unit": "%", "printed_range": "0-2"},
            "Absolute Neutrophil Count": {"value": 4.1, "unit": "x10^3/uL", "printed_range": None},
            "Absolute Lymphocyte Count": {"value": 1.85, "unit": "x10^3/uL", "printed_range": None},
            "Absolute Monocyte Count": {"value": 0.45, "unit": "x10^3/uL", "printed_range": ""},
            "Absolute Eosinophil Count": {"value": 0.28, "unit": "x10^3/uL", "printed_range": ""},
            "Absolute Basophil Count": {"value": 0.03, "unit": "x10^3/uL", "printed_range": ""},
        },
        "advice": {
            "summary": "This is placeholder advice generated in MOCK_AI mode for testing structure without a real AI call. A few values are outside the typical range. Please consult a licensed doctor to interpret your actual report and decide on any next steps.",
            "findings": [
                {"name": "Hemoglobin", "advice": "Your hemoglobin is slightly below the typical range, which can sometimes relate to low iron levels."},
                {"name": "Hematocrit", "advice": "Your hematocrit is slightly below range and often moves together with hemoglobin."},
                {"name": "Total Leukocyte Count", "advice": "Your white blood cell count is slightly elevated, which can be a normal response to minor stress or immune activity."},
                {"name": "Platelet Count", "advice": "Your platelet count is slightly below the typical range."},
            ],
        },
    },

    "diabetes": {
        "biomarkers": {
            "HbA1c": {"value": 6.1, "unit": "%", "printed_range": "<5.7"},
            "Fasting Blood Glucose": {"value": 118, "unit": "mg/dL", "printed_range": "70-100"},
        },
        "advice": {
            "summary": "This is placeholder advice generated in MOCK_AI mode for testing structure without a real AI call. Please consult a licensed doctor to interpret your actual report and decide on any next steps.",
            "findings": [
                {"name": "HbA1c", "advice": "Your HbA1c is in a range sometimes described as prediabetes, reflecting average blood sugar over recent months."},
                {"name": "Fasting Blood Glucose", "advice": "Your fasting glucose is in a range sometimes described as prediabetes."},
            ],
        },
    },

    "lipid": {
        "biomarkers": {
            "Total Cholesterol": {"value": 225, "unit": "mg/dL", "printed_range": "<200"},
            "LDL": {"value": 145, "unit": "mg/dL", "printed_range": "<100"},
            "HDL": {"value": 35, "unit": "mg/dL", "printed_range": ">40"},
            "Triglycerides": {"value": 180, "unit": "mg/dL", "printed_range": "<150"},
        },
        "advice": {
            "summary": "This is placeholder advice generated in MOCK_AI mode for testing structure without a real AI call. Please consult a licensed doctor to interpret your actual report and decide on any next steps.",
            "findings": [
                {"name": "Total Cholesterol", "advice": "Your total cholesterol is above the desirable range; the breakdown into LDL and HDL matters for interpreting it."},
                {"name": "LDL", "advice": "Your LDL is above the optimal range and is generally considered a long-term cardiovascular consideration."},
                {"name": "HDL", "advice": "Your HDL is on the lower side; for HDL, higher is generally considered more favorable."},
                {"name": "Triglycerides", "advice": "Your triglycerides are above the normal range, which is often influenced by diet and activity."},
            ],
        },
    },

    "thyroid": {
        "biomarkers": {
            "TSH": {"value": 6.2, "unit": "mIU/L", "printed_range": "0.4-4.0"},
            "Free T4": {"value": 1.1, "unit": "ng/dL", "printed_range": "0.8-1.8"},
            "Free T3": {"value": 3.0, "unit": "pg/mL", "printed_range": "2.3-4.2"},
        },
        "advice": {
            "summary": "This is placeholder advice generated in MOCK_AI mode for testing structure without a real AI call. Please consult a licensed doctor to interpret your actual report and decide on any next steps.",
            "findings": [
                {"name": "TSH", "advice": "Your TSH is above the typical range, a pattern sometimes associated with an underactive thyroid; it is usually interpreted alongside T3 and T4."},
            ],
        },
    },

    "vitamins": {
        "biomarkers": {
            "Vitamin D": {"value": 18, "unit": "ng/mL", "printed_range": ">30"},
            "Vitamin B12": {"value": 350, "unit": "pg/mL", "printed_range": "200-900"},
        },
        "advice": {
            "summary": "This is placeholder advice generated in MOCK_AI mode for testing structure without a real AI call. Please consult a licensed doctor to interpret your actual report and decide on any next steps.",
            "findings": [
                {"name": "Vitamin D", "advice": "Your Vitamin D is below the typical range, which is common and often addressed through sun exposure, diet, or supplementation."},
            ],
        },
    },
}


def _get_mock_report(report_key: str = "blood") -> dict:
    """Return the mock report (biomarkers + advice) for a type, defaulting to blood."""
    return MOCK_REPORTS.get(report_key, MOCK_REPORTS["blood"])


def get_mock_biomarkers(report_key: str = "blood") -> dict:
    return _get_mock_report(report_key)["biomarkers"]


def get_mock_advice(report_key: str = "blood") -> dict:
    return _get_mock_report(report_key)["advice"]