from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import requests
import re
from io import BytesIO
app = Flask(__name__)
CORS(app)

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    post_url = data.get('url')

    if not post_url or 'bsky.app' not in post_url:
        return jsonify({'error': 'Invalid Bluesky URL'}), 400

    try:
        html = requests.get(post_url, timeout=10).text
        match = re.search(r'https://[^\\s\"]+\\.mp4', html)
        if not match:
            return jsonify({'error': 'No video found in the post'}), 404

        video_url = match.group(0)
        video_data = requests.get(video_url, stream=True, timeout=10)
        if video_data.status_code != 200:
            return jsonify({'error': 'Failed to fetch video file'}), 500

        return send_file(BytesIO(video_data.content), mimetype='video/mp4', download_name='video.mp4')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run()
