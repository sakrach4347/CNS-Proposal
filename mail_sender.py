#!/usr/bin/env python3
"""
CNS Automation - Main Email Sender
Final running file that processes generated_mails.csv and sends emails with logging
"""

import csv
import re
import sys
import time
from datetime import datetime

# Import our modules
from Gmail_send import gmail_send_message
from log_simple import EmailLogger

class EmailAutomation:
    def __init__(self, csv_file="generated_mails-5.csv", kill_switch=True):
        """
        Initialize the email automation system
        
        Args:
            csv_file (str): Path to the generated mails CSV file
            kill_switch (bool): If True, prevents actual email sending (dry run mode)
        """
        self.csv_file = csv_file
        self.kill_switch = kill_switch
        self.logger = EmailLogger()
        self.emails_processed = 0
        self.emails_sent = 0
        self.emails_failed = 0
        
        print("🚀 CNS Email Automation System")
        print("=" * 50)
        if self.kill_switch:
            print("⚠️  KILL SWITCH ENABLED - NO EMAILS WILL BE SENT")
            print("📋 Running in DRY RUN mode")
        else:
            print("✅ LIVE MODE - Emails will be sent")
        print("=" * 50)
    
    def extract_poc_info(self, to_email, body, poc_name_col=None, org_col=None):
        """
        Extract POC name and organization from email data
        
        Args:
            to_email (str): Recipient email address
            body (str): Email body content
            poc_name_col (str): POC name from CSV column (if available)
            org_col (str): Organization from CSV column (if available)
            
        Returns:
            tuple: (poc_name, organization)
        """
        # If we have POC info from CSV, use that first
        if poc_name_col and org_col:
            return poc_name_col.strip(), org_col.strip()
        
        # Fallback to regex extraction if CSV columns not available
        # Extract POC name from email body using regex
        # Look for "Dear Mr./Ms./Dr. [Name]" pattern
        name_patterns = [
            r"Dear (?:Mr\.|Ms\.|Dr\.|Mrs\.)?\s*([A-Za-z\s]+),",
            r"Hi\s+([A-Za-z\s]+),",
            r"Hello\s+([A-Za-z\s]+),"
        ]
        
        poc_name = "Unknown"
        for pattern in name_patterns:
            match = re.search(pattern, body)
            if match:
                poc_name = match.group(1).strip()
                break
        
        # Extract organization from email domain or body
        # First try to get from email domain
        email_domain = to_email.split('@')[1] if '@' in to_email else ""
        org_from_domain = email_domain.split('.')[0] if email_domain else ""
        
        # Try to find organization mentions in body
        org_patterns = [
            r"([A-Za-z\s]+)'s (?:impressive work|commitment|mission)",
            r"following ([A-Za-z\s]+)'s",
            r"impressed by ([A-Za-z\s]+)'s",
            r"([A-Za-z\s]+) in (?:providing|creating|developing)"
        ]
        
        organization = org_from_domain.title()
        for pattern in org_patterns:
            match = re.search(pattern, body)
            if match:
                potential_org = match.group(1).strip()
                if len(potential_org) > len(organization):
                    organization = potential_org
                break
        
        return poc_name, organization
    
    def load_emails(self):
        """
        Load emails from the CSV file
        
        Returns:
            list: List of email dictionaries
        """
        emails = []
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('From') and row.get('To') and row.get('Subject') and row.get('Body'):
                        emails.append({
                            'from': row['From'],
                            'to': row['To'],
                            'subject': row['Subject'],
                            'body': row['Body'],
                            'poc_name': row.get('POC_Name', ''),
                            'organization': row.get('Organization', '')
                        })
            
            print(f"📧 Loaded {len(emails)} emails from {self.csv_file}")
            return emails
            
        except FileNotFoundError:
            print(f"❌ Error: File {self.csv_file} not found")
            return []
        except Exception as e:
            print(f"❌ Error loading emails: {e}")
            return []
    
    def send_email_batch(self, emails, batch_size=5, delay_between_emails=2):
        """
        Send emails in batches with delays
        
        Args:
            emails (list): List of email dictionaries
            batch_size (int): Number of emails per batch
            delay_between_emails (int): Seconds to wait between emails
        """
        total_emails = len(emails)
        
        for i, email_data in enumerate(emails, 1):
            print(f"\n📧 Processing Email {i}/{total_emails}")
            print("-" * 40)
            
            # Extract POC info (use CSV columns if available, fallback to regex)
            poc_name, organization = self.extract_poc_info(
                email_data['to'], 
                email_data['body'],
                email_data.get('poc_name'),
                email_data.get('organization')
            )
            
            print(f"📨 To: {email_data['to']}")
            print(f"👤 POC: {poc_name}")
            print(f"🏢 Org: {organization}")
            print(f"📝 Subject: {email_data['subject'][:50]}...")
            
            self.emails_processed += 1
            
            if self.kill_switch:
                # Dry run mode - just log without sending
                print("🚫 KILL SWITCH - Email not sent (dry run)")
                self.logger.log_email(poc_name, organization, ping_count=1, status="Dry Run")
                self.emails_sent += 1  # Count as "sent" for dry run stats
            else:
                # Actually send the email
                try:
                    result = gmail_send_message(
                        to_email=email_data['to'],
                        from_email=email_data['from'],
                        subject=email_data['subject'],
                        body=email_data['body'],
                        poc_name=poc_name,
                        org=organization,
                        enable_logging=True
                    )
                    
                    if result:
                        print("✅ Email sent successfully")
                        self.emails_sent += 1
                    else:
                        print("❌ Email failed to send")
                        self.emails_failed += 1
                        
                except Exception as e:
                    print(f"❌ Error sending email: {e}")
                    self.logger.log_email(poc_name, organization, ping_count=1, status="Failed")
                    self.emails_failed += 1
            
            # Batch processing with delays
            if i % batch_size == 0 and i < total_emails:
                print(f"\n⏱️  Batch {i//batch_size} completed. Waiting 30 seconds before next batch...")
                # time.sleep(30)
            elif i < total_emails:
                print(f"⏱️  Waiting {delay_between_emails} seconds...")
                time.sleep(delay_between_emails)
    
    def run(self):
        """
        Main execution function
        """
        print(f"\n🔄 Starting email automation at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Load emails
        emails = self.load_emails()
        if not emails:
            print("❌ No emails to process. Exiting.")
            return
        
        # Confirm execution
        if not self.kill_switch:
            print(f"\n⚠️  WARNING: You are about to send {len(emails)} REAL emails!")
            confirm = input("Type 'SEND' to confirm or anything else to cancel: ").strip()
            if confirm != 'SEND':
                print("❌ Operation cancelled by user")
                return
        
        # Send emails
        self.send_email_batch(emails)
        
        # Final statistics
        self.print_summary()
    
    def print_summary(self):
        """Print final execution summary"""
        print("\n" + "="*50)
        print("📊 EMAIL AUTOMATION SUMMARY")
        print("="*50)
        print(f"📧 Total Emails Processed: {self.emails_processed}")
        print(f"✅ Emails Sent: {self.emails_sent}")
        print(f"❌ Emails Failed: {self.emails_failed}")
        print(f"⏱️  Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if self.kill_switch:
            print("🚫 Mode: DRY RUN (Kill switch enabled)")
        else:
            print("✅ Mode: LIVE SENDING")
        
        print("\n📋 Recent logs:")
        self.logger.print_recent_logs(5)


def main():
    """Main function with command line options"""
    
    # Check for kill switch override
    kill_switch = True  # Default: safe mode
    
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == '--live':
            kill_switch = False
            print("⚠️  LIVE MODE ENABLED - Emails will be sent!")
        elif sys.argv[1].lower() == '--dry-run':
            kill_switch = True
            print("🚫 DRY RUN MODE - No emails will be sent")
        elif sys.argv[1].lower() == '--help':
            print("CNS Email Automation Usage:")
            print("python main_sender.py              # Dry run mode (default)")
            print("python main_sender.py --dry-run    # Dry run mode (explicit)")
            print("python main_sender.py --live       # Live sending mode")
            print("python main_sender.py --help       # Show this help")
            return
    
    # Create and run automation
    automation = EmailAutomation(kill_switch=kill_switch)
    automation.run()


if __name__ == "__main__":
    main()
