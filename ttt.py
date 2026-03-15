import yt_dlp

def download_audio(url: str, output_dir: str = "."):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{output_dir}/%(title)s.%(ext)s",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        print(f"Downloading audio: {info['title']}")
        ydl.download([url])
        print("Download complete!")

if __name__ == "__main__":
    url = input("Enter YouTube URL: ")
    download_audio(url)