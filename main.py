# Ouvrir fenetre avec textfield + bouton "get Clips"
# Connexion curl API Twitch
# Parsing JSON
# Affichage et tri
import requests
import json

CLIENT_ID = "mn75d76tgsck5famr0lw8zegpbd4wx"


def get_broadcaster_id(pstreamer_name):
    twitch_response = json.loads(requests.get("https://api.twitch.tv/helix/users",
                                              headers={"Accept": "application/vnd.twitchtv.v5+json",
                                                       "Client-ID": CLIENT_ID},
                                              params={"login": pstreamer_name}
                                              ).text)
    return twitch_response["data"][0]["id"]


def get_clips(pstreamer_id):
    twitch_response = json.loads(requests.get("https://api.twitch.tv/helix/clips",
                                              headers={"Accept": "application/vnd.twitchtv.v5+json",
                                                       "Client-ID": CLIENT_ID},
                                              params={"broadcaster_id": pstreamer_id,
                                                      "first": 100}
                                              ).text)
    return twitch_response["data"]


if __name__ == "__main__":
    streamer_name = "adhoc_yt"
    print(json.dumps(get_clips(get_broadcaster_id(streamer_name)), indent=4))
