import base64
from io import BytesIO
from typing import List
from pydash import snake_case
from vision.cv import encoded_frame_to_base64


def fill_email_template_html_tasks_summary(tasks: List[dict]) -> (str, List):
    print(f"[fill_email_template_html_tasks_summary] {len(tasks)} tasks to HTML")
    # SETUP
    # --- open
    email_html = "<html><body>"
    # --- compile files for sendgrid, using consistent cid
    # email_files = []

    for task in tasks:
        # --- header
        email_html += f"<h4><u>TASK: {task.get('taskName')}</u></h4>"
        email_html += f"<p>{task.get('taskSummary')}"
        # --- observation (TODO: trying to make this an AI reflective statement as 3rd party)
        # --- actions bullet list
        if len(task.get("taskActions", [])) > 0:
            email_html += " Actions: </p><ul>"
            for action in task.get('taskActions'):
                email_html += f"<li>{action}</li>"
            email_html += "</ul>"
        # --- image (could do attachments + cid reference, or base64 inline)
        if task.get("image") is not None:
            image_base64_encoded = encoded_frame_to_base64(task.get("image"))
            email_html += f"<img src='data:image/jpeg;base64,{image_base64_encoded}' />"
            # CID METHOD DOES NOT WORK, DOING BASE64 ENCODING INLINE
            # email_files.append({
            #     'filename': f"{snake_case(task['taskName'])}.jpg",
            #     'contentType': 'image/jpeg',
            #     'cid': snake_case(task['taskName']),
            #     'content': image_base64_encoded
            # })
            # email_html += f"<img src='cid:{snake_case(task['taskName'])}' />"


        # --- gap
        email_html += "<br/>"
    # --- close
    email_html += "</body></html>"

    # RETURN tuple of html and the file structure
    return email_html #, email_files