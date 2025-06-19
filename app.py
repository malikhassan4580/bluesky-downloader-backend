from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import requests
import re
from io import BytesIO

app = Flask(__name__)
CORS(app)

@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        post_url = data.get('url')

        if not post_url or 'bsky.app' not in post_url:
            return jsonify({'error': 'Invalid Bluesky URL'}), 400

        # Fetch post HTML
        html = requests.get(post_url, timeout=10).text

        # Look for .mp4 or .m3u8 URLs
        mp4_match = re.search(r'https://[^\\s"]+\\.mp4', html)
        m3u8_match = re.search(r'https://[^\\s"]+\\.m3u8', html)

        if mp4_match:
            video_url = mp4_match.group(0)
        elif m3u8_match:
            return jsonify({
                'error': 'This post contains a streaming video (.m3u8), which is not supported for direct download.'
            }), 415
        else:
            return jsonify({
                'error': 'No downloadable video (.mp4) found in the post.'
            }), 404

        # Download the video
        video_data = requests.get(video_url, stream=True, timeout=10)
        if video_data.status_code != 200:
            return jsonify({'error': 'Failed to fetch video file'}), 500

        return send_file(
            BytesIO(video_data.content),
            mimetype='video/mp4',
            download_name='bluesky_video.mp4'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run()
