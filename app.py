from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import whisper
import yt_dlp

app = Flask(__name__)


def download_audio(url):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "./audio.mp4",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        error_code = ydl.download(url)


def generate_transcript_list(audio_path) -> list[dict]:
    model = whisper.load_model("small")  # 모델 크기 선택 가능: "tiny", "small", "medium", "large"
    result = model.transcribe(audio_path, fp16=False)  # CPU에서 실행 시 FP16 비활성화

    transcript_list = []
    for segment in result["segments"]:
        start = segment["start"]
        end = segment["end"]
        text = segment["text"]

        # 타임스탬프 (hh:mm:ss 형식)
        start_time = f"{int(start // 3600):02}:{int((start % 3600) // 60):02}:{int(start % 60):02}"
        end_time = f"{int(end // 3600):02}:{int((end % 3600) // 60):02}:{int(end % 60):02}"
        time_range = f"{start_time} - {end_time}"
        transcript_list.append({"time": time_range, "text": text})

    return transcript_list


@app.route("/")
def index():
    video = "https://www.youtube.com/watch?v=x7X9w_GIm1s"
    download_audio(video)

    transcript = generate_transcript_list("./audio.mp4")
    return jsonify({"transcript": transcript})


@app.route("/get_transcript", methods=["GET"])
def get_transcript():
    video_id = request.args.get("video_id")

    if not video_id:
        return jsonify({"error": "Missing video_id parameter"}), 400

    try:
        transcript = YouTubeTranscriptApi.get_transcript(
            video_id, languages=["ko", "en"]
        )
        modified_transcript = [
            {'start': int(item['start']), 'text': item['text']}
            for item in transcript
        ]
        return jsonify(modified_transcript)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=5000)  # 로컬 서버 실행
