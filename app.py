import json
from pathlib import Path

import pandas as pd
import streamlit as st

from alert_manager import add_event, clear_events, get_events, process_event_payload

st.set_page_config(
    page_title="Railway Safety Monitor",
    page_icon="🚆",
    layout="wide",
)

st.title("🚆 Railway Platform Safety Monitor")
st.caption("Person 3 — Alerts, User Interface and Incident Management")

st.sidebar.header("Navigation")
page = st.sidebar.radio(
    "Choose a page",
    ["Dashboard", "Test Alerts", "Integration", "Incident History"],
)

st.sidebar.info(
    "Real detection alerts require integration with the team's models."
)

SAMPLES = {
    "Safety-line crossing": {
        "event_type": "SAFETY_LINE_CROSSING",
        "severity": "WARNING",
        "message": "Person may have crossed the safety boundary.",
        "object_id": "test-person-1",
        "source": "test_mode",
    },
    "Person on track": {
        "event_type": "PERSON_ON_TRACK",
        "severity": "DANGER",
        "message": "Potential person-on-track incident.",
        "object_id": "test-person-2",
        "source": "test_mode",
    },
    "Obstacle detected": {
        "event_type": "OBSTACLE_DETECTED",
        "severity": "WARNING",
        "message": "Potential obstacle in a restricted area.",
        "object_id": "test-obstacle-1",
        "source": "test_mode",
    },
    "Person detected": {
        "event_type": "PERSON_DETECTED",
        "severity": "INFO",
        "message": "Person detected; no risk assessment supplied.",
        "object_id": "test-person-3",
        "source": "test_mode",
    },
    "System normal": {
        "event_type": "SYSTEM_NORMAL",
        "severity": "INFO",
        "message": "No violation reported by this test event.",
        "object_id": "test-system",
        "source": "test_mode",
    },
}


def show_event(event):
    severity = event["severity"]
    message = f"{event['event_type']}\n\n{event['message']}"

    if severity == "DANGER":
        st.error("🚨 " + message)
    elif severity == "WARNING":
        st.warning("⚠️ " + message)
    else:
        st.info("ℹ️ " + message)


if page == "Dashboard":
    events = get_events(limit=500)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Recorded incidents", len(events))
    c2.metric("Danger events", sum(e["severity"] == "DANGER" for e in events))
    c3.metric("Warnings", sum(e["severity"] == "WARNING" for e in events))
    c4.metric("System status", "Events received" if events else "Waiting")

    st.divider()
    left, right = st.columns([3, 2])

    with left:
        st.subheader("📹 Image / Video Viewer")
        uploaded = st.file_uploader(
            "Upload media for preview",
            type=["jpg", "jpeg", "png", "mp4", "mov", "avi"],
        )

        if uploaded:
            extension = Path(uploaded.name).suffix.lower()
            if extension in [".jpg", ".jpeg", ".png"]:
                st.image(uploaded, use_container_width=True)
            else:
                st.video(uploaded)
            st.caption("Preview only; uploading media does not run detection.")
        else:
            st.info("Upload an image or video to preview it.")

    with right:
        st.subheader("🚨 Latest Alert")
        if events:
            show_event(events[0])
            st.caption(f"Time: {events[0]['timestamp']}")
            st.caption(f"Source: {events[0]['source']}")
        else:
            st.info("No events have been received.")

        st.subheader("Alert Severity")
        st.markdown(
            "- 🔴 **DANGER:** Potential person-on-track incident\n"
            "- 🟠 **WARNING:** Potential boundary violation or obstacle\n"
            "- 🔵 **INFO:** Informational event"
        )

    st.divider()
    st.subheader("Recent Incidents")
    if events:
        st.dataframe(pd.DataFrame(events), use_container_width=True, hide_index=True)
    else:
        st.write("Incident history is empty.")

elif page == "Test Alerts":
    st.subheader("Test Alert Generation")
    st.warning("These are simulated events, not real detections.")

    selected = st.selectbox("Choose an event", list(SAMPLES.keys()))

    if st.button("Generate Sample Alert", type="primary"):
        inserted, message = add_event(SAMPLES[selected])
        if inserted:
            st.success("Event recorded successfully.")
        else:
            st.info(message)

    if st.button("Generate All Sample Alerts"):
        count = sum(add_event(sample)[0] for sample in SAMPLES.values())
        st.success(f"{count} new sample events recorded.")

    if st.button("Clear Incident History"):
        clear_events()
        st.success("Incident history cleared.")
        st.rerun()

elif page == "Integration":
    st.subheader("Integration with Person 1 and Person 2")
    st.write(
        "Submit a JSON event from the detection/tracking pipeline. "
        "Real detections must be connected by your team."
    )

    example = {
        "event_type": "PERSON_ON_TRACK",
        "severity": "DANGER",
        "message": "Person detected in restricted track area.",
        "timestamp": "2026-10-13T10:30:00",
        "object_id": "person-17",
        "source": "person2_tracking",
    }

    raw_json = st.text_area("Event JSON", value=json.dumps(example, indent=2), height=260)

    if st.button("Submit Integration Event", type="primary"):
        try:
            result = process_event_payload(json.loads(raw_json))
            st.success(
                f"Inserted: {result['inserted']} | "
                f"Duplicates suppressed: {result['duplicates']}"
            )
        except (json.JSONDecodeError, ValueError) as exc:
            st.error(f"Invalid event payload: {exc}")

elif page == "Incident History":
    st.subheader("Incident History and CSV Export")
    events = get_events(limit=5000)

    if events:
        df = pd.DataFrame(events)
        severities = st.multiselect(
            "Filter by severity",
            ["INFO", "WARNING", "DANGER"],
            default=["INFO", "WARNING", "DANGER"],
        )
        filtered = df[df["severity"].isin(severities)]

        st.dataframe(filtered, use_container_width=True, hide_index=True)
        st.download_button(
            "Download Incident History (CSV)",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="railway_incident_history.csv",
            mime="text/csv",
        )
        st.caption(f"{len(filtered)} events displayed.")

        if st.button("Delete All Incidents"):
            clear_events()
            st.success("All incidents deleted.")
            st.rerun()
    else:
        st.info("No incidents recorded yet.")

st.divider()
st.caption("Railway Safety Monitoring Prototype | Person 3: Alerts + UI")
