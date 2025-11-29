import os
import google_auth_oauthlib.flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from pathlib import Path

project_dir = Path.home() / "Desktop" / "Youtube Automation"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
token_path = project_dir  / "token.json"
secret_path = project_dir / "client_secret.json"


def get_credentials():
    creds = None

    # Load existing token if available
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # If no valid credentials, ask user to log in once
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh token silently without login
            creds.refresh(Request())
        else:
            # First-time login
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                secret_path, SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save the token for future runs
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return creds


def upload_video(video_path, title, description, tags, privacy="public"):
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    # Get stored or new credentials
    creds = get_credentials()

    youtube = build("youtube", "v3", credentials=creds)

    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": privacy
        }
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media
    )

    print("Uploading...")

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Progress: {int(status.progress() * 100)}%")

    print("Done!")
    print("Video ID:", response["id"])