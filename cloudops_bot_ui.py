import streamlit as st
import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import json
import pandas as pd  # ✅ for pretty tables

# Lambda Function URL (with AWS_IAM auth)
LAMBDA_URL = "https://h5xtjthqbbwegusk5eqyvpsa7u0mlwlm.lambda-url.us-east-1.on.aws/"
REGION = "us-east-1" # replace with your Lambda region

# ----------------------------
# Streamlit Page Config
# ----------------------------
st.set_page_config(page_title="CloudOps Bot", page_icon="🤖", layout="centered")
st.title("🤖 CloudOps Assistant")

# ----------------------------
# Who am I / What can I do section
# ----------------------------
with st.expander("ℹ️ Who am I / What can I do?", expanded=True):
    st.markdown(
        """
        I am your **CloudOps Assistant** 🧑‍💻.  
        
        ✅ I can provide you with **cost optimization solutions** for your AWS account. 
        ✅ I can provide you with **Billing summary** for your AWS account.
        ✅ I can help with **cloud operations** like **EC2 management** and **EC2 analysis**.  
        ✅ I act as your personal **AWS operations helper** to make your cloud journey easier.  
        """
    )

# ----------------------------
# Custom Chat Styles
# ----------------------------
st.markdown(
    """
    <style>
    .chat-box {
        border-radius: 18px;
        padding: 10px 14px;
        margin: 8px 0;
        display: inline-block;
        max-width: 70%;
        word-wrap: break-word;
        font-size: 15px;
        line-height: 1.4;
        box-shadow: 0px 2px 6px rgba(0,0,0,0.15);
    }
    .user-msg {
        background-color: #2C2F33;
        color: #F5F5F5;
        margin-left: auto;
        text-align: right;
    }
    .bot-msg {
        background-color: #2C2F33;
        color: #F5F5F5;
        margin-right: auto;
        text-align: left;
    }
    .scrollable-table {
        max-height: 300px;
        overflow-y: auto;
        display: block;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ----------------------------
# Session State for Messages
# ----------------------------
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"sender": "bot", "text": "Hello 👋, I’m your CloudOps Assistant. How can I help you today?"}
    ]

# ----------------------------
# Display Chat History
# ----------------------------
for msg in st.session_state["messages"]:
    if msg["sender"] == "user":
        st.markdown(f"<div class='chat-box user-msg'>🧑 {msg['text']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='chat-box bot-msg'>🤖 {msg['text']}</div>", unsafe_allow_html=True)

# ----------------------------
# Function to invoke Lambda
# ----------------------------
def invoke_lambda_iam(query):
    aws_access_key = st.secrets["AWS_ACCESS_KEY_ID"]
    aws_secret_key = st.secrets["AWS_SECRET_ACCESS_KEY"]
    aws_region = st.secrets.get("AWS_DEFAULT_REGION", REGION)
    aws_session_token = st.secrets.get("AWS_SESSION_TOKEN", None)

    from botocore.credentials import Credentials
    frozen = Credentials(
        access_key=aws_access_key,
        secret_key=aws_secret_key,
        token=aws_session_token
    ).get_frozen_credentials()

    request = AWSRequest(
        method="POST",
        url=LAMBDA_URL,
        data=json.dumps({"query": query}),
        headers={"Content-Type": "application/json"}
    )
    SigV4Auth(frozen, "lambda", aws_region).add_auth(request)

    response = requests.post(LAMBDA_URL, data=request.body, headers=dict(request.headers))
    return response.json()

# ----------------------------
# Helper: format structured responses
# ----------------------------
def format_as_table(data):
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        df = pd.DataFrame(data)
        return f"<div class='scrollable-table'>{df.to_markdown(index=False)}</div>"
    elif isinstance(data, dict):
        return "\n".join([f"- **{k}**: {v}" for k, v in data.items()])
    else:
        return str(data)

# ----------------------------
# Chat Input
# ----------------------------
query = st.chat_input("Type your message...")

if query:
    st.session_state["messages"].append({"sender": "user", "text": query})

    with st.status("🤖 Working on your request, this may take a few seconds...", expanded=True) as status:
        try:
            reply_json = invoke_lambda_iam(query)

            reply = reply_json.get("reply", "")

            # format any extra fields from lambda (structured data)
            for key, value in reply_json.items():
                if key != "reply" and value:
                    reply += "\n\n" + format_as_table(value)

            if not reply:
                reply = "⚠️ No response from Lambda"

        except Exception as e:
            reply = f"⚠️ Error contacting Lambda: {str(e)}"

        status.update(label="✅ Response received", state="complete", expanded=False)

    st.session_state["messages"].append({"sender": "bot", "text": reply})
    st.rerun()

