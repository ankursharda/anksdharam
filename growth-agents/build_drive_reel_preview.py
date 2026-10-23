#!/usr/bin/env python3
"""Build one preview Reel from Google Drive assets. Never publishes."""
import json, os, random, re, subprocess, tempfile
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

FOLDERS={"music":"1UsrcZLZQGyEclDwzd3yPQDSg9G6ihzCg","images":"1fAWzh16reJb5ttg9wHfMwmPCWbVJkghY"}
API="https://www.googleapis.com/drive/v3/files"

def get_token():
    data=urlencode({"client_id":os.environ["GOOGLE_DRIVE_CLIENT_ID"],"client_secret":os.environ["GOOGLE_DRIVE_CLIENT_SECRET"],"refresh_token":os.environ["GOOGLE_DRIVE_REFRESH_TOKEN"],"grant_type":"refresh_token"}).encode()
    with urlopen(Request("https://oauth2.googleapis.com/token",data=data),timeout=30) as r:
        return json.load(r)["access_token"]

def request(url,token):
    return urlopen(Request(url,headers={"Authorization":"Bearer "+token}),timeout=120)

def files(folder,token):
    result=[]
    page=None
    while True:
        q={"q":f"'{folder}' in parents and trashed = false","fields":"nextPageToken,files(id,name,mimeType,size)","page_size":100}
        if page:q["page_token"]=page
        with request(API+"?"+urlencode(q),token) as r: data=json.load(r)
        result.extend(data.get("files",[]))
        page=data.get("nextPageToken")
        if not page:break
    return result

# Match only identifiable devotional subjects; do not infer a match from generic words.
SUBJECTS = {
    "shiva": ("shiva", "shiv", "mahadev", "bholenath", "neelkanth", "shankar"),
    "krishna": ("krishna", "kanha", "govind", "gopal", "madhav"),
    "rama": ("rama", "ram", "raghav", "siyaram"),
    "hanuman": ("hanuman", "bajrang", "maruti"),
    "ganesha": ("ganesha", "ganesh", "ganpati", "vinayak"),
    "durga": ("durga", "kali", "chandi", "mahishasurmardini"),
    "vishnu": ("vishnu", "narayan", "narayana", "hari"),
    "shani": ("shani", "shanidev", "shanishchar"),
    "narasimha": ("narasimha", "narsimha", "narsingh"),
    "lakshmi": ("lakshmi", "laxmi"),
    "saraswati": ("saraswati", "sarasvati"),
    "parashuram": ("parashuram", "parshuram"),
    "vamana": ("vamana", "vaman"),
    "kalki": ("kalki",),
}

def subjects(name):
    tokens = set(re.findall(r"[a-z]+", name.lower()))
    normalized = re.sub(r"[^a-z]", "", name.lower())
    return {subject for subject, aliases in SUBJECTS.items()
            if any(alias in tokens or (len(alias) >= 5 and alias in normalized) for alias in aliases)}

# Scene/mood categories are conservative: ambiguous or opposing cues block a pairing.
MOODS = {
    "peaceful": ("peace", "peaceful", "calm", "meditation", "meditating", "dhyan", "serene", "relax", "soothing", "sleep"),
    "devotional": ("bhajan", "aarti", "arti", "mantra", "chant", "stotram", "stotra", "prayer", "puja", "pooja", "devotion", "devotional"),
    "battle": ("battle", "war", "fight", "fighting", "combat", "attack", "rage", "angry", "asur", "asura", "demon", "rakshas", "rakshasa", "killing", "slaying"),
    "celebration": ("festival", "celebration", "dance", "dancing", "wedding", "vivah", "holi", "diwali"),
    "sad": ("sad", "sorrow", "mourning", "crying", "grief", "tragic"),
}
# Only battle/peace and battle/devotional combinations are blocked; unspecified
# mood remains allowed for generic deity portraits, but explicit battle images
# require battle-themed audio to avoid incongruous religious pairings.
def mood_tags(name):
    tokens = set(re.findall(r"[a-z]+", name.lower()))
    return {mood for mood, aliases in MOODS.items() if tokens.intersection(aliases)}

