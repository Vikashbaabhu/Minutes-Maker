import streamlit as st
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import tempfile
import os
import time
import requests

INPUT_BUCKET = "minute-maker-input"
OUTPUT_BUCKET = "minute-maker-output"

AWS_ACCESS_KEY = st.secrets["AWS_ACCESS_KEY_ID"]
AWS_SECRET_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]
region = st.secrets.get("AWS_REGION", "us-east-1")

# API Endpoint for Processing
PROCESSING_API_URL = "https://iniyxycalb.execute-api.us-east-1.amazonaws.com/prod/upload"

# ---- S3 Client ---- #
def get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY
    )

# ---- Upload to Input Bucket ---- #
def upload_to_input_bucket(file_path, s3_filename):
    try:
        s3 = get_s3_client()
        s3.upload_file(file_path, INPUT_BUCKET, s3_filename)
        return True, f"✅ Uploaded to s3://{INPUT_BUCKET}/{s3_filename}"
    except NoCredentialsError:
        return False, "❌ AWS credentials not found."
    except Exception as e:
        return False, f"❌ Upload failed: {str(e)}"

# ---- Call Processing API ---- #
def call_processing_api(bucket_name, key_name):
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "bucket": bucket_name,
        "key": key_name
    }
    try:
        response = requests.post(PROCESSING_API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            return True, "✅ Processing API triggered successfully!"
        else:
            return False, f"❌ API call failed: {response.status_code} - {response.text}"
    except Exception as e:
        return False, f"❌ API call error: {str(e)}"

# ---- Check if output file exists ---- #
def check_and_fetch_output(video_filename):
    base_name = os.path.splitext(video_filename)[0]
    txt_filename = f"{base_name}_minutes.txt"  # Modified format: video name + _minutes.txt
    s3 = get_s3_client()

    try:
        response = s3.get_object(Bucket=OUTPUT_BUCKET, Key=txt_filename)
        text_content = response["Body"].read().decode("utf-8")
        return True, txt_filename, text_content

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchKey':
            return False, txt_filename, None
        else:
            return False, txt_filename, f"Unexpected S3 error: {error_code} - {e}"
    except Exception as e:
        return False, txt_filename, f"Unhandled exception: {str(e)}"

# ---- Session State ---- #
if "video_uploaded" not in st.session_state:
    st.session_state.video_uploaded = False
if "video_filename" not in st.session_state:
    st.session_state.video_filename = None
if "polling" not in st.session_state:
    st.session_state.polling = False

# ---- Streamlit UI ---- #
st.markdown("<h1 style='text-align: center; color: white;'>🎥 Minutes Maker</h1>", unsafe_allow_html=True)

st.markdown('<div class="background-container"></div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("📂 Upload Your Video File", type=["mp4", "mov", "avi", "mkv"])

# Upload Button
if uploaded_file is not None:
    st.video(uploaded_file)

    if st.button("🚀 Upload Video and Trigger Processing"):
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(uploaded_file.read())
            temp_path = tmp_file.name

        with st.spinner("Uploading to S3..."):
            success, msg = upload_to_input_bucket(temp_path, uploaded_file.name)
        os.remove(temp_path)

        if success:
            st.success(msg)
            st.session_state.video_uploaded = True
            st.session_state.video_filename = uploaded_file.name

            with st.spinner("Triggering processing API..."):
                api_success, api_msg = call_processing_api(INPUT_BUCKET, uploaded_file.name)

            if api_success:
                st.success(api_msg)
            else:
                st.error(api_msg)

        else:
            st.error(msg)

# Check Transcript Button
if st.session_state.video_uploaded:
    st.subheader("✅ Video uploaded successfully!")
    if st.button("🔍 Check for Transcript Output"):
        st.session_state.polling = True
        st.session_state.poll_start_time = time.time()  # Save start time
        st.rerun()

# Polling with 10 minutes maximum
if st.session_state.polling and st.session_state.video_filename:
    st.info("📡 Polling every 10 seconds for transcript (max 10 minutes)...")

    # Calculate elapsed time
    elapsed_minutes = (time.time() - st.session_state.poll_start_time) / 60

    if elapsed_minutes > 10:
        st.session_state.polling = False
        st.error("❌ Timeout: Transcript not found within 10 minutes.")
    else:
        found, txt_name, text = check_and_fetch_output(st.session_state.video_filename)

        if found:
            st.session_state.polling = False
            st.success(f"📝 Transcript `{txt_name}` found!")
            st.subheader("📄 Transcribed Text")
            st.text_area("Transcript", text, height=300)
            st.download_button("📥 Download Transcript", text, file_name=txt_name, mime="text/plain")
        else:
            time.sleep(10)
            st.rerun()
