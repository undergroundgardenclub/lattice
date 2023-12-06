import base64
from io import BytesIO
from typing import List
from pydash import snake_case


def fill_email_template_html_tasks_summary(tasks: List[dict]) -> (str, List):
    # SETUP
    # --- open
    email_html = "<html><body>"
    # --- compile files for sendgrid, using consistent cid
    # email_files = []

    for task in tasks:
        # --- header
        email_html += f"<h2><u>TASK: {task['taskName']}</u></h2>"

        # --- actions bullet list
        if (len(task['taskActions']) > 0):
            email_html += "<small>What was Done:</small><ul>"
            for action in task['taskActions']:
                email_html += f"<li>{action}</li>"
            email_html += "</ul>"

        # --- thoughts bullet list
        if (len(task['taskThoughts']) > 0):
            email_html += "<small>Observations/Thoughts:</small><ul>"
            for thought in task['taskThoughts']:
                email_html += f"<li>{thought}</li>"
            email_html += "</ul>"

        # --- image
        if task['image'] is not None:
            # attachment image data and cid reference
            buffered = BytesIO(task['image'])
            image_base64_encoded = base64.b64encode(buffered.getvalue()).decode('utf-8')
            # CID METHOD DOES NOT WORK, DOING BASE64 ENCODING INLINE
            # email_files.append({
            #     'filename': f"{snake_case(task['taskName'])}.jpg",
            #     'contentType': 'image/jpeg',
            #     'cid': snake_case(task['taskName']),
            #     'content': image_base64_encoded
            # })
            # email_html += f"<img src='cid:{snake_case(task['taskName'])}' />"
            email_html += f"<img src='data:image/jpeg;base64,{image_base64_encoded}' />"

        # --- gap
        email_html += "<br/>"
    # --- close
    email_html += "</body></html>"

    # RETURN tuple of html and the file structure
    return email_html #, email_files