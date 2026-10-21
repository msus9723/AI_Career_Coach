"""Streamlit UI for the AI Career Coach.

Paste a resume and a job description, click Analyze, and see the API's
response. This app holds no coaching logic. It only calls the FastAPI
backend over HTTP (POST /gap-analysis), like any other client would.

Settings come from environment variables:
    API_BASE_URL  where the FastAPI server is (default http://localhost:8000)
    API_KEY       sent as the X-API-Key header (default dev-key-change-me)

Run locally:   streamlit run ui/app.py
Run in Docker: docker compose up   (see docker-compose.yml)
"""

import os

import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
API_KEY = os.getenv("API_KEY", "dev-key-change-me")

# The API answers in milliseconds today; the generous timeout leaves room
# for the LLM + RAG calls coming in later weeks.
REQUEST_TIMEOUT_SECONDS = 60


def api_is_up() -> bool:
    """True if GET /health answers. Used for the status dot in the sidebar."""
    try:
        return requests.get(f"{API_BASE_URL}/health", timeout=3).ok
    except requests.RequestException:
        return False


def call_gap_analysis(resume: str, job_description: str, user_id: str | None) -> requests.Response:
    return requests.post(
        f"{API_BASE_URL}/gap-analysis",
        headers={"X-API-Key": API_KEY},
        json={
            "resume_text": resume,
            "job_description_text": job_description,
            "user_id": user_id or None,
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )


def show_error(response: requests.Response) -> None:
    """Turn the API's HTTP status codes into messages a person can act on."""
    try:
        detail = response.json().get("detail")
    except ValueError:
        detail = response.text

    if response.status_code == 401:
        st.error("The API rejected the API key. Check API_KEY matches one of the API's API_KEYS.")
    elif response.status_code == 422:
        st.error("The API couldn't accept the input. Make sure both boxes have text.")
    elif response.status_code == 429:
        # Two different 429s: our daily quota (dict detail) or the
        # per-minute rate limit from slowapi (string detail).
        if isinstance(detail, dict) and "limit" in detail:
            st.warning(
                f"Daily quota reached ({detail['used']}/{detail['limit']} requests today). "
                "It resets at midnight UTC."
            )
        else:
            st.warning("Too many requests in a short time. Wait a minute and try again.")
    else:
        st.error(f"The API returned an error ({response.status_code}).")

    with st.expander("Error details"):
        st.json(detail if detail is not None else {})


st.set_page_config(page_title="AI Career Coach", layout="wide")

with st.sidebar:
    st.header("Settings")
    user_id = st.text_input(
        "User ID",
        value="meera",
        help="Used for the per-user daily quota. Leave empty to share the anonymous quota.",
    )
    st.caption(f"API: `{API_BASE_URL}`")
    if api_is_up():
        st.success("API is running")
    else:
        st.error("API is not reachable. Start it with `uvicorn app.main:app`.")

st.title("AI Career Coach")
st.write("Paste your resume and a job description to see how well they match.")

# A form sends both text boxes together when Analyze is pressed. Without it,
# Streamlit re-runs the whole script every time a box loses focus.
with st.form("gap_analysis_form"):
    resume_col, jd_col = st.columns(2)
    with resume_col:
        resume_text = st.text_area("Resume", height=320, placeholder="Paste your resume here…")
    with jd_col:
        jd_text = st.text_area(
            "Job description", height=320, placeholder="Paste the job description here…"
        )
    submitted = st.form_submit_button("Analyze", type="primary")

if submitted:
    if not resume_text.strip() or not jd_text.strip():
        st.warning("Please fill in both the resume and the job description.")
        st.stop()

    with st.spinner("Analyzing…"):
        try:
            response = call_gap_analysis(resume_text, jd_text, user_id.strip())
        except requests.ConnectionError:
            st.error(f"Couldn't connect to the API at {API_BASE_URL}. Is it running?")
            st.stop()
        except requests.Timeout:
            st.error("The API took too long to answer. Try again.")
            st.stop()

    if not response.ok:
        show_error(response)
        st.stop()

    result = response.json()

    if result.get("status") == "placeholder":
        st.info("This is placeholder output. Real analysis arrives once RAG + the LLM are wired in.")

    st.subheader("Gap analysis")
    st.write(result.get("gap_analysis") or "—")

    skills_col, recs_col = st.columns(2)
    with skills_col:
        st.subheader("Missing skills")
        for skill in result.get("missing_skills") or ["None yet"]:
            st.markdown(f"- {skill}")
    with recs_col:
        st.subheader("Recommendations")
        for rec in result.get("recommendations") or ["None yet"]:
            st.markdown(f"- {rec}")

    # The same id is in the API's logs, telemetry, and the interactions table.
    st.caption(f"Request ID: `{result.get('request_id')}`")
    with st.expander("Raw API response"):
        st.json(result)
