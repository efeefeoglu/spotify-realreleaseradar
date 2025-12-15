import requests, json, random
from datetime import datetime
from requests.auth import HTTPBasicAuth

exclude = ["0LyfQWJT6nXafLPZqxe9Of"]

from collections import Counter

def removeElements(lst,limit):
    counted = Counter(lst)
    return [el for el in lst if counted[el] >= limit]

data = {
    'grant_type': 'refresh_token',
    'refresh_token': 'AQA6aRYnezOEgk4QdI-YLJRo6hyQuy4fthMZOvw8Yj2DhH-kWO8AKh3pKsvw0hlwzAomO4bXfU6zxepeRIbrakwmd7hB6EvZRuElKEBdEB3xlcM68x1CDTSJmCTKH-inwRs'
}
gettoken = requests.post('https://accounts.spotify.com/api/token', data=data, auth=HTTPBasicAuth('9076f6e1d48f4693b426d0e4554ae3a6', '0dd2879dc1634c28858e00f4f37182aa'))
print("-------------------------------------------------------")
print("-------------------------------------------------------")
print("-------------------------------------------------------")
print(gettoken.text)
print("-------------------------------------------------------")

token = json.loads(gettoken.text)["access_token"]
headers = {"Authorization": f"Bearer {token}"}



print("#Remove adeu")
playlist = requests.get(f"https://api.spotify.com/v1/playlists/3JipB668cYf4wNMXCqFORj/tracks", headers=headers)
pl = playlist.json()
cc = pl["items"]
remove_data = {"tracks": []}
clean_data = {"tracks": []}
for c in cc:
    albumID = c["track"]["album"]["id"]
    clean_data["tracks"].append({"uri": str(c["track"]["uri"])})
    album_req = requests.get(f"https://api.spotify.com/v1/albums/{albumID}/tracks", headers=headers)
    album_tracks = album_req.json()["items"]
    for at in album_tracks:
        remove_data["tracks"].append({"uri": str(at["uri"])})
if clean_data["tracks"]:
    clean = requests.delete("https://api.spotify.com/v1/playlists/3JipB668cYf4wNMXCqFORj/tracks", headers=headers, json=clean_data)
    print(clean.text)
    remove = requests.delete("https://api.spotify.com/v1/playlists/6atuuQCz16M44yALH3inPW/tracks", headers=headers, json=remove_data)
    print(remove.text)



print("#Clean Real Release Radar")
playlist = requests.get(f"https://api.spotify.com/v1/playlists/6DrQLRiTFXuuMrGrrU3Yag/tracks", headers=headers)
pl = json.loads(playlist.text)
cc = pl["items"]
clean_data = {"tracks": []}
for c in cc:
    clean_data["tracks"].append({"uri": str(c["track"]["uri"])})

clean = requests.delete("https://api.spotify.com/v1/playlists/6DrQLRiTFXuuMrGrrU3Yag/tracks", headers=headers, json=clean_data)
print(clean.text)


print("#Clean masnuevos")
playlist = requests.get(f"https://api.spotify.com/v1/playlists/0xa959gzBBzf3ppnlskFdl/tracks", headers=headers)
pl = json.loads(playlist.text)
cc = pl["items"]
clean_data = {"tracks": []}
for c in cc:
    clean_data["tracks"].append({"uri": str(c["track"]["uri"])})

clean = requests.delete("https://api.spotify.com/v1/playlists/0xa959gzBBzf3ppnlskFdl/tracks", headers=headers, json=clean_data)
print(clean.text)


print("#Get following")
following = []
lastFollowing = ""
while True:
    if lastFollowing:
        followingReq = requests.get(f"https://api.spotify.com/v1/me/following?type=artist&limit=50&after={lastFollowing}", headers=headers)
    else:
        followingReq = requests.get(f"https://api.spotify.com/v1/me/following?type=artist&limit=50", headers=headers)
    followingData = json.loads(followingReq.text)
    for follow in followingData["artists"]["items"]:
        following.append(follow["id"])
        lastFollowing = follow["id"]
    if len(followingData["artists"]["items"])<50:
        break


