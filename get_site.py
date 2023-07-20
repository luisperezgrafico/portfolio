import os
import time
import webbrowser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from threading import Thread

# URL of the webpage you want to access
url = "https://luis-portfolio-971e91.webflow.io/"

# Directory where you want to save the files
output_dir = "./"

ignored_urls = [
    "https://fonts.googleapis.com",
    "https://fonts.gstatic.com",
    "https://ajax.googleapis.com/ajax/libs/webfont/1.6.26/webfont.js",
    "https://uploads-ssl.webflow.com/img/favicon.ico",
    "https://uploads-ssl.webflow.com/img/webclip.png",
]

# Send a request to the URL
response = requests.get(url)

# Parse the response content with BeautifulSoup
soup = BeautifulSoup(response.content, "html.parser")

# Find all the link elements that have an href attribute
for link in soup.find_all(["link", "script"]):
    href = link.get("href") if link.get("href") is not None else link.get("src")

    # If the href is not None and not in ignored_urls
    if href and not any(i in href for i in ignored_urls):
        # Join the URL of the webpage with the href
        abs_url = urljoin(url, href)

        # Send a request to the abs_url
        res = requests.get(abs_url)

        # Generate a sanitized local file name by removing query parameters
        parsed_url = urlparse(abs_url)
        filename = parsed_url.path.split("/")[-1]
        sanitized_filename = (
            filename.split(".")[0].split("-")[0] + "." + filename.split(".")[-1]
        )

        # Write the content of the resource to a local file
        local_file = os.path.join(output_dir, sanitized_filename)
        with open(local_file, "w", encoding="utf-8") as f:
            content = res.text

            # If the file is a JS file, replace the specific line
            if local_file.endswith(".js"):
                content = content.replace(':(e.setAttribute(t,n+""),n)', ":n")

            f.write(content)

        # Update the href to point to the local file
        if link.get("href") is not None:
            link["href"] = sanitized_filename
        else:
            link["src"] = sanitized_filename

        # Remove crossorigin and integrity attributes
        if "crossorigin" in link.attrs:
            del link["crossorigin"]
        if "integrity" in link.attrs:
            del link["integrity"]

        # If the file is a CSS file, remove the w-webflow-badge class
        if local_file.endswith(".css"):
            with open(local_file, "r", encoding="utf-8") as f:
                content = f.read()
            content = content.replace(".w-webflow-badge", "")
            with open(local_file, "w", encoding="utf-8") as f:
                f.write(content)

# Save the modified HTML to a local file
with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
    f.write(str(soup.prettify()))


# Start a simple HTTP server in a new thread
def serve_http():
    server = TCPServer(("localhost", 8000), SimpleHTTPRequestHandler)
    server.serve_forever()


thread = Thread(target=serve_http)
thread.daemon = True
thread.start()

# Wait for some time to let the files be written
time.sleep(5)

# Open the webpage in the default web browser
webbrowser.open_new("http://localhost:8000/index.html")

# Wait for some time for the browser to open
time.sleep(5)

# Stop the server
thread.join(timeout=0.1)
