"""MBOX file parser."""
import mailbox
import quopri
from pathlib import Path
from typing import Generator, Tuple


class MBoxParser:
    """Parser for MBOX email files."""
    
    def __init__(self, mbox_path: str):
        """Initialize MBOX parser."""
        self.mbox_path = Path(mbox_path)
        
        if not self.mbox_path.exists():
            raise FileNotFoundError(f"MBOX file not found: {self.mbox_path}")
    
    def parse(self) -> Generator[Tuple[str, str, str], None, None]:
        """
        Parse MBOX file and yield email data.
        
        Yields:
            Tuple of (subject, from_address, body)
        """
        try:
            mbox = mailbox.mbox(str(self.mbox_path))
            
            for message in mbox:
                subject = message.get('subject', '')
                from_addr = message.get('from', '')
                
                # Extract email body
                body = ""
                if message.is_multipart():
                    for part in message.walk():
                        if part.get_content_type() == 'text/plain':
                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            break
                        elif part.get_content_type() == 'text/html':
                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                else:
                    body = message.get_payload(decode=True).decode('utf-8', errors='ignore')
                
                # Handle quoted-printable encoding if present
                if '=' in body and body.count('=') > 5:  # Likely quoted-printable
                    try:
                        body = quopri.decodestring(body.encode()).decode('utf-8', errors='ignore')
                    except Exception:
                        pass  # If decoding fails, keep original
                
                yield subject, from_addr, body
        
        except Exception as e:
            raise RuntimeError(f"Error parsing MBOX file: {e}")
    
    @staticmethod
    def validate_email(subject: str, from_addr: str) -> bool:
        """Check if email appears to be from Zomato."""
        zomato_indicators = [
            'zomato' in subject.lower(),
            'zomato' in from_addr.lower(),
            'order' in subject.lower() and 'zomato' in from_addr.lower()
        ]
        return any(zomato_indicators)
