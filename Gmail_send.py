import base64
from email.message import EmailMessage
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Import our simplified logging system
from log_simple import EmailLogger

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']


def gmail_send_message(to_email=None, from_email=None, subject=None, body=None, poc_name=None, org=None, enable_logging=True):
  """Create and send an email message
  Print the returned  message id
  Returns: Message object, including message id
  """
  # Initialize CSV logger
  logger = EmailLogger() if enable_logging else None
  
  # Default values if not provided
  # if not to_email:
  #   to_email = input("Enter recipient email: ")
  # if not from_email:
  #   from_email = to_email  # Use same email as sender
  # if not subject:
  #   subject = "Test: Automated email from Python"
  # if not body:
  #   body = "This is an automated email sent via Python Gmail API - Test successful!"
  # if not poc_name:
  #   poc_name = input("Enter POC name: ")
  # if not org:
  #   org = input("Enter organization: ")
  creds = None
  # The file token.json stores the user's access and refresh tokens. It is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          'credentials.json', SCOPES)
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.json', 'w') as token:
      token.write(creds.to_json())

  try:
    service = build("gmail", "v1", credentials=creds)
    message = EmailMessage()

    message.set_content(body)

    message["To"] = to_email
    message["From"] = from_email
    message["Subject"] = subject
    message["cc"]= ""

    # encoded message
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    create_message = {"raw": encoded_message}
    # pylint: disable=E1101
    send_message = (
        service.users()
        .messages()
        .send(userId="me", body=create_message)
        .execute()
    )
    print(f'Email sent successfully!')
    print(f'To: {to_email}')
    print(f'Subject: {subject}')
    print(f'Message Id: {send_message["id"]}')
    
    # Log successful email with new format
    if logger:
      ping_count = logger.update_ping_count(poc_name, org)
      print(f"Updated ping count for {poc_name} to {ping_count}")
    
    return send_message
  except HttpError as error:
    print(f"An error occurred: {error}")
    
    # Log failed email with new format
    if logger:
      logger.log_email(poc_name, org, ping_count=1, status="Failed")
    
    send_message = None
  return send_message


if __name__ == "__main__":
  gmail_send_message()