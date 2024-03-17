import re
import time
import json
import datetime
import requests
import threading

from ytmusicapi import YTMusic

regex = re.compile(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*")

def get_history():

    # use google takeout with JSON export format
    with open("history.json", "r", encoding="utf-8") as f:
        history = json.load(f)

    seen = []

    for entry in history.copy():
        date = datetime.datetime.fromisoformat(entry["time"][:-1])
        if date.year > 2020:
            history.remove(entry)
            continue

        if "titleUrl" not in entry:
            history.remove(entry)
            continue

        url = entry["titleUrl"]
        if url in seen:
            history.remove(entry)
            continue

        seen.append(url)

    return history

def check_music_available(history, musics):
    while len(history) > 0:
        entry = history.pop(0)
        video_id = regex.search(entry["titleUrl"]).group(1)
        r = requests.get("https://yt.lemnoslife.com/videos?part=music&id=" + video_id)
        available = r.json()["items"][0]["music"]["available"]
        print(entry["title"], "available" if available else "not available")
        if available:
            musics.append(entry)

def main():
    t1 = time.time()

    workers = 10
    history = get_history()
    video_count = len(history)
    musics = []
    
    threads = [threading.Thread(target=check_music_available, args=(history, musics)) for _ in range(workers)]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    t2 = time.time()
    print("Took", t2 - t1, "seconds to check all", video_count, "videos.")
    with open("musics-new.json", "w", encoding="utf-8") as f:
        json.dump(musics, f, indent=2, ensure_ascii=False)

    yt = YTMusic("oauth.json")
    video_ids = [regex.search(entry["titleUrl"]).group(1) for entry in musics]
    pl_id = yt.create_playlist("müzikler", "2013 ve 2016 arasında dinlediğim şarkılar (rial)")
    yt.add_playlist_items(pl_id, video_ids)

if __name__ == "__main__":
    main()
