import os
import time
import base64
import csv
from email.message import EmailMessage

# Google API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Local LLM import
import ollama

# We need BOTH readonly (to check replies/threads) and send scopes
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
]

def authenticate_gmail():
    """Authenticates using the existing token.json, requesting more scopes if needed."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no credentials, they are invalid, or they are missing the readonly scope
    if not creds or not creds.valid or not creds.has_scopes(SCOPES):
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                # Refresh failed, need full re-auth
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
        else:
            print("🔑 Required scopes have changed. Requesting new authorization...")
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    return build('gmail', 'v1', credentials=creds)

def get_target_emails(csv_file="generated_mails-5.csv"):
    """Reads the CSV to know who we just emailed and gets their names/orgs."""
    targets = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('To'):
                    # Extract first name safely for the greeting
                    full_name = row.get('POC_Name', 'there').strip()
                    first_name = full_name.split()[0] if full_name else "there"
                    
                    targets.append({
                        'email': row['To'],
                        'first_name': first_name,
                        'organization': row.get('Organization', 'your organization')
                    })
    except Exception as e:
        print(f"❌ Error reading {csv_file}: {e}")
    return targets

def extract_original_email_data(service, recipient_email):
    """Snipes the 'Sent' folder to find the exact message IDs and Body."""
    try:
        # Search for the most recent email sent to this person
        results = service.users().messages().list(userId='me', q=f"to:{recipient_email} in:sent", maxResults=1).execute()
        messages = results.get('messages', [])
        
        if not messages:
            return None
            
        msg_id = messages[0]['id']
        thread_id = messages[0]['threadId']
        
        # Get full message details
        msg_full = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        
        # Extract headers
        headers = msg_full['payload'].get('headers', [])
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
        rfc_message_id = next((h['value'] for h in headers if h['name'].lower() == 'message-id'), '')
        
        # Robustly extract plain text body
        body = ""
        def extract_text(payload):
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data', '')
                        return base64.urlsafe_b64decode(data + "===").decode('utf-8')
                    elif 'parts' in part:
                        res = extract_text(part)
                        if res: return res
            elif payload.get('mimeType') == 'text/plain':
                data = payload['body'].get('data', '')
                return base64.urlsafe_b64decode(data + "===").decode('utf-8')
            return ""

        body = extract_text(msg_full['payload'])

        return {
            "threadId": thread_id,
            "rfc_message_id": rfc_message_id,
            "subject": subject,
            "body": body,
            "to": recipient_email
        }
    except Exception as e:
        print(f"⚠️ Error fetching sent mail for {recipient_email}: {e}")
        return None

def has_replied(service, thread_id):
    """Checks the thread. If there's more than 1 message, they replied."""
    try:
        thread = service.users().threads().get(userId='me', id=thread_id).execute()
        messages = thread.get('messages', [])
        # If there is more than 1 message in the thread, we got a reply!
        return len(messages) > 1
    except Exception as e:
        print(f"⚠️ Error checking thread {thread_id}: {e}")
        return False

