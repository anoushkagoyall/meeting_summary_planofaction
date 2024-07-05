import os
import subprocess
import streamlit as st
import openai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from whisper import load_model

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

if not OPENAI_API_KEY:
    st.error("OpenAI API key not set. Please set the OPENAI_API_KEY environment variable.")
else:
    openai.api_key = OPENAI_API_KEY

st.title("Meeting Summariser and Plan of Action Generator")


def send_email(sender_email, sender_app_password, recipient_email, subject, body):
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = subject

    message.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp_server:
            smtp_server.starttls()
            smtp_server.login(sender_email, sender_app_password)
            smtp_server.sendmail(sender_email, recipient_email, message.as_string())

        st.success(f"Email sent successfully to {recipient_email}!")
    except Exception as e:
        st.error(f"Error sending email: {e}")

email_address = st.text_input("Enter email address")

video_file = st.file_uploader("Upload a video file", type=["mp4", "mkv", "mov", "avi"])

if video_file:
    with open("temp_video.mp4", "wb") as f:
        f.write(video_file.getbuffer())
    st.success("Video uploaded successfully")
    st.video(video_file)

    st.info("Converting video to audio...")
    audio_file = "temp_audio.wav"
    subprocess.run(["ffmpeg", "-y", "-i", "temp_video.mp4", audio_file])

    st.success("Audio extracted successfully")
    st.audio(audio_file)

    st.info("Transcribing audio...")
    model = load_model("base")
    result = model.transcribe(audio_file)
    transcription = result["text"]
    st.text_area("Transcription", transcription, height=200)

    st.info("Generating summary and plan of action...")
    prompt = f"Summarize the meeting and provide a plan of action:\n\n{transcription}"
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        summary_and_plan = response['choices'][0]['message']['content']
        st.text_area("Summary and Plan of Action", summary_and_plan, height=200)
    except openai.error.OpenAIError as e:
        st.error(f"OpenAI API error: {e}")
    except Exception as e:
        st.error(f"An error occurred: {e}")

    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        st.error("Sender's email credentials not configured. Please check the environment variables.")
    elif not email_address:
        st.error("Please enter a valid recipient email address.")
    else:
        sender_email = EMAIL_ADDRESS
        sender_app_password = EMAIL_PASSWORD
        recipient_email = email_address
        subject = "Summary and Plan of Action"
        body = f"""
Greetings sir/ma'am,

Please find below the summary and plan of action of the meeting.

Summary and Plan of Action:
{summary_and_plan}

Regards,
Anoushka Goyal
"""
        send_email(sender_email, sender_app_password, recipient_email, subject, body)