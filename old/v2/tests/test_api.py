import requests

API_URL = "http://localhost:8000"

def test_upload():
    with open("data/uploads/test_sample.csv", "rb") as f:
        files = {"file": ("test_sample.csv", f, "text/csv")}
        r = requests.post(f"{API_URL}/upload/", files=files)
        assert r.status_code == 200
        print("✅ Upload OK")

def test_all_endpoints():
    endpoints = [
        ("GET", "/head?n=5"),
        ("GET", "/missing-values/"),
        ("GET", "/describe/"),
        ("GET", "/duplicates/"),
        ("POST", "/drop-duplicates/"),
        ("POST", "/drop-columns/", {"columns": ["ghg_emissions_total"]}),
        ("GET", "/export/"),
        ("GET", "/report/")
    ]
    for method, endpoint, *payload in endpoints:
        if method == "GET":
            r = requests.get(f"{API_URL}{endpoint}")
        elif method == "POST":
            r = requests.post(f"{API_URL}{endpoint}", json=payload[0])
        assert r.status_code in [200, 400]
        print(f"✅ {endpoint} OK")

if __name__ == "__main__":
    test_upload()
    test_all_endpoints()
    print("\nTous les tests API ont été exécutés avec succès.")
