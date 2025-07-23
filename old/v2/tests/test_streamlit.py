import time
from playwright.sync_api import sync_playwright

def test_streamlit_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:8501")

        # Vérifie que le titre apparaît
        assert "EDA Explorer" in page.content()

        # Upload de fichier
        page.set_input_files("input[type='file']", "data/uploads/test_sample.csv")
        time.sleep(2)  # attendre le traitement du fichier

        assert "Fichier chargé avec succès" in page.content()
        print("✅ Interface Streamlit testée avec succès.")

        browser.close()

if __name__ == "__main__":
    test_streamlit_ui()
