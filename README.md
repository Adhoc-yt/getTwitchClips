# getTwitchClips 
### A tool to get Twitch clips for a given user, and sort by name, date, views.

Live coding sessions in French on https://twitch.tv/adhoc_yt

---

#### Live of 5/6/2020 - Added GUI + OAuth support

Script is currently unusable without "auth.json", which contains client_id and client_secret, needed to generate OAuth tokens.

We get many more results much faster using the new Twitch API (800 req/min instead of 30).

The GUI is simple but functional.

---
#### Live of 5/4/2020 - Script prompts for Twitch channel name, uses the API to retrieve collection of clips

+main.py

We note that the results are not always accurate, and we tend to hit the 429 (too many requests) easily.

Still a bit flimsy but usable to get a JSON list of all clips (if the streamer has a *REASONABLE* number of clips)

---
