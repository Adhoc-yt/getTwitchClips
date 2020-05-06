# Ouvrir fenetre avec textfield + bouton "get Clips"
# Connexion curl API Twitch
# Parsing JSON
# Affichage et tri
# Exit status 1: Error API Twitch


import requests
import json
import time
import sys
import tkinter
import tkinter.messagebox

CLIENT_ID = "mn75d76tgsck5famr0lw8zegpbd4wx"


def get_broadcaster_id(pstreamer_name):
    twitch_response = requests.get("https://api.twitch.tv/helix/users",
                                   headers={"Accept": "application/vnd.twitchtv.v5+json",
                                            "Client-ID": CLIENT_ID},
                                   params={"login": pstreamer_name}
                                   )

    if twitch_response.status_code > 400:
        tkinter.messagebox.showerror("Error reaching Twitch API",
                                     "Error {}\n{}".format(twitch_response.status_code,
                                                           json.dumps(json.loads(twitch_response.text),
                                                                      indent=4))
                                     )
        sys.exit(1)

    twitch_response = json.loads(twitch_response.text)
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
            first_value = min(2 * first_value, 100)
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


def send_form(pentry_var):
    streamer_name = pentry_var.get()
    if not streamer_name:
        tkinter.messagebox.showerror(title="Erreur",
                                     message="Veuillez entrer un nom de streamer")
        return

    results = get_clips(get_broadcaster_id(streamer_name))
    display_results(results, streamer_name)


def display_results(presults, pstreamer_name):
    res_window = tkinter.Tk()
    res_window.title("Liste des clips pour {}".format(pstreamer_name))
    res_window.geometry("600x1000")

    text_var = tkinter.text(res_window,
                            text=presults)


def get_streamer_name_window():
    streamer_name_window = tkinter.Tk()
    streamer_name_window.title("Get Twitch Clips")
    streamer_name_window.geometry("300x200")

    label_var = tkinter.Label(streamer_name_window,
                              text="Nom du streamer :"
                              )
    label_var.grid(row=0,
                   column=0,
                   padx=(20, 0),
                   pady=(80, 0))

    entry_var = tkinter.Entry(streamer_name_window,
                              bd=3,
                              width=20)
    entry_var.grid(row=0,
                   column=1,
                   pady=(80, 0))

    btn_var = tkinter.Button(streamer_name_window,
                             text="OK",
                             command=lambda: send_form(entry_var),
                             padx=10,
                             pady=5)
    btn_var.grid(row=1,
                 column=1,
                 pady=(20, 0))

    streamer_name_window.mainloop()


if __name__ == "__main__":
    get_streamer_name_window()
