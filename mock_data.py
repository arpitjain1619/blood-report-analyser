# Fake data used only when MOCK_AI=true — lets us test the app's structure
# (detection, categorization, response shape) without real API calls.
# Each report type owns its biomarkers AND its advice together.

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
        "advice": """This is placeholder advice generated in MOCK_AI mode, for testing the
application's structure without calling a real AI model.

Your Hemoglobin and Hematocrit are slightly below the typical range, which can
sometimes relate to low iron levels. Your Total Leukocyte Count is slightly
elevated, which can be a normal response to minor stress or immune activity.
Your Platelet Count is slightly below range as well.

This is mock data only. Please consult a licensed doctor to interpret your
actual blood report and decide on any next steps.""",
    },

    "diabetes": {
        "biomarkers": {
            "HbA1c": {"value": 6.1, "unit": "%", "printed_range": "<5.7"},
            "Fasting Blood Glucose": {"value": 118, "unit": "mg/dL", "printed_range": "70-100"},
        },
        "advice": """This is placeholder advice generated in MOCK_AI mode, for testing the
application's structure without calling a real AI model.

Your HbA1c and fasting glucose are in a range sometimes described as prediabetes,
which can relate to how your body is managing blood sugar over time.

This is mock data only. Please consult a licensed doctor to interpret your
actual report and decide on any next steps.""",
    },

    "lipid": {
        "biomarkers": {
            "Total Cholesterol": {"value": 225, "unit": "mg/dL", "printed_range": "<200"},
            "LDL": {"value": 145, "unit": "mg/dL", "printed_range": "<100"},
            "HDL": {"value": 35, "unit": "mg/dL", "printed_range": ">40"},
            "Triglycerides": {"value": 180, "unit": "mg/dL", "printed_range": "<150"},
        },
        "advice": """This is placeholder advice generated in MOCK_AI mode, for testing the
application's structure without calling a real AI model.

Several of your cholesterol values, including LDL and triglycerides, are above the
desirable range, and your HDL is on the lower side.

This is mock data only. Please consult a licensed doctor to interpret your
actual report and decide on any next steps.""",
    },

    "thyroid": {
        "biomarkers": {
            "TSH": {"value": 6.2, "unit": "mIU/L", "printed_range": "0.4-4.0"},
            "Free T4": {"value": 1.1, "unit": "ng/dL", "printed_range": "0.8-1.8"},
            "Free T3": {"value": 3.0, "unit": "pg/mL", "printed_range": "2.3-4.2"},
        },
        "advice": """This is placeholder advice generated in MOCK_AI mode, for testing the
application's structure without calling a real AI model.

Your TSH is above the typical range while your T4 and T3 are within range, a
pattern sometimes associated with thyroid function.

This is mock data only. Please consult a licensed doctor to interpret your
actual report and decide on any next steps.""",
    },

    "vitamins": {
        "biomarkers": {
            "Vitamin D": {"value": 18, "unit": "ng/mL", "printed_range": ">30"},
            "Vitamin B12": {"value": 350, "unit": "pg/mL", "printed_range": "200-900"},
        },
        "advice": """This is placeholder advice generated in MOCK_AI mode, for testing the
application's structure without calling a real AI model.

Your Vitamin D is below the typical range, while your Vitamin B12 is within range.

This is mock data only. Please consult a licensed doctor to interpret your
actual report and decide on any next steps.""",
    },
}


def _get_mock_report(report_key: str = "blood") -> dict:
    """Return the mock report (biomarkers + advice) for a type, defaulting to blood."""
    return MOCK_REPORTS.get(report_key, MOCK_REPORTS["blood"])


def get_mock_biomarkers(report_key: str = "blood") -> dict:
    return _get_mock_report(report_key)["biomarkers"]


def get_mock_advice(report_key: str = "blood") -> str:
    return _get_mock_report(report_key)["advice"]