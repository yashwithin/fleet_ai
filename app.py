import streamlit as st
from llm import run_agent
from sqlite_db import list_customers, list_rides, list_drivers, reset_system

st.set_page_config(page_title="🚖 Ride Chatbot", layout="wide")
st.title("🚖 Ride Booking Assistant")


def render_response(response):
    # Case 1: tool call output
    if isinstance(response, dict) and "tool_output" in response:
        st.subheader("Tool Used")
        st.code(response["tool_name"])

        # st.subheader("Input")
        # st.json(response["tool_args"])

        st.subheader("Output")
        st.json(response["tool_output"])
        return

    # Case 2: normal chat
    if isinstance(response, dict) and "message" in response:
        st.write(response["message"])
        return

    # fallback
    st.write(response)


# ---------------------------
# SIDEBAR (Demo + Debug)
# ---------------------------
with st.sidebar:
    st.header("Sample Queries")

    sample_queries = [
        "Book a cab for C001 from Airport to MI Road",
        "Check wallet balance for C001",
        "Where is my ride R1775814979",
        "Book a ride for C002 from JECRC to Poornima",
    ]

    for q in sample_queries:
        if st.button(q):
            st.session_state["sample_query"] = q

    st.divider()

    if st.button("Refresh Data"):
        st.rerun()

    st.dataframe(list_customers())

    st.dataframe(list_drivers())

    st.dataframe(list_rides())

    st.divider()

    if st.button("🔄 Reset System (Drivers + Rides)"):
        msg = reset_system()
        st.success(msg)
        st.rerun()

# ---------------------------
# CHAT STATE
# ---------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# Reset chat
if st.button("🔄 Reset Chat"):
    st.session_state.messages = []
    st.rerun()

# Display chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ---------------------------
# INPUT (with sample support)
# ---------------------------
user_input = st.chat_input("Ask something...")

# If sample button clicked
if "sample_query" in st.session_state:
    user_input = st.session_state.pop("sample_query")

# ---------------------------
# HANDLE INPUT
# ---------------------------
if user_input:
    # Show user
    st.chat_message("user").write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Run agent
    response = run_agent(user_input)

    # Show assistant
    with st.chat_message("assistant"):
        render_response(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
