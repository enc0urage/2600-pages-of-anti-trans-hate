from html import escape
from glob import glob
from pathlib import Path
import json
import sys

from slugify import slugify
from dateutil.parser import parse as parse_date


HTML_HEADER = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>the emails - 2600 pages of hate</title>
</head>
<h1>the emails - 2600 pages of hate</h1>
<body>
<ul>
"""

HTML_FOOTER = r"""
</ul>
</body>
</html>
"""


def convert_html(fileinfo, output_directory):
    with open(Path(output_directory, "txt", f"{fileinfo[1]}.txt")) as f:
        data = f.read()

    subject = fileinfo[0]
    if len(subject) == 0:
        subject = fileinfo[1]

    with open(Path(output_directory, "html", f"{fileinfo[1]}.html"), "w") as f:
        f.write(
            f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{escape(subject)}</title>
<style type="text/css">
pre {{
  white-space: pre-wrap;
  word-break: keep-all;
}}
</style>
</head>
<body>
<pre>
{escape(data)}
</pre>
</body>
</html>
"""
        )


def fix_file(name):
    with open(name) as f:
        data = f.read()
    file = open(name, "w")
    file.seek(0)
    file.truncate()

    past_subject = False

    for l in data.split("\n"):
        if past_subject:
            print(l, file=file)
            continue
        for a in ["Sent:", "To:", "Cc:", "Bcc:"]:
            if a in l:
                l = l.replace(a, f"\n{a}")
        if "Subject:" in l:
            l = l.replace("Subject:", "\nSubject:")
            past_subject = True
        print(l, file=file)

    file.close()


def parse_file(filename):
    file = open(filename)
    data = {
        "file": filename,
        "from": "",
        "sent": "",
        "to": "",
        "cc": "",
        "bcc": "",
        "subject": "",
        "body": "",
    }

    state = "from"

    for l in file:
        if state == "body":
            data["body"] += l
            continue
        elif l.startswith("Sent:"):
            state = "sent"
        elif l.startswith("To:"):
            state = "to"
        elif l.startswith("Cc:"):
            state = "cc"
        elif l.startswith("Bcc:"):
            state = "bcc"
        elif l.startswith("Subject:"):
            data["subject"] = l[8:].strip()
            if len(data["subject"]) == 0:
                data["subject"] = next(file).strip()
            state = "body"
            continue

        data[state] += l

    file.close()

    for a in ["from", "sent", "to", "cc", "bcc"]:
        if len(data[a]) == 0:
            continue
        data[a] = data[a][(len(a) + 1) :].strip(" \n").replace("\n", " ")

    if len(data["sent"]) > 0:
        data["sent"] = parse_date(data["sent"], fuzzy=True).strftime("%Y%m%d")

    new_filename = []
    for a in ["sent", "from", "to", "subject"]:
        if len(data[a]) == 0:
            continue
        new_filename.append(slugify(data[a].split(" <", 1)[0]))
    new_filename = "_".join(new_filename)

    if len(new_filename) == 0:
        new_filename += slugify(data["body"].replace("\n", ""))

    if len(new_filename) > 246:
        new_filename = new_filename[:246]
    old_filename = Path(data["file"]).name.rsplit(".txt")[0]
    new_filename = Path(Path(filename).parent, f"{old_filename}_{new_filename}.txt")

    Path(filename).rename(new_filename)

    return data["subject"], new_filename.name[:-4]


def parse_files(output_directory, h):
    h.write(HTML_HEADER)
    files = []
    for name in glob(f"{output_directory}/txt/*.txt"):
        fix_file(name)
        files.append(parse_file(name))
    for file in sorted(files, key=lambda x: int(x[1].split("_", 1)[0])):
        convert_html(file, output_directory)
        h.write(
            f"""
        <li>
        <a href="html/{file[1]}.html" target="_blank">
        {file[1].replace("_", " ")}
        </a>
        </li>
        """
        )
    h.write(HTML_FOOTER)


def split_files(input_file, output_directory):
    i = 0

    input_file = open(input_file)
    output_file = None

    Path(output_directory, "txt").mkdir(parents=True)
    Path(output_directory, "html").mkdir(parents=True)

    for line in input_file:
        if line.startswith("From:") and output_file is not None:
            output_file.close()
            i += 1
            output_file = Path(output_directory, "txt", f"{i}.txt").open("w")
        elif output_file is None:
            output_file = Path(output_directory, "txt", f"{i}.txt").open("w")
        output_file.write(line)

    output_file.close()
    input_file.close()


def cli():
    input_file = sys.argv[1]
    output_directory = sys.argv[2]

    html_output = Path(output_directory, "index.html").open("w")

    split_files(input_file, output_directory)
    parse_files(Path(output_directory), html_output)

    html_output.close()
