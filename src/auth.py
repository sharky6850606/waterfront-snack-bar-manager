"""Small, fail-closed password gate backed by Streamlit Secrets."""
import hmac
import time

import streamlit as st

from .config import LOGO_PATH

MAX_ATTEMPTS = 5
LOCK_SECONDS = 30


def credentials_match(username, password, expected_username, expected_password):
    """Compare credentials without early-exit string comparisons."""
    if not all(isinstance(value, str) and value for value in (username, password, expected_username, expected_password)):
        return False
    username_ok = hmac.compare_digest(username.casefold(), expected_username.casefold())
    password_ok = hmac.compare_digest(password, expected_password)
    return username_ok and password_ok


def _configured_credentials():
    return str(st.secrets.get("APP_USERNAME", "")), str(st.secrets.get("APP_PASSWORD", ""))


def require_login():
    """Render the login page and stop execution until this browser session is authenticated."""
    if st.session_state.get("authenticated"):
        return

    st.markdown("""<style>
    [data-testid="stSidebar"], [data-testid="collapsedControl"]{display:none!important}
    .block-container{max-width:720px!important;padding-top:4.5rem!important}
    .wf-login-title{text-align:center;margin-bottom:1.3rem}
    .wf-login-title h1{font-size:2.35rem;margin:.7rem 0 .25rem;letter-spacing:-.045em}
    .wf-login-title p{color:#6B6863;margin:0}
    </style>""", unsafe_allow_html=True)

    if LOGO_PATH.exists():
        left, logo, right = st.columns([2, 1, 2])
        logo.image(str(LOGO_PATH), width=125)
    st.markdown('<div class="wf-login-title"><h1>Waterfront Snack Bar</h1><p>Financial Manager · Secure access</p></div>', unsafe_allow_html=True)

    expected_username, expected_password = _configured_credentials()
    if not expected_username or not expected_password:
        st.error("Login has not been configured. Add APP_USERNAME and APP_PASSWORD to Streamlit Secrets, then restart the app.")
        st.stop()

    locked_until = float(st.session_state.get("login_locked_until", 0))
    remaining = max(0, int(locked_until - time.time() + 0.999))
    if st.session_state.pop("login_failed", False):
        st.error("The username or password is incorrect.")
    if remaining:
        st.warning(f"Too many unsuccessful attempts. Wait {remaining} seconds, then refresh this page.")

    with st.container(border=True):
        st.markdown("### Sign in")
        st.caption("Enter the private credentials provided by the app owner.")
        with st.form("login_form", clear_on_submit=True):
            username = st.text_input("Username", autocomplete="username")
            password = st.text_input("Password", type="password", autocomplete="current-password")
            submitted = st.form_submit_button("Sign in", type="primary", width="stretch", disabled=bool(remaining))

    if submitted:
        if credentials_match(username, password, expected_username, expected_password):
            st.session_state["authenticated"] = True
            st.session_state.pop("login_attempts", None)
            st.session_state.pop("login_locked_until", None)
            st.rerun()
        attempts = int(st.session_state.get("login_attempts", 0)) + 1
        if attempts >= MAX_ATTEMPTS:
            st.session_state["login_attempts"] = 0
            st.session_state["login_locked_until"] = time.time() + LOCK_SECONDS
        else:
            st.session_state["login_attempts"] = attempts
        st.session_state["login_failed"] = True
        st.rerun()

    st.caption("Your password is checked only against the value stored in Streamlit Secrets.")
    st.stop()


def logout():
    """End the authenticated browser session and clear page state."""
    for key in list(st.session_state):
        del st.session_state[key]
    st.rerun()
