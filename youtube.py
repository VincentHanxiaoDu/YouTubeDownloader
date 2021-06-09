import requests
import re
import json
import os

# customize UA
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36"

# specify ffmpeg executable
ffmpeg_path = r"C:\ToolSet\ffmpeg-20200727-16c2ed4-win64-static\bin\ffmpeg.exe"


# proxies = {
# 'http': 'socks5h://127.0.0.1:1080', 
# 'https': 'socks5h://127.0.0.1:1080'
# }
# add proxies
proxies = {}

def get(url, headers, proxy=proxies):
    return requests.get(url, headers=headers, proxies=proxy)

def get_adaptive_formats(url):
    req = get(url, headers={"User-Agent": UA})
    text = req.text
    pattern = re.compile(r",\"adaptiveFormats\":(\[.*?\])")
    info_source = re.findall(pattern, text)[0]
    info_source = info_source.replace("\\\"", "\"")
    info_json_str = re.sub(r"codecs=\"(.*?)\"", r"codecs='\1'", info_source)
    info = json.loads(info_json_str)
    return info

def download(url, file):
    file += ".mp4"
    info_list = get_adaptive_formats(url)
    info_video = None
    info_audio = None
    i = 0
    # You can customize video and audio streams here, the loop chooses the first appearance.
    while info_video is None or info_audio is None:
        info = info_list[i]
        if info["mimeType"].find("video/mp4") != -1 and info_video is None:
            info_video = info
        if info["mimeType"].find("audio/mp4") != -1 and info_audio is None:
            info_audio = info
        i += 1
    video_file = file + ".vid"
    audio_file = file + ".aud"
    download_content(info_video, video_file)
    download_content(info_audio, audio_file)
    merge(video_file, audio_file, file)

def download_content(info, file):
    vid_url = info["url"].replace(r"\u0026", "&")
    length = int(info["contentLength"])
    buffer_size = 10000000
    current = 0
    if os.path.isfile(file):
        raise Exception("files exists: " + file)
    with open(file, "ab+") as f:
        while current < length:
            if (length-current) < buffer_size:
                buffer_range = f"&range={current}-{length-1}"
                current = length
            else:
                buffer_range = f"&range={current}-{current+buffer_size-1}"
                current += buffer_size
            buffer_url = vid_url + buffer_range
            buffer = get(buffer_url, headers={"User-Agent": UA}).content
            f.write(buffer)

def merge(video_file, audio_file, output_file):
    print("Merging video and audio...")
    cmd = f"{ffmpeg_path} -i \"{video_file}\" -i \"{audio_file}\" -c:v copy -c:a aac \"{output_file}\""
    os.system(cmd)
    os.remove(video_file)
    os.remove(audio_file)


def get_list_info(url):
    req = get(url, headers={"User-Agent": UA})
    text = req.text
    pattern = re.compile(r"\"playlistVideoRenderer\":\{\"videoId\":\"(.*?)\"")
    info = re.findall(pattern, text)
    return(info)

def download_playlist(url, directory, filename, index_range=""):
    vid_urls = get_list_info(url)
    BASE_URL = r"https://www.youtube.com/watch?v="
    length = len(vid_urls)
    lower = 0
    upper = length - 1
    if index_range != "":
        s = index_range.split("-")
        if s[0] != "" and int(s[0]) > 0:
            lower = int(s[0]) - 1
        if s[1] != "" and int(s[1]) < length:
            upper = int(s[1]) - 1
    i = lower
    while i <= upper:
        index = i + 1
        u = BASE_URL + vid_urls[i]
        print(f"downloading vid {index}: {u}")
        download(u, os.path.join(directory, f"{filename}_{index}"))
        i += 1

def main():
    islist = input("list?(y/n)")
    if (islist == "y"):
        # e.g. range = "1-3", this downloads the first three videos of the playlist
        download_playlist(input("url: "), input("directory: "), input("filename:"), input("range:"))
    elif (islist == "n"):
        download(input("url: "), input("file path: "))
    else:
        print("please type (y/n)")
        main()

if __name__ == "__main__":
    main()
