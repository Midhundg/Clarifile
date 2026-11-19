"""Authentication UI component for user login, registration, and session initialization."""

import streamlit as st
from services.auth_service import AuthService, User


def render_auth_page(auth_service: AuthService) -> None:
    """Render a clean, secure, centered Apple/Google-standard authentication screen."""
    # Ensure default user is seeded for instant first-time login
    auth_service.seed_default_user_if_empty()

    # Center alignment wrapper
    _, col_main, _ = st.columns([1, 1.8, 1])

    with col_main:
        st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)

        with st.container(border=True):
            # Brand Header
            st.markdown(
                """
                <div style="text-align: center; padding: 12px 10px 16px 10px;">
                    <div style="
                        width: 56px; height: 56px; margin: 0 auto 12px auto;
                        background: #EFF6FF; border: 1.5px solid #93C5FD; border-radius: 14px;
                        display: flex; align-items: center; justify-content: center; font-size: 28px;
                    ">📄</div>
                    <h2 style="margin: 0; font-size: 1.6rem; font-weight: 700; letter-spacing: -0.02em;">Clarifile</h2>
                    <div style="font-size: 0.88rem; color: #64748B; margin-top: 4px;">
                        Intelligent Multi-User Document Intelligence
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Session Alert
            if "auth_alert" in st.session_state and st.session_state.auth_alert:
                alert = st.session_state.auth_alert
                if alert["type"] == "error":
                    st.error(alert["msg"])
                elif alert["type"] == "success":
                    st.success(alert["msg"])
                st.session_state.auth_alert = None

            tab_login, tab_register = st.tabs(["🔐 Sign In", "✨ Create Account"])

            # -----------------------------------------------------------------
            # Tab 1: Sign In
            # -----------------------------------------------------------------
            with tab_login:
                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                login_user = st.text_input(
                    "Username",
                    placeholder="Enter your username",
                    key="input_login_username",
                )
                login_pass = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                    key="input_login_password",
                )

                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

                if st.button("Sign In →", type="primary", use_container_width=True, key="btn_login_submit"):
                    if not login_user.strip() or not login_pass:
                        st.session_state.auth_alert = {
                            "type": "error",
                            "msg": "Please enter both username and password.",
                        }
                        st.rerun()

                    success, user, msg = auth_service.authenticate(login_user, login_pass)
                    if success and user:
                        st.session_state.authenticated_user = user.to_dict()
                        # Reset per-session state for fresh user
                        st.session_state.uploaded_docs = {}
                        st.session_state.chat_history = []
                        st.session_state.active_page = "Dashboard"
                        st.rerun()
                    else:
                        st.session_state.auth_alert = {"type": "error", "msg": msg}
                        st.rerun()

                st.markdown(
                    """
                    <div style="
                        margin-top: 16px; padding: 10px 12px;
                        background: rgba(0, 102, 204, 0.05); border: 1px solid rgba(0, 102, 204, 0.15);
                        border-radius: 8px; font-size: 0.8rem; color: #64748B; text-align: center;
                    ">
                        💡 <b>Default Demo Account:</b><br/>
                        Username: <code>midhun</code> &nbsp;•&nbsp; Password: <code>password123</code>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # -----------------------------------------------------------------
            # Tab 2: Create Account
            # -----------------------------------------------------------------
            with tab_register:
                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                reg_name = st.text_input(
                    "Your Name",
                    placeholder="e.g. Alex Smith",
                    key="input_reg_name",
                )
                reg_user = st.text_input(
                    "Choose Username",
                    placeholder="Letters, numbers, min 3 chars",
                    key="input_reg_username",
                )
                reg_pass = st.text_input(
                    "Choose Password",
                    type="password",
                    placeholder="Min 6 characters",
                    key="input_reg_password",
                )
                reg_confirm = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Repeat password",
                    key="input_reg_confirm",
                )

                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

                if st.button("Create Account & Enter →", type="primary", use_container_width=True, key="btn_reg_submit"):
                    if not reg_user.strip() or not reg_pass:
                        st.session_state.auth_alert = {
                            "type": "error",
                            "msg": "Username and password are required.",
                        }
                        st.rerun()

                    if reg_pass != reg_confirm:
                        st.session_state.auth_alert = {
                            "type": "error",
                            "msg": "Passwords do not match. Please re-enter.",
                        }
                        st.rerun()

                    success, new_user, msg = auth_service.register(
                        username=reg_user,
                        password=reg_pass,
                        display_name=reg_name or reg_user,
                    )
                    if success and new_user:
                        st.session_state.authenticated_user = new_user.to_dict()
                        st.session_state.uploaded_docs = {}
                        st.session_state.chat_history = []
                        st.session_state.active_page = "Dashboard"
                        st.rerun()
                    else:
                        st.session_state.auth_alert = {"type": "error", "msg": msg}
                        st.rerun()

        st.markdown(
            """
            <div style="text-align: center; font-size: 0.78rem; color: #94A3B8; margin-top: 16px;">
                Each account receives its own isolated vector database and document library.
            </div>
            """,
            unsafe_allow_html=True,
        )
