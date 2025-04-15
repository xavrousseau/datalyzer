# sections/export.py

import streamlit as st


def run_export():
    st.subheader("💾 Export du fichier final")
    df = st.session_state.get("df")

    if df is None:
        st.warning("❌ Aucune donnée disponible pour l’export.")
        return

    selected_name = st.session_state.get("global_df_selector", "dataframe")
    st.markdown(f"🔎 **Fichier sélectionné : `{selected_name}`**")

    with st.form("export_form"):
        file_name = st.text_input("Nom du fichier CSV", value="cleaned_data.csv")
        submit = st.form_submit_button("📥 Télécharger")

        if submit:
            csv_data = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Télécharger le CSV",
                csv_data,
                file_name,
                mime="text/csv"
            )
