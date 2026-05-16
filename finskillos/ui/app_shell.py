def run_app() -> None:
    """Run the FinSkillOS Streamlit shell."""
    import streamlit as st

    st.set_page_config(page_title="FinSkillOS v2.1", layout="wide")
    st.title("FinSkillOS v2.1 Control Room")
    st.caption("Personal trading operating system rebuild.")

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("System Mode", "Setup")
    col_b.metric("Data Layer", "Pending")
    col_c.metric("Risk Firewall", "Ready")

    st.info("P1 skeleton is active. Implement each .devmd slice in numerical order.")