def compatible(audio, image):
    a, i = mood_tags(audio["name"]), mood_tags(image["name"])
    if "battle" in i and "battle" not in a:
        return False
    if "battle" in a and ("peaceful" in i or "devotional" in i) and "battle" not in i:
        return False
    if "peaceful" in a and ("battle" in i or "sad" in i):
        return False
    if "sad" in a and "celebration" in i:
        return False
    if "celebration" in a and "sad" in i:
        return False
    return True

def choose_pair(music, images, used_pairs=None):
    used_pairs = used_pairs or set()
    candidates = [(audio, image) for audio in music for image in images
                  if subjects(audio["name"]) & subjects(image["name"])
                  and compatible(audio, image)
                  and (audio["id"], image["id"]) not in used_pairs]
    if not candidates:
        raise RuntimeError("No safe subject-and-mood music/image pairing found in filenames. "
                           "Add subject and scene/mood keywords to filenames; no random pairing will be made.")
    return random.choice(candidates)

def main():
    token=get_token()
    music=[f for f in files(FOLDERS["music"],token) if f.get("mimeType","").startswith("audio/") or f["name"].lower().endswith(".mp3")]
    images=[f for f in files(FOLDERS["images"],token) if f.get("mimeType","").startswith("image/") or f["name"].lower().endswith((".png",".jpg",".jpeg"))]
    print(f"Available: {len(music)} audio files, {len(images)} images")
    if not music or not images:raise RuntimeError("Music and image folders must both contain usable files")
    history_path = Path("growth-agents/reels-generated-history.json")
    history = json.loads(history_path.read_text()) if history_path.exists() else {"pairs": []}
    used_pairs = {(p["audio_id"], p["image_id"]) for p in history["pairs"]}
    audio,image=choose_pair(music,images,used_pairs)
    print('Matched subject(s):', ', '.join(sorted(subjects(audio['name']) & subjects(image['name']))))
    print('Audio mood:', sorted(mood_tags(audio['name'])), 'Image mood:', sorted(mood_tags(image['name'])))
    Path("reels-preview").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        paths=[]
        for item,ext in [(audio,".mp3"),(image,".jpg")]:
            path=Path(tmp)/("asset"+str(len(paths))+ext)
            with request(API+"/"+item["id"]+"?alt=media",token) as r,open(path,"wb") as out:
                import shutil
                shutil.copyfileobj(r,out)
            paths.append(path)
        output="reels-preview/reel-preview.mp4"
        # 30 seconds, 1080x1920, gentle Ken Burns zoom, H.264/AAC.
        vf="scale=1200:2134:force_original_aspect_ratio=increase,crop=1200:2134,zoompan=z='min(zoom+0.00015,1.12)':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=900:s=1080x1920:fps=30,format=yuv420p"
        cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-loop","1","-framerate","30","-i",str(paths[1]),"-stream_loop","-1","-i",str(paths[0]),"-t","30","-vf",vf,"-c:v","libx264","-preset","veryfast","-crf","26","-c:a","aac","-b:a","128k","-pix_fmt","yuv420p","-movflags","+faststart",output]
        subprocess.run(cmd,check=True,timeout=540)
    Path("reels-preview/selection.json").write_text(json.dumps({"audio":audio["name"],"image":image["name"],"duration_seconds":30},indent=2))
    history["pairs"].append({"audio_id":audio["id"],"image_id":image["id"],"audio_name":audio["name"],"image_name":image["name"]})
    history_path.write_text(json.dumps(history,indent=2,ensure_ascii=False)+"\n")
    print("Preview created successfully; generated pair recorded to prevent repetition. No Instagram publishing occurred.")

if __name__=="__main__":main()
