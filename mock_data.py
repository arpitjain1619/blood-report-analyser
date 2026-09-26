# Fake data used only when MOCK_AI=true in .env — lets us test the
# app's structure (uploads, API responses, frontend) without making
# real API calls or burning rate-limited quota.

MOCK_BIOMARKERS = {
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
}

MOCK_ADVICE = """This is placeholder advice generated in MOCK_AI mode, for testing the
application's structure without calling a real AI model.

Your Hemoglobin and Hematocrit are slightly below the typical range, which can
sometimes relate to low iron levels. Your Total Leukocyte Count is slightly
elevated, which can be a normal response to minor stress or immune activity.
Your Platelet Count is slightly below range as well.

This is mock data only. Please consult a licensed doctor to interpret your
actual blood report and decide on any next steps."""