def generate_smart_followup(original_body, first_name, organization):
    """Uses local Ollama to fill in your specific follow-up template."""
    
    prompt = f"""You are an expert business consultant at 180 Degrees Consulting. You are writing a follow-up email.

Original Email Context:
{original_body}

Task: Use the EXACT template below for your response. 
Fill in the [BRACKETED] placeholders based on the Original Email Context provided above.
Do NOT change the rest of the text. Do NOT add subject lines, introductory text, markdown formatting, or signatures. Ensure there is a blank line between each paragraph.

TEMPLATE:
Dear {first_name},

I hope you’ve been doing well.

I just wanted to gently follow up on my previous message regarding a potential collaboration between {organization} and 180 Degrees Consulting, IIT Kharagpur. Just wanted to check in and see if you might have had a chance to review my earlier note.

We remain very excited about the possibility of supporting {organization}’s impactful work in the [INSERT SPECIFIC INDUSTRY/DOMAIN] space, particularly in areas such as [INSERT VALUE PROP 1], [INSERT VALUE PROP 2], and [INSERT VALUE PROP 3].

If this is something you’d be open to exploring, I would be happy to work around your schedule for a brief virtual conversation at a time that’s convenient for you.

Looking forward to hearing from you.
"""

    try:
        response = ollama.chat(model='llama3', messages=[
            {'role': 'system', 'content': 'You are a precise system that only outputs the requested template. No preamble, no markdown formatting.'},
            {'role': 'user', 'content': prompt}
        ])
        
        # Clean up any weird line breaks the LLM might have hallucinated
        cleaned_response = response['message']['content'].strip()
        cleaned_response = cleaned_response.replace('\r\n', '\n')
        
        return cleaned_response
    except Exception as e:
        print(f"❌ Ollama Error: {e}")
        return None

def send_threaded_followup(service, email_data, followup_body):
    """Sends the new email properly nested in the original thread."""
    try:
        message = EmailMessage()
        message.set_content(followup_body)
        
        message["To"] = email_data['to']
        
        # Prefix "Re: " if not already there to match standard reply behavior
        subject = email_data['subject']
        message["Subject"] = subject if subject.startswith("Re:") else f"Re: {subject}"
        
        # CRITICAL: These headers force Gmail to thread the email
        if email_data['rfc_message_id']:
            message["In-Reply-To"] = email_data['rfc_message_id']
            message["References"] = email_data['rfc_message_id']
        
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # Include threadId in the API payload for absolute grouping
        create_message = {
            "raw": encoded_message,
            "threadId": email_data['threadId']
        }
        
        service.users().messages().send(userId="me", body=create_message).execute()
        print(f"✅ Successfully sent threaded follow-up to {email_data['to']}")
        
    except HttpError as e:
        print(f"❌ API Failed to send follow-up to {email_data['to']}: {e}")
    except Exception as e:
        print(f"❌ Failed to send follow-up to {email_data['to']}: {e}")

def main():
    print("🚀 180DC Smart Follow-up Prototype initialized.")
    print("=" * 50)
    
    # 1. Start the 15-minute timer
    wait_minutes = 1
    print(f"⏱️  Waiting {wait_minutes} minutes to allow for replies...")
    for remaining in range(wait_minutes * 60, 0, -60):
        print(f"   ... {remaining // 60} minutes remaining. (Go reply to your dummy emails!)")
        time.sleep(60)
        
    print("\n🔍 Time's up! Analyzing sent emails and checking for replies...")
    print("-" * 50)
    
    # 2. Authenticate and Get Targets
    service = authenticate_gmail()
    targets = get_target_emails()
    
    if not targets:
        print("❌ No target emails found in generated_mails-5.csv. Exiting.")
        return

    # 3. Process each target email
    for target in targets:
        email = target['email']
        first_name = target['first_name']
        organization = target['organization']
        
        print(f"\n📨 Evaluating Thread for: {email}")
        
        # Snipe the original sent data
        email_data = extract_original_email_data(service, email)
        if not email_data:
            print(f"   ⚠️ Could not find a recently sent email to {email}. Skipping.")
            continue
            
        # Check if they replied
        if has_replied(service, email_data['threadId']):
            print(f"   🟢 GREEN SIGNAL: {email} replied! Eliminating from follow-up queue.")
            continue
            
        print(f"   🔴 No reply from {email}. Generating structured follow-up locally via Ollama...")
        
        # Generate and Send using new template system
        followup_body = generate_smart_followup(email_data['body'], first_name, organization)
        if followup_body:
            print(f"   🤖 Draft Generated:\n   --- \n{followup_body}\n   ---")
            send_threaded_followup(service, email_data, followup_body)

    print("\n🎉 Follow-up protocol complete!")
    print("=" * 50)

if __name__ == "__main__":
    main()