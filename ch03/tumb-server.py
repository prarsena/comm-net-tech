from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

# 32x32 retro/indie Tumblr-era avatar sprites (Base64 BMPs, no external assets needed)
AVATARS = {
    "indie-polaroid": "data:image/bmp;base64,Qk06AgAAAAAAADYAAAAoAAAAIAAAACAAAAABAAQAAAAAAMABAAAAAAAAAAAAAAAAAAAAAAAAAAAAgAAAgAAAAICAAIAAAACAAIAAgIAAAP8AAAD/AP8A//8AAP8AAAD//wD/AP//////AAAAAAAAAAAAAAAAB3d3d3d3d3cAAAAAAAAAB3d3d3d3d3cAAAAHd3d3d3d3d3d3d3cAAAd3d3d3d3d3d3d3dwAAd3d3d3d3d3d3d3d3AAAHd3d3d3d3d3d3d3cAAAB3d3d3d3d3d3d3dwAAAAAAAAB3d3cAAAAAAAAAAAAAAAd3d3cAAAAAAAAHd3d3d3d3d3d3cAAAB3d3d3d3d3d3d3d3cAAHd3d3d3d3d3d3d3dwAAd3d3d3d3d3d3d3d3AAAHd3d3d3d3d3d3d3cAAAB3d3d3d3d3d3d3dwAAAAAAAAAAAAAAAADwAAAAAAAA",
    "soft-grunge-93": "data:image/bmp;base64,Qk06AgAAAAAAADYAAAAoAAAAIAAAACAAAAABAAQAAAAAAMABAAAAAAAAAAAAAAAAAAAAAAAAAAAAgAAAgAAAAICAAIAAAACAAIAAgIAAAP8AAAD/AP8A//8AAP8AAAD//wD/AP//////AAAAAAAAAAAAAAAAd3d3d3d3d3cAAAAAAAAHd3d3d3d3d3cAAAAAAAd3d3d3d3d3cAAAAAAAB3d3d3d3d3cAAAAAAAAd3d3d3d3dwAAAAAAAAB3d3d3d3d3AAAAAAAAAAd3d3d3dwAAAAAAAAAAB3d3d3cAAAAAAAAAAAB3d3d3AAAAAAAAAAAAAHd3dwAAAAAAAAAAAAAAB3d3AAAAAAAAAAAAAAAAHd3cAAAAAAAAAAAAAAAAAB3dwAAAAAAAAAAAAAAAAB3d3AAAAAAAAAAAAAAAAHd3cAAAAAAAAAAAAAAAAB3dwAAAAAAAAAAAAAAAA==",
    "pastel-dystopia": "data:image/bmp;base64,Qk06AgAAAAAAADYAAAAoAAAAIAAAACAAAAABAAQAAAAAAMABAAAAAAAAAAAAAAAAAAAAAAAAAAAAgAAAgAAAAICAAIAAAACAAIAAgIAAAP8AAAD/AP8A//8AAP8AAAD//wD/AP//////AP8A/wD/AP8A/wD/AAAA/wD/AP8A/wD/AP8AAAAA/wD/AP8A/wD/AP8AAAAAAP8A/wD/AP8A/wAAAAAAAP8A/wD/AP8A/wAAAAAAAAD/AP8A/wD/AAAAAAAAAAAP8A/wD/AP8AAAAAAAAAAA/wD/AP8AAAAAAAAAAAAAAP8A/wAAAAAAAAAAAAAAAP8A/wD/AAAAAAAAAAAA/wD/AP8A/wAAAAAAAAAA/wD/AP8A/wD/AAAAAAAAAP8A/wD/AP8A/wAAAAAAAAD/AP8A/wD/AP8A/wAAAAAA/wD/AP8A/wD/AP8AAAAAAP8A/wD/AP8A/wD/AAAA",
    "neon-nostalgia-07": "data:image/bmp;base64,Qk06AgAAAAAAADYAAAAoAAAAIAAAACAAAAABAAQAAAAAAMABAAAAAAAAAAAAAAAAAAAAAAAAAAAAgAAAgAAAAICAAIAAAACAAIAAgIAAAP8AAAD/AP8A//8AAP8AAAD//wD/AP//////d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3",
    "vapor-cassette": "data:image/bmp;base64,Qk06AgAAAAAAADYAAAAoAAAAIAAAACAAAAABAAQAAAAAAMABAAAAAAAAAAAAAAAAAAAAAAAAAAAAgAAAgAAAAICAAIAAAACAAIAAgIAAAP8AAAD/AP8A//8AAP8AAAD//wD/AP//////AAAAAAAAAAAAAAAAB3d3d3d3d3d3d3cAAAAHd3d3d3d3d3d3d3cAAAd3d3d3d3d3d3d3dwAAd3d3d3d3d3d3d3d3AAAHd3d3AAAAAAAHd3cAAAB3d3cAAAAAAAAd3dwAAAB3d3cAAAAAAAAd3dwAAAB3d3cAAAAAAAAd3dwAAAB3d3cAAAAAAAAd3dwAAAHd3d3AAAAAAAHd3cAAAAHd3d3d3d3d3d3d3cAAAAB3d3d3d3d3d3d3dwAAAAAAB3d3d3d3d3cAAAAAAAAAB3d3d3d3d3cAAAAAAAAAAB3d3d3dwAAAAAAAAAAAA==",
}

HTML_PAGE = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>New Post — Tumblr Dashboard</title>
  <style>
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      background-color: #36465d;
      font-family: "Helvetica Neue", HelveticaNeue, Helvetica, Arial, sans-serif;
      color: #444;
      display: flex;
      justify-content: center;
      padding: 40px 15px;
    }}
    .dashboard-container {{
      display: flex;
      gap: 16px;
      width: 580px;
    }}
    .avatar-column {{
      flex-shrink: 0;
    }}
    .blog-avatar {{
      width: 64px;
      height: 64px;
      border-radius: 4px;
      background: #2c3849;
      display: block;
      border: 2px solid #5294c7;
      image-rendering: pixelated;
    }}
    .post-card {{
      background: #ffffff;
      border-radius: 6px;
      flex-grow: 1;
      box-shadow: 0 2px 5px rgba(0,0,0,0.28);
      position: relative;
    }}
    /* Tumblr's iconic speech-bubble triangle pointing to avatar */
    .post-card::before {{
      content: "";
      position: absolute;
      top: 20px;
      left: -9px;
      width: 0;
      height: 0;
      border-top: 9px solid transparent;
      border-bottom: 9px solid transparent;
      border-right: 9px solid #ffffff;
    }}
    .card-header {{
      padding: 16px 20px 10px;
      border-bottom: 1px solid #e7ecf1;
    }}
    .post-type-tag {{
      font-size: 11px;
      font-weight: 700;
      color: #a2b0be;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      margin-bottom: 4px;
    }}
    .card-header h2 {{
      font-size: 19px;
      color: #444;
      font-weight: 600;
    }}
    .privacy-notice {{
      background-color: #f6f8fa;
      border-left: 3px solid #5294c7;
      padding: 10px 14px;
      margin: 14px 20px;
      font-size: 12px;
      color: #617385;
      line-height: 1.45;
    }}
    .privacy-notice strong {{
      color: #36465d;
    }}
    form {{
      padding: 0 20px 20px;
    }}
    .field-group {{
      margin-bottom: 14px;
    }}
    label {{
      display: block;
      font-size: 11px;
      font-weight: 700;
      color: #7b8999;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 5px;
    }}
    select, input[type="text"], textarea {{
      width: 100%;
      border: 1px solid #d5dde5;
      border-radius: 3px;
      padding: 9px 11px;
      font-size: 13px;
      color: #333;
      font-family: inherit;
      background: #fafbfc;
    }}
    select:focus, input[type="text"]:focus, textarea:focus {{
      outline: none;
      border-color: #5294c7;
      background: #fff;
    }}
    textarea {{
      resize: vertical;
      min-height: 85px;
      line-height: 1.5;
    }}
    .action-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 18px;
      padding-top: 14px;
      border-top: 1px solid #edf1f5;
    }}
    .btn-cancel {{
      font-size: 12px;
      color: #8fa0b2;
      text-decoration: none;
      font-weight: 600;
    }}
    .btn-submit {{
      background: #5294c7;
      border: none;
      border-radius: 3px;
      color: #ffffff;
      font-size: 13px;
      font-weight: 700;
      padding: 8px 18px;
      cursor: pointer;
      transition: background 0.15s ease;
    }}
    .btn-submit:hover {{
      background: #417ba8;
    }}
  </style>
  <script>
    const avatarMap = {{
      "indie-polaroid": "{AVATARS['indie-polaroid']}",
      "soft-grunge-93": "{AVATARS['soft-grunge-93']}",
      "pastel-dystopia": "{AVATARS['pastel-dystopia']}",
      "neon-nostalgia-07": "{AVATARS['neon-nostalgia-07']}",
      "vapor-cassette": "{AVATARS['vapor-cassette']}"
    }};
    function onRecipientChange() {{
      const select = document.getElementById("recipient");
      const img = document.getElementById("avatar-preview");
      img.src = avatarMap[select.value] || "";
    }}
  </script>
</head>
<body>
  <div class="dashboard-container">
    <div class="avatar-column">
      <img id="avatar-preview" class="blog-avatar" src="{AVATARS['indie-polaroid']}" alt="Recipient Avatar">
    </div>

    <div class="post-card">
      <div class="card-header">
        <div class="post-type-tag">Fan Mail / Direct Ask</div>
        <h2>Send Private Whisper</h2>
      </div>

      <div class="privacy-notice">
        <strong>🔒 Discreet Dashboard Transmission</strong><br>
        Ask privately. This message will route directly to their inbox and will never appear on their public tumblelog.
      </div>

      <form method="POST" action="/">
        <div class="field-group">
          <label for="recipient">Target Tumblelog</label>
          <select id="recipient" name="recipient" onchange="onRecipientChange()">
            <option value="indie-polaroid">indie-polaroid.tumblr.com (35mm film &amp; vinyl)</option>
            <option value="soft-grunge-93">soft-grunge-93.tumblr.com (Doc Martens &amp; plaid)</option>
            <option value="pastel-dystopia">pastel-dystopia.tumblr.com (pale pink skies)</option>
            <option value="neon-nostalgia-07">neon-nostalgia-07.tumblr.com (glowing CRT screens)</option>
            <option value="vapor-cassette">vapor-cassette.tumblr.com (synthwave aesthetic)</option>
          </select>
        </div>

        <div class="field-group">
          <label for="sender_handle">Your Tumblr URL or Alias</label>
          <input type="text" id="sender_handle" name="sender_handle" placeholder="e.g., starry-night-diaries" required>
        </div>

        <div class="field-group">
          <label for="real_name">Your Real Name (kept PRIVATE. ONLY to be used if YOU agree)</label>
          <input type="text" id="real_name" name="real_name" placeholder="First and Last Name" required>
        </div>

        <div class="field-group">
          <label for="secret_message">Ask / Secret Whisper</label>
          <textarea id="secret_message" name="secret_message" placeholder="Write a confidential question or confession..." required></textarea>
        </div>

        <div class="field-group">
          <label for="tags">Tags (comma separated)</label>
          <input type="text" id="tags" name="tags" placeholder="#aesthetic, #secrets, #dashboard thoughts">
        </div>

        <div class="action-bar">
          <a href="#" class="btn-cancel">Close</a>
          <button type="submit" class="btn-submit">Send Secret Ask</button>
        </div>
      </form>
    </div>
  </div>
</body>
</html>
"""

class TumblrMessengerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
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
        real_name = fields.get("real_name", ["Unspecified"])[0]
        message = fields.get("secret_message", [""])[0]
        tags = fields.get("tags", ["#untagged"])[0]

        ack_page = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Ask Sent!</title>
  <style>
    body {{ background: #36465d; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; display: flex; justify-content: center; padding: 60px 20px; }}
    .card {{ background: #ffffff; padding: 24px 30px; border-radius: 6px; width: 480px; box-shadow: 0 2px 6px rgba(0,0,0,0.3); }}
    h3 {{ color: #5294c7; margin-bottom: 12px; }}
    p {{ font-size: 13px; color: #444; margin-bottom: 6px; }}
    .tag-line {{ color: #8fa0b2; font-size: 12px; margin-top: 10px; font-style: italic; }}
    a {{ display: inline-block; margin-top: 16px; font-size: 12px; color: #5294c7; text-decoration: none; font-weight: 600; }}
  </style>
</head>
<body>
  <div class="card">
    <h3>✔ Ask Dispatched to Inbox</h3>
    <p><strong>To:</strong> {recipient}.tumblr.com</p>
    <p><strong>From:</strong> {sender}</p>
    <p><strong>Confidential Identity:</strong> {real_name}</p>
    <p class="tag-line">Tags: {tags}</p>
    <a href="/">← Return to Dashboard</a>
  </div>
</body>
</html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(ack_page.encode("utf-8"))

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8080), TumblrMessengerHandler)
    print("Tumblr Dashboard messenger running at http://localhost:8080 (Ctrl+C to stop)...")
    server.serve_forever()