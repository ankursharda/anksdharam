#!/usr/bin/env python3
"""Build one preview Reel from Google Drive assets. Never publishes."""
import json, os, random, subprocess, tempfile
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

def main():
    token=get_token()
    music=[f for f in files(FOLDERS["music"],token) if f.get("mimeType","").startswith("audio/") or f["name"].lower().endswith(".mp3")]
    images=[f for f in files(FOLDERS["images"],token) if f.get("mimeType","").startswith("image/") or f["name"].lower().endswith((".png",".jpg",".jpeg"))]
    print(f"Available: {len(music)} audio files, {len(images)} images")
    if not music or not images:raise RuntimeError("Music and image folders must both contain usable files")
    audio=random.choice(music); image=random.choice(images)
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
    print("Preview created successfully. No Instagram publishing occurred.")

if __name__=="__main__":main()
