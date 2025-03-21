# tests/test_api.py

import requests
import os

def test_eda_endpoint():
    file_path = os.path.join("data", "spotify_2023.csv")
    url = "http://127.0.0.1:8000/eda/"

    with open(file_path, "rb") as f:
        files = {"file": f}
        response = requests.post(url, files=files)

    assert response.status_code == 200, f"❌ Code retour inattendu : {response.status_code}"
    json_data = response.json()

    # Vérifications clés
    assert "overview" in json_data
    assert "numeric_stats" in json_data
    assert "correlation_matrix_base64" in json_data
    assert "missing_values_plot_base64" in json_data
    print("✅ Test API passé avec succès.")

if __name__ == "__main__":
    test_eda_endpoint()
