import json
from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi

app = Flask(__name__)


@app.route("/get_transcript", methods=["GET"])
def get_transcript():
    video_id = request.args.get("video_id")

    if not video_id:
        return jsonify({"error": "Missing video_id parameter"}), 400

    try:
        transcript = YouTubeTranscriptApi.get_transcript(
            video_id, languages=["ko", "en"]
        )
        return jsonify(transcript)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=5000)  # 로컬 서버 실행
