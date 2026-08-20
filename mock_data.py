# Fake data used only when MOCK_AI=true in .env — lets us test the
# app's structure (uploads, API responses, frontend) without making
# real API calls or burning rate-limited quota.

MOCK_BIOMARKERS = {
    "Total Leukocyte Count": 13.8,
    "RBC Count": 4.85,
    "Hemoglobin": 10.6,
    "Hematocrit": 38.2,
    "MCV": 84.1,
    "MCH": 28.0,
    "MCHC": 33.1,
    "RDW-CV": 13.0,
    "Platelet Count": 128,
    "Neutrophils": 62,
    "Lymphocytes": 28,
    "Monocytes": 6,
    "Eosinophils": 3,
    "Basophils": 1,
    "Absolute Neutrophil Count": 4.1,
    "Absolute Lymphocyte Count": 1.85,
    "Absolute Monocyte Count": 0.45,
    "Absolute Eosinophil Count": 0.28,
    "Absolute Basophil Count": 0.03,
}

MOCK_ADVICE = """This is placeholder advice generated in MOCK_AI mode, for testing the
application's structure without calling a real AI model.

Your Hemoglobin and Hematocrit are slightly below the typical range, which can
sometimes relate to low iron levels. Your Total Leukocyte Count is slightly
elevated, which can be a normal response to minor stress or immune activity.
Your Platelet Count is slightly below range as well.

This is mock data only. Please consult a licensed doctor to interpret your
actual blood report and decide on any next steps."""
