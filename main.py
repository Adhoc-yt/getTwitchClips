# Ouvrir fenetre avec textfield + bouton "get Clips"
# Connexion curl API Twitch
# Parsing JSON
# Affichage et tri
import requests
import json
import time

CLIENT_ID = "mn75d76tgsck5famr0lw8zegpbd4wx"


def get_broadcaster_id(pstreamer_name):
    twitch_response = json.loads(requests.get("https://api.twitch.tv/helix/users",
                                              headers={"Accept": "application/vnd.twitchtv.v5+json",
                                                       "Client-ID": CLIENT_ID},
                                              params={"login": pstreamer_name}
                                              ).text)
    return twitch_response["data"][0]["id"]


def get_clips(pstreamer_id):
    data = []
    pagination_cursor = ""
    first_value = 20

    while True:
        twitch_response = requests.get("https://api.twitch.tv/helix/clips",
                                       headers={"Accept": "application/vnd.twitchtv.v5+json",
                                                "Client-ID": CLIENT_ID},
                                       params={"broadcaster_id": pstreamer_id,
                                               "first": first_value,
                                               "after": pagination_cursor}
                                       )
        if twitch_response.status_code == 429:
            print("Too fast for Twitch, gotta cool down, increasing fetch rate (currently {})...".format(first_value))
            first_value = min(2*first_value, 100)
            time.sleep(60)
            continue
        elif twitch_response.status_code >= 400:
            print("ALERTE-{}-{}".format(twitch_response.status_code, twitch_response.text))
            break

        twitch_response = json.loads(twitch_response.text)
        if "data" in twitch_response:
            data.extend(twitch_response["data"])

        if "pagination" in twitch_response and "cursor" in twitch_response["pagination"]:
            pagination_cursor = twitch_response["pagination"]["cursor"]
        else:
            break

    return data


if __name__ == "__main__":
    streamer_name = input("Nom du streamer:")
    res = get_clips(get_broadcaster_id(streamer_name))
    print(json.dumps(res, indent=4))
    print("Total clips:{}".format(len(res)))
