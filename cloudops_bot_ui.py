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
st.set_page_config(page_title="I am your COMFY", page_icon="🤖", layout="wide")

# ----------------------------
# Session State for Chat
# ----------------------------
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"sender": "bot", "text": "Hello 👋, I’m your COMFY (Cloud Assistant)! How can I help you today?"}
    ]

if "pending_query" not in st.session_state:
    st.session_state["pending_query"] = None

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
# Layout: Two Columns
# ----------------------------
col1, col2 = st.columns([1, 3])

# ----------------------------
# Left Column → Quick Actions
# ----------------------------
with col1:
    st.subheader("✨ Quick Actions")

    predefined_prompts = [
        "Provide cost optimization solution for your account",
        "List all running EC2 instances",
        "Show billing summary of my account",
        "Analyze my EC2 instance utilization"
    ]

    for prompt in predefined_prompts:
        if st.button(prompt, use_container_width=True):
            st.session_state["messages"].append({"sender": "user", "text": prompt})
            st.session_state["pending_query"] = prompt
            st.rerun()

# ----------------------------
# Right Column → Welcome + Chat
# ----------------------------
with col2:
    # Welcome Box
    st.markdown(
        """
        <div style="
            border: 2px solid #4CAF50; 
            border-radius: 12px; 
            padding: 20px; 
            margin: 20px auto; 
            text-align: left;
            background-color: #f9f9f9;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        ">
            <h3 style="color:#2E7D32;"> Welcome to COMFY ! </h3>
            <h4 style="color:#2E7D32;"> Your Intelligent Cloud Assistant. </h4>
            <p>I am <b>COMFY</b> - Who am I & What can I do? I can:</p>
            <ul>
                <li>💰 Provide you with <b>cost optimization solutions</b> for your AWS account</li>
                <li>📊 Provide you with <b>billing summaries</b> for your AWS account</li>
                <li>🖥️ Help with <b>cloud operations</b> like EC2 management</li>
                <li>🔎 Perform <b>EC2 analysis</b></li>
            </ul>
            <p>✨ I act as your personal operations assistant to make your cloud journey smoother.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Chat History
    for msg in st.session_state["messages"]:
        if msg["sender"] == "user":
            st.markdown(f"**🧑 You:** {msg['text']}")
        else:
            st.markdown(f"**🤖 Bot:** {msg['text']}")

    # Chat Input
    query = st.chat_input("Type your message...")
    if query:
        st.session_state["messages"].append({"sender": "user", "text": query})
        st.session_state["pending_query"] = query
        st.rerun()

    # Process Pending Query
    if st.session_state["pending_query"]:
        with st.status("🤖 Your request is loading, this may take a few seconds...", expanded=True) as status:
            try:
                reply_json = invoke_lambda_iam(st.session_state["pending_query"])
                reply = reply_json.get("reply", "⚠️ No response from Lambda")
            except Exception as e:
                reply = f"⚠️ Error contacting Lambda: {str(e)}"

            st.session_state["messages"].append({"sender": "bot", "text": reply})
            st.session_state["pending_query"] = None
            status.update(label="✅ Response received!", state="complete", expanded=False)
            st.rerun()
