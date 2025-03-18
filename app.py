from flask import Flask, request, jsonify
import requests

# from youtube_transcript_api import YouTubeTranscriptApi
# import whisper
import yt_dlp
import xml.etree.ElementTree as ET


app = Flask(__name__)


def progress_hook(d) -> None:
    # print(d)
    pass


def download_info(url, ydl):
    info = ydl.extract_info(url=url, download=False)
    return info


# def generate_transcript_list(audio_path) -> list[dict]:
#     model = whisper.load_model(
#         "small"
#     )  # 모델 크기 선택 가능: "tiny", "small", "medium", "large"
#     result = model.transcribe(audio_path, fp16=False)  # CPU에서 실행 시 FP16 비활성화

#     transcript_list = []
#     for segment in result["segments"]:
#         start = segment["start"]
#         end = segment["end"]
#         text = segment["text"]

#         # 타임스탬프 (hh:mm:ss 형식)
#         start_time = f"{int(start // 3600):02}:{int((start % 3600) // 60):02}:{int(start % 60):02}"
#         end_time = (
#             f"{int(end // 3600):02}:{int((end % 3600) // 60):02}:{int(end % 60):02}"
#         )
#         time_range = f"{start_time} - {end_time}"
#         transcript_list.append({"time": time_range, "text": text})

#     return transcript_list


def fetch_transcript(transcript_url, ydl):
    response = ydl.urlopen(transcript_url).read().decode("utf-8")
    return response


def parse_srv1(xml_string):
    root = ET.fromstring(xml_string)  # XML 파싱
    transcript_data = []

    # <text> 태그를 찾아서 파싱
    for text_elem in root.findall("text"):
        start = float(text_elem.get("start", 0))  # 시작 시간
        duration = float(text_elem.get("dur", 0))  # 지속 시간
        text_content = text_elem.text if text_elem.text else ""  # 텍스트 내용

        end = start + duration  # 종료 시간 계산

        # 시간 형식을 hh:mm:ss로 변환
        def format_time(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            sec = int(seconds % 60)
            return f"{hours:02}:{minutes:02}:{sec:02}"

        transcript_data.append(
            {
                "time": f"{format_time(start)} - {format_time(end)}",
                "text": text_content.strip(),  # 불필요한 공백 제거
            }
        )

    return transcript_data  # JSON 형태의 리스트 반환


def parse_srv2(xml_string):
    # not implemented
    return []


def parse_transcript(transcript, ext):
    if ext == "srv1":
        return parse_srv1(transcript)
    elif ext == "srv2":
        return parse_srv2(transcript)
    else:
        return transcript


@app.route("/get_transcript", methods=["GET"])
def get_transcript():
    url = request.args.get("url", ydl)

    if not url:
        return jsonify({"error": "Missing url parameter"}), 400
    try:
        info = download_info(url)
        transcript_info = info["automatic_captions"]["ko"]
        transcript_urls = {item["ext"]: item["url"] for item in transcript_info}

        priority = ["srv1", "srv2"]  # will be added
        parsing_function = None
        for ext in priority:
            if ext in transcript_urls:
                transcript_url = transcript_urls[ext]
                break

        ydl_opts = {
            "format": "bestaudio/best",
            "concurrent_fragment_downloads": 10,
            "retry_sleep_functions": {"fragment": lambda n: n + 1},
            "progress_hooks": [progress_hook],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            transcript = fetch_transcript(transcript_url, ydl)
            transcript = parse_transcript(transcript, ext)
            return jsonify({"transcript": transcript})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=5000)  # 로컬 서버 실행