print("#Get Artists from Ultimate")
total = 5000
i = 0
artists = []
while i<total:
    playlist = requests.get(f"https://api.spotify.com/v1/playlists/6J36Cfyn8bnyzklQj2IJaA/tracks?offset={i}", headers=headers)
    pl = json.loads(playlist.text)
    pp = pl["items"]

    for p in pp:
        artists.append(p["track"]["artists"][0]["id"])
    total = pl["total"]
    i+=100


print("#Get Artists from recently played")
getlatest = requests.get("https://api.spotify.com/v1/me/player/recently-played?limit=50", headers=headers)
latest = json.loads(getlatest.text)
lasts = []
for l in latest["items"]:
    artist_id = l["track"]["album"]["artists"][0]["id"]
    if not(artist_id in exclude):
        lasts.append(artist_id)

lasts = removeElements(lasts,3)

artists = list(dict.fromkeys(artists + lasts))


print("#Follow new artists")
follow = list(set(artists) - set(following))
if len(follow)>0:
    for i in range(round(len(follow)/50)+1):
        x = i*50
        text_artists = ','.join(follow[x:x+50])
        f_data = {"ids": follow[x:x+50]}
        followReq = requests.put(f"https://api.spotify.com/v1/me/following?type=artist&ids={text_artists}", headers=headers, json=f_data)
        print(followReq.text)


print("#Get New Releases")
today = datetime.today()
uris = []
for a in artists:
  albums = requests.get(f"https://api.spotify.com/v1/artists/{a}/albums", headers=headers)
  al = json.loads(albums.text)
  aal = al["items"]
  for al in aal:
      datetime_str = al["release_date"]
      try:
          datetime_object = datetime.strptime(datetime_str, '%Y-%m-%d')
          diff = today-datetime_object
          if(diff.days<30):
            aid=al["id"]
            tt = requests.get(f"https://api.spotify.com/v1/albums/{aid}/tracks?limit=2", headers=headers)
            trks = json.loads(tt.text)
            for trk in trks["items"]:
              uris.append(trk["uri"])
      except:
        pass

print("#Update Real Release Radar Tracks")
json = {"uris":uris}
updatelist =requests.post(f"https://api.spotify.com/v1/playlists/6DrQLRiTFXuuMrGrrU3Yag/tracks", headers=headers, json=json)
print(updatelist.text)


print("#Find related artists")
candidates = []
for a in artists:
    try:
        getrelated = requests.get(f"https://api.spotify.com/v1/artists/{a}/related-artists", headers=headers)
        related = json.loads(getrelated.text)
        print(getrelated.text)
        for r in related["artists"]:
            candidates.append(r["id"])
    except:
        pass

print(candidates)
candidates = removeElements(candidates,2)
print(candidates)

print("#Update Real Release Radar Tracks")
uris = []
for a in candidates:
    if not(a in artists):
        albums = requests.get(f"https://api.spotify.com/v1/artists/{a}/top-tracks", headers=headers)
        al = json.loads(albums.text)
        for trk in al["tracks"][:2]:
            uris.append(trk["uri"])
if len(uris)>0:
    json = {"uris":uris}
    updatelist =requests.post(f"https://api.spotify.com/v1/playlists/6DrQLRiTFXuuMrGrrU3Yag/tracks", headers=headers, json=json)
    print(updatelist.text)




print("#GET Artist from Yeni")

total = 5000
i = 0
tracks = []
while i<total:
    try:
        yeni = requests.get(f"https://api.spotify.com/v1/playlists/6atuuQCz16M44yALH3inPW/tracks?offset={i}", headers=headers)
        pl = yeni.json()
        pp = pl["items"]
        for p in pp:
            tracks.append(p["track"]["uri"])
        total = pl["total"]
        i+=100
    except Exception as e:
        print(e)
        break
print(tracks)
randomTracks = random.sample(tracks, 25)

print("#Update masnuevos Tracks")

json = {"uris":randomTracks}
updatelist =requests.post(f"https://api.spotify.com/v1/playlists/0xa959gzBBzf3ppnlskFdl/tracks", headers=headers, json=json)
print(updatelist.text)
