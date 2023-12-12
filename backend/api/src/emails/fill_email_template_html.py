import base64
from io import BytesIO
from typing import List
from pydash import snake_case
from vision.cv import encoded_frame_to_base64


def fill_email_template_html_tasks_summary(tasks: List[dict]) -> (str, List):
    print(f"[fill_email_template_html_tasks_summary] {len(tasks)} tasks to HTML")
    # SETUP
    # --- open (adding CSS for tables so we can do a series of images)
    email_html = "<html><head><style>table {width: 100%;}td {text-align: center;}img {display: inline-block;max-width: 100%;height: auto;}</style></head><body>"
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
        if hasattr(task.get("images"), '__iter__'):
            # --- start table
            email_html += "<table cellspacing='0' cellpadding='0'><tr>"
            # --- add image <td>
            for image in task.get("images"):
                email_html += f"<td><img src='data:image/jpeg;base64,{encoded_frame_to_base64(image)}' /></td>"
            # --- close table
            email_html += "</tr></table>"

        # --- gap
        email_html += "<br/>"
    # --- close
    email_html += "</body></html>"

    # RETURN tuple of html and the file structure
    return email_html #, email_files