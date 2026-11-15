from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Code Forge AI Platform</title>
    <style>
        body {
            background: #090d16;
            color: #f1f5f9;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            padding: 24px;
            box-sizing: border-box;
        }
        .container {
            background: #131b2e;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 18px;
            padding: 44px 36px;
            max-width: 620px;
            text-align: center;
            box-shadow: 0 20px 45px rgba(0, 0, 0, 0.6);
        }
        .badge {
            background: rgba(0, 255, 135, 0.1);
            color: #00ff87;
            border: 1px solid rgba(0, 255, 135, 0.3);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            letter-spacing: 0.5px;
            display: inline-block;
            margin-bottom: 20px;
        }
        h1 {
            font-size: 2rem;
            font-weight: 800;
            margin: 0 0 10px 0;
            color: #f8fafc;
        }
        .tagline {
            color: #94a3b8;
            font-size: 0.95rem;
            margin-bottom: 24px;
        }
        .info-card {
            background: #0a0e18;
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 18px;
            text-align: left;
            margin-bottom: 26px;
            font-size: 0.9rem;
            line-height: 1.6;
            color: #cbd5e1;
        }
        .info-card strong {
            color: #00ff87;
        }
        .btn-launch {
            display: inline-block;
            background: linear-gradient(135deg, #00ff87, #00e5ff);
            color: #090d16;
            font-weight: 700;
            padding: 12px 28px;
            border-radius: 10px;
            text-decoration: none;
            font-size: 0.95rem;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .btn-launch:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 255, 135, 0.3);
        }
        .footer {
            margin-top: 32px;
            padding-top: 18px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            font-size: 0.82rem;
            color: #64748b;
        }
        .footer strong {
            color: #00ff87;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="badge">PLATFORM ARCHITECTURE NOTICE</div>
        <h1>⚡ Code Forge AI Platform</h1>
        <div class="tagline">Search. Think. Code. Explore.</div>
        
        <div class="info-card">
            <strong>Deployment Environment:</strong><br/>
            Code Forge AI uses full stateful WebSockets, an isolated Python terminal runner, and real-time financial Plotly dashboards built natively with Streamlit.<br/><br/>
            Because Vercel runs stateless serverless functions, the production Streamlit web UI is designed for <b>Streamlit Community Cloud</b> or <b>Docker / Render</b> with zero configuration.
        </div>

        <a href="https://github.com/rishithreddyyy" target="_blank" class="btn-launch">
            View on GitHub &amp; Deployment Docs &rarr;
        </a>

        <div class="footer">
            Developed &amp; Designed by <strong>Rishith Reddy Serikar</strong><br/>
            &copy; 2026 Code Forge AI. All Rights Reserved.
        </div>
    </div>
</body>
</html>"""
        self.wfile.write(html.encode('utf-8'))
        return
