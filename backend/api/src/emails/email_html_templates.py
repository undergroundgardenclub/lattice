from typing import List
from vision.cv import encoded_frame_jpg_to_base64


# reusable html <head/> code for layout/styling (esp. inline images)
HTML_HEAD = "<head><style>table {width: 100%;}td {text-align: center;}img {display: inline-block;max-width: 100%;height: auto;}</style></head>"


def html_template_step_section(header_text: str, summary_text: str, video_url: str, attributes_list: List[str], image_frame_jpgs: List[bytes]) -> str:
    print(f"[html_template_step_section] start")
    html = "<div>"
    # --- header
    html = f"<h3>STEP: {header_text}</h3>"
    # --- video/summary
    html += f"<p>[<a href='{video_url}'>Video</a>] {summary_text}</p>"
    # --- explicit attributes
    if attributes_list != None and len(attributes_list) > 0:
        html += "<ul>"
    for attribute in attributes_list:
        html += f"<li>{attribute}</li>"
    if attributes_list != None and len(attributes_list) > 0:
        html += "</ul>"
    # --- images
    if hasattr(image_frame_jpgs, '__iter__'):
        # --- start table
        html += "<table cellspacing='0' cellpadding='0'><tr>"
        # --- add image <td>
        for image in image_frame_jpgs:
            html += f"<td><img src='data:image/jpeg;base64,{encoded_frame_jpg_to_base64(image)}' /></td>"
        # --- close table
        html += "</tr></table>"
    # --- gap
    html += "<div/>"
    # --- return
    return html

def html_template_steps_body(steps_html: List[str], title: str = None) -> str:
    print(f"[html_template_steps_body] start")
    html = f"<html>{HTML_HEAD}<body>"
    # --- header
    html = f"<h1><u>{title or 'Summary'}</u></h1>"
    html += "<main>"
    # --- steps
    for step_html in steps_html:
        html += step_html
    # --- gap
    html += "</main>"
    html += "</body></html>"
    # --- return
    return html

