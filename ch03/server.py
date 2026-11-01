from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import os
import mimetypes

HTML_PAGE = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>:: [xXx_MyPrivateSpace_xXx] :: Direct Connect Instant Messenger ::</title>
  <style>
    body {
      background-color: #000314;
      background-image: radial-gradient(#1a2754 15%, transparent 16%);
      background-size: 8px 8px;
      font-family: "Comic Sans MS", "Chalkboard SE", "Verdana", sans-serif;
      color: #00ff66;
      margin: 20px;
    }
    .wrapper {
      width: 580px;
      margin: 0 auto;
      background: #0d1224;
      border: 3px ridge #ff007f;
      box-shadow: 0 0 15px #ff007f, inset 0 0 10px #00e5ff;
      padding: 15px;
    }
    .header {
      background: linear-gradient(180deg, #ff007f 0%, #7a003c 100%);
      color: #ffffff;
      padding: 6px 10px;
      font-weight: bold;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 1px;
      display: flex;
      justify-content: space-between;
      border: 1px solid #ffffff;
    }
    .marquee-bar {
      background: #000;
      color: #ffea00;
      font-size: 11px;
      padding: 3px;
      margin: 8px 0;
      border: 1px dashed #ffea00;
      font-family: "Courier New", monospace;
    }
    .security-badge {
      background: #002b11;
      border: 2px dashed #00ff66;
      color: #a3ffcc;
      padding: 8px;
      font-size: 11px;
      margin-bottom: 15px;
      line-height: 1.4;
    }
    .security-badge strong {
      color: #00ff66;
      text-transform: uppercase;
    }
    .buddy-row {
      display: flex;
      gap: 12px;
      align-items: center;
      margin-bottom: 10px;
      font-size: 12px;
      color: #fff;
    }
    /* Set avatar dimensions to 32x32 pixels */
    .buddy-icon {
      width: 96px;
      height: 96px;
      border: 2px solid #ff007f;
      object-fit: cover;
      image-rendering: pixelated;
      background: #000;
    }
    label {
      display: block;
      font-size: 12px;
      font-weight: bold;
      color: #00e5ff;
      margin-bottom: 4px;
      text-shadow: 1px 1px 2px #000;
    }
    select, textarea, input[type="text"] {
      width: 100%;
      background: #000;
      border: 2px inset #ff007f;
      color: #00ff66;
      font-family: "Courier New", monospace;
      font-size: 13px;
      box-sizing: border-box;
      padding: 6px;
      margin-bottom: 12px;
    }
    select option {
      background: #0b0f19;
      color: #fff;
    }
    .btn-submit {
      width: 100%;
      background: linear-gradient(180deg, #00ff66 0%, #008f39 100%);
      color: #000;
      font-family: "Comic Sans MS", sans-serif;
      font-weight: bold;
      font-size: 14px;
      padding: 10px;
      border: 2px outset #a3ffcc;
      cursor: pointer;
      text-transform: uppercase;
    }
    .btn-submit:hover {
      background: linear-gradient(180deg, #ff007f 0%, #b30059 100%);
      color: #fff;
      border-color: #ff99cc;
    }
    .footer-note {
      font-size: 10px;
      color: #8892b0;
      text-align: center;
      margin-top: 10px;
    }
  </style>
  <script>
    // Map screen names directly to local image endpoints
    const buddyIcons = {
      "xX_Tom_MySpace_Xx": "/avatars/tom.png",
      "Sk8r_Boi_2004": "/avatars/sk8r.png",
      "~*Gl1tt3r_G1rl*~": "/avatars/glitterr.png",
      "rawr_XD_goth": "/avatars/goth.png",
      "SarahxStarrr": "/avatars/glitter.png",
      "n30_h4ck3r_2k": "/avatars/hackerr.png"
    };
    function updateAvatar() {
      const select = document.getElementById("recipient-select");
      const icon = document.getElementById("active-icon");
      icon.src = buddyIcons[select.value] || "";
    }
  </script>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <span>MyPrivateSpace Instant Messenger v2.4</span>
      <span>[ _ □ X ]</span>
    </div>

    <div class="marquee-bar">
      *** PRIVATE CONNECTION ACTIVE :: END-TO-END SECRET TRANSMISSION SYSTEM ***
    </div>

    <div class="security-badge">
      🔒 <strong>GUARANTEED PRIVATE &amp; ENCRYPTED SESSION</strong><br>
      Your connection is protected by our proprietary <em>UltraSafe™ Stealth Socket Layer</em>. 
      No third party, network snooper, or wiretapping tool can inspect your private messages or identity. Speak freely.
    </div>

    <form method="POST" action="/">
      <label for="recipient-select">Choose Private Recipient (Top 5 Buddies):</label>
      <div class="buddy-row">
        <img id="active-icon" class="buddy-icon" src="/avatars/tom.png" alt="Avatar">
        <select id="recipient-select" name="recipient" onchange="updateAvatar()">
          <option value="xX_Tom_MySpace_Xx">xX_Tom_MySpace_Xx (Your Friend Since Day 1)</option>
          <option value="Sk8r_Boi_2004">Sk8r_Boi_2004 (Away - At The Skatepark)</option>
          <option value="~*Gl1tt3r_G1rl*~">~*Gl1tt3r_G1rl*~ (Online - Listening to MCR)</option>
          <option value="rawr_XD_goth">rawr_XD_goth (Busy - Writing Poetry)</option>
          <option value="SarahxStarrr">SarahxStarrr (Online - Here or there)</option>
          <option value="n30_h4ck3r_2k">n30_h4ck3r_2k (Offline - Lurking)</option>
        </select>
      </div>

      <label for="user-handle">Your Secret Alias:</label>
      <input type="text" id="user-handle" name="sender_handle" placeholder="e.g., anonymous_surfer99" required>

      <label for="real-name">Your Real Name (kept PRIVATE. ONLY to be used if YOU agree):</label>
      <input type="text" id="real-name" name="real_name" placeholder="e.g., Firstname Lastname" required>

      <label for="secret-msg">Confidential Transmission:</label>
      <textarea id="secret-msg" name="secret_message" rows="4" placeholder="Enter your confidential secret message here..." required></textarea>

      <button type="submit" class="btn-submit">⚡ Send Super-Secret Private Message ⚡</button>
    </form>

    <div class="footer-note">
      Best viewed in Netscape Navigator 6.0 or Internet Explorer 5.5 @ 800x600 resolution.
    </div>
  </div>
</body>
</html>
"""

class RetroMessengerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Serve local files from the /avatars/ route
        if self.path.startswith("/avatars/"):
            file_name = os.path.basename(self.path)
            file_path = os.path.join(os.getcwd(), "avatars", file_name)

            if os.path.isfile(file_path):
                content_type, _ = mimetypes.guess_type(file_path)
                self.send_response(200)
                self.send_header("Content-Type", content_type or "application/octet-stream")
                self.end_headers()
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_error(404, "File Not Found")
                return

        # Default route: serve index page
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML_PAGE.encode("utf-8"))

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(length).decode("utf-8")
        
        fields = urllib.parse.parse_qs(post_data)
        recipient = fields.get("recipient", ["Unknown"])[0]
        sender = fields.get("sender_handle", ["Anonymous"])[0]
        real_name = fields.get("real_name", ["Not Provided"])[0]

        ack_page = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Message Dispatched</title>
  <style>
    body {{ background: #000314; color: #00ff66; font-family: monospace; padding: 40px; text-align: center; }}
    .box {{ border: 2px ridge #ff007f; padding: 20px; display: inline-block; background: #0d1224; text-align: left; }}
    a {{ color: #00e5ff; text-decoration: none; }}
  </style>
</head>
<body>
  <div class="box">
    <h2>✔ TRANSMISSION DELIVERED IN TOTAL PRIVACY</h2>
    <p><strong>Alias:</strong> {sender}</p>
    <p><strong>Real Name (Kept Ultra Secret):</strong> {real_name}</p>
    <p><strong>To:</strong> {recipient}</p>
    <p><strong>Status:</strong> Dispatched across cleartext HTTP socket!</p>
    <br>
    <a href="/">[ Send Another Private Dispatch ]</a>
  </div>
</body>
</html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(ack_page.encode("utf-8"))

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8080), RetroMessengerHandler)
    print("Retro Messenger online at http://localhost:8080 (Press Ctrl+C to exit)...")
    server.serve_forever()