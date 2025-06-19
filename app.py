from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import requests
import re
from io import BytesIO

app = Flask(__name__)
CORS(app)

# Extract repo and rkey from the post URL
def parse_bsky_url(url):
    try:
        match = re.search(r"bsky\.app/profile/([^/]+)/post/([^/?#]+)", url)
        return match.group(1), match.group(2)
    except:
        return None, None

@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        post_url = data.get('url')

        if not post_url or 'bsky.app' not in post_url:
            return jsonify({'error': 'Invalid Bluesky URL'}), 400

        repo, rkey = parse_bsky_url(post_url)
        if not repo or not rkey:
            return jsonify({'error': 'Could not parse post URL'}), 400

        # Fetch post metadata from Bluesky public API
        api_url = "https://public.api.bsky.app/xrpc/com.atproto.repo.getRecord"
        params = {
            "collection": "app.bsky.feed.post",
            "repo": repo,
            "rkey": rkey
        }

        response = requests.get(api_url, params=params, timeout=10)
        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch post metadata'}), 500

        record = response.json().get('value', {})
        embeds = record.get('embed', {}).get('images') or record.get('embed', {}).get('media', {}).get('images')

        if not embeds or not embeds[0].get('fullsize'): 
            return jsonify({'error': 'No video found in the post'}), 404

        # Fetch the image/video content
        video_url = embeds[0]['fullsize']
        video_data = requests.get(video_url, stream=True, timeout=10)
        if video_data.status_code != 200:
            return jsonify({'error': 'Failed to fetch video'}), 500

        return send_file(BytesIO(video_data.content), mimetype='video/mp4', download_name='bluesky_video.mp4')

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run()
