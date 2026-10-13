import streamlit as st

st.title("Railway Safety Dashboard Debug")
st.write("Checkpoint 1: Streamlit is rendering.")

try:
    import pandas as pd
    st.success("Checkpoint 2: pandas imported.")

    from alert_manager import get_events
    st.success("Checkpoint 3: alert_manager imported.")

    events = get_events(limit=5)
    st.success(f"Checkpoint 4: Database read succeeded. Events: {len(events)}")

except Exception as e:
    st.exception(e)
