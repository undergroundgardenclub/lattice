import base64
from io import BytesIO
from typing import List
from pydash import snake_case
from vision.cv import encoded_frame_to_base64


def fill_email_template_html_tasks_summary(tasks: List[dict]) -> (str, List):
    # SETUP
    # --- open
    email_html = "<html><body>"
    # --- compile files for sendgrid, using consistent cid
    # email_files = []

    for task in tasks:
        has_summary = task['taskSummary']
        # has_observation = task['taskObservation'] != None
        has_actions = len(task['taskActions']) > 0
        # --- header
        email_html += f"<h4><u>TASK: {task['taskName']}</u></h4>"
        # --- thoughts paragraph
        email_html += f"<p>{task['taskSummary']}"
        # # --- observation (TODO: trying to make this an AI reflective statement as 3rd party)
        # email_html += f" {task['taskObservation']}"
        # --- actions bullet list
        if has_actions:
            email_html += " Actions: </p><ul>"
            for action in task['taskActions']:
                email_html += f"<li>{action}</li>"
            email_html += "</ul>"
        # --- image
        if task['image'] is not None:
            # attachment image data and cid reference
            image_base64_encoded = encoded_frame_to_base64(task['image'])
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