from sendgrid import SendGridAPIClient
from typing import List
from env import env_get_sendgrid_api_key

from_email = "x@markthemark.com"

def send_email(to_emails: List[str], subject: str, html: str, files: List = []) -> None:
    print(f"[send_email] to: ", to_emails)
    # --- build email payload
    payload = {
        # there's a whole sendgrid concept of personalizations we can just ignore for now
        'personalizations': [{
            'to': list(map(lambda email: { 'email': email }, to_emails)),
            'subject': subject
        }],
        'from': { 'email': from_email },
        'content': [{
            'type': 'text/html',
            'value': html
        }],
        # https://sendgrid.com/en-us/blog/embedding-images-emails-facts
        'files': files
    }
    # --- send
    sg = SendGridAPIClient(env_get_sendgrid_api_key())
    response = sg.send(payload)
    # --- eval response (ex: print err)
    print(f"[send_email] response: ", response.status_code)