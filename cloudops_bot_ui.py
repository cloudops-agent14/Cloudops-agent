import streamlit as st
import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import json

# Lambda Function URL (with AWS_IAM auth)
LAMBDA_URL = "https://h5xtjthqbbwegusk5eqyvpsa7u0mlwlm.lambda-url.us-east-1.on.aws/"
REGION = "us-east-1"  # replace with your Lambda region

# ----------------------------
# Streamlit Page Config
# ----------------------------
st.set_page_config(page_title="CloudOps Bot", page_icon="🤖", layout="centered")
st.title("🤖 CloudOps Assistant")

# ----------------------------
# Who am I / What can I do box
# ----------------------------
st.markdown(
    """
    <div style="
        border: 2px solid #4CAF50; 
        border-radius: 12px; 
        padding: 20px; 
        margin: 20px auto; 
        width: 80%; 
        text-align: left;
        background-color: #f9f9f9;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    ">
        <h3 style="color:#2E7D32;">🌟 Who am I & What can I do?</h3>
        <p>I am your <b>CloudOps Assistant</b>. I can:</p>
        <ul>
            <li>💰 Provide you with <b>cost optimization solutions</b> for your AWS account</li>
            <li>📊 Provide you with <b>billing summaries</b> for your AWS account</li>
            <li>🖥️ Help with <b>cloud operations</b> like EC2 management</li>
            <li>🔎 Perform <b>EC2 analysis</b></li>
        </ul>
        <p>✨ I act as your personal AWS operations helper to make your cloud journey easier.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# ----------------------------
# Session State for Chat
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
        st.markdown(f"**🧑 You:** {msg['text']}")
    else:
        st.markdown(f"**🤖 Bot:** {msg['text']}")

# ----------------------------
# Function to invoke Lambda
# ----------------------------
def invoke_lambda_iam(query):
    # Get AWS credentials from Streamlit Secrets
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
# Chat Input (Enter to send & clears automatically)
# ----------------------------
query = st.chat_input("Type your message...")  # clears automatically after sending

if query:
    # Add user message
    st.session_state["messages"].append({"sender": "user", "text": query})

    # Show a fallback loader near the chat
    with st.status("🤖 Your request is loading... this may take some time", expanded=True) as status:
        try:
            reply_json = invoke_lambda_iam(query)
            reply = reply_json.get("reply", "⚠️ No response from Lambda")
        except Exception as e:
            reply = f"⚠️ Error contacting Lambda: {str(e)}"

        # Update loader when done
        status.update(label="✅ Response received", state="complete", expanded=False)

    # Add bot reply
    st.session_state["messages"].append({"sender": "bot", "text": reply})
    st.rerun()

