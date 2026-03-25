import csv
import os
from datetime import datetime

class EmailLogger:
    def __init__(self, csv_file="email_log.csv"):

        self.csv_file = csv_file
        self._setup_csv_file()
    
    def _setup_csv_file(self):
        """Set up CSV file with headers if it doesn't exist"""
        if not os.path.exists(self.csv_file):
            headers = ["POC Name", "Org", "Number of Pings", "Status"]
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            print(f"Created CSV log file: {self.csv_file}")
    
    def log_email(self, poc_name, org, ping_count=1, status="Success"):

        log_data = [poc_name, org, ping_count, status]
        
        # Log to CSV
        self._log_to_csv(log_data)
        
        # Print to console
        print(f"Logged: {status} - {poc_name} ({org}) - Ping #{ping_count}")
    
    def _log_to_csv(self, log_data):
        """Log data to CSV file"""
        try:
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(log_data)
        except Exception as e:
            print(f"❌ Failed to log to CSV: {e}")
    
    def update_ping_count(self, poc_name, org):

        rows = []
        ping_count = 1
        found = False
        
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            # Find existing entry and update ping count
            for i, row in enumerate(rows):
                if len(row) >= 4 and i > 0:  # Skip header
                    if row[0] == poc_name and row[1] == org:
                        current_pings = int(row[2]) if row[2].isdigit() else 0
                        ping_count = current_pings + 1
                        rows[i][2] = str(ping_count)
                        rows[i][3] = "Success"  # Update status
                        found = True
                        break
            
            if found:
                # Write back updated data
                with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerows(rows)
            else:
                # Add new entry
                self.log_email(poc_name, org, ping_count, "Success")
        
        except Exception as e:
            print(f"❌ Error updating ping count: {e}")
            # Fall back to adding new entry
            self.log_email(poc_name, org, ping_count, "Success")
        
        return ping_count
    
    def get_recent_logs(self, limit=10):
        """Get recent log entries from CSV"""
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                
            if len(rows) <= 1:  # Only headers or empty
                return []
            
            # Return recent entries (excluding header)
            return rows[1:limit+1]
            
        except Exception as e:
            print(f"❌ Failed to read logs: {e}")
            return []
    
    def print_recent_logs(self, limit=5):
        """Print recent log entries"""
        logs = self.get_recent_logs(limit)
        
        if not logs:
            print("No recent logs found")
            return
        
        print(f"\nRecent Email Logs (Last {len(logs)} entries):")
        print("-" * 60)
        print(f"{'POC Name':<20} {'Organization':<25} {'Pings':<8} {'Status':<10}")
        print("-" * 60)
        
        for log in logs:
            if len(log) >= 4:
                poc_name, org, pings, status = log[0], log[1], log[2], log[3]
                status_emoji = "✅" if status == "Success" else "❌" if status == "Failed" else "⏳"
                print(f"{poc_name:<20} {org:<25} {pings:<8} {status_emoji} {status}")
        
        print("-" * 60)


# Convenience function to create logger instance
def create_logger():
    """Create and return an EmailLogger instance"""
    return EmailLogger()


if __name__ == "__main__":
    # Test the logger
    logger = create_logger()
    
    # Test log entry
    logger.log_email(
        poc_name="John Doe",
        org="ABC Company",
        ping_count=1,
        status="Success"
    )
    
    # Test updating ping count
    logger.update_ping_count("John Doe", "ABC Company")
    
    # Show recent logs
    logger.print_recent_logs()
