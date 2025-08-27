import streamlit as st
import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import json

# Lambda Function URL (with AWS_IAM auth)
LAMBDA_URL = "https://h5xtjthqbbwegusk5eqyvpsa7u0mlwlm.lambda-url.us-east-1.on.aws/"
REGION = "us-east-1"  # replace with your Lambda region

# Initialize Streamlit UI
st.set_page_config(page_title="CloudOps Bot", page_icon="🤖", layout="centered")
st.title("🤖 CloudOps Assistant")

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"sender": "bot", "text": "Hello 👋, I’m your CloudOps Assistant. How can I help you today?"}
    ]

# Display chat history
for msg in st.session_state["messages"]:
    if msg["sender"] == "user":
        st.markdown(f"**🧑 You:** {msg['text']}")
    else:
        st.markdown(f"**🤖 Bot:** {msg['text']}")

# Input box
query = st.text_input("Your message:")

# Function to invoke Lambda URL with SigV4 signing
def invoke_lambda_iam(query):
    # Get AWS credentials from Streamlit Secrets
    aws_access_key = st.secrets["AWS_ACCESS_KEY_ID"]
    aws_secret_key = st.secrets["AWS_SECRET_ACCESS_KEY"]
    aws_region = st.secrets.get("AWS_DEFAULT_REGION", REGION)

    # If using temporary session tokens (like from IAM role), add them
    aws_session_token = st.secrets.get("AWS_SESSION_TOKEN", None)

    # Create frozen credentials manually
    from botocore.credentials import Credentials
    frozen = Credentials(
        access_key=aws_access_key,
        secret_key=aws_secret_key,
        token=aws_session_token
    ).get_frozen_credentials()

    # Prepare AWS signed request
    request = AWSRequest(
        method="POST",
        url=LAMBDA_URL,
        data=json.dumps({"query": query}),
        headers={"Content-Type": "application/json"}
    )
    SigV4Auth(frozen, "lambda", aws_region).add_auth(request)

    # Send signed request
    response = requests.post(LAMBDA_URL, data=request.body, headers=dict(request.headers))
    return response.json()

# Send button action
if st.button("Send") and query:
    # Add user message
    st.session_state["messages"].append({"sender": "user", "text": query})

    try:
        reply_json = invoke_lambda_iam(query)
        reply = reply_json.get("reply", "⚠️ No response from Lambda")
    except Exception as e:
        reply = f"⚠️ Error contacting Lambda: {str(e)}"

    # Add bot reply
    st.session_state["messages"].append({"sender": "bot", "text": reply})
    st.rerun()