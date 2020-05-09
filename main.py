# Ouvrir fenetre avec textfield + bouton "get Clips"
# Connexion curl API Twitch
# Parsing JSON
# Affichage et tri
# Exit status 1: Error API Twitch
# Exit status 2: auth.json does not exist
# Exit status 2: auth.json exists but is full of crap
# TODO Faire en sorte que le focus clavier soit dans le champ texte a l'ouverture


import requests
import json
import time
import sys
import tkinter
import tkinter.messagebox
import os.path
import webbrowser

OAUTH_TOKEN = ""
CLIENT_ID = ""


def print_json(x):
    print(json.dumps(json.loads(x.text), indent=4))


def get_broadcaster_id(pstreamer_name):
    twitch_response = requests.get("https://api.twitch.tv/helix/users",
                                   headers={"Accept": "application/vnd.twitchtv.v5+json",
                                            "Client-ID": CLIENT_ID,
                                            "Authorization": "Bearer {}".format(OAUTH_TOKEN)},
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

    if twitch_response["data"]:
        return twitch_response["data"][0]["id"]
    else:
        return None


def get_clips(pstreamer_id):
    pagination_cursor = ""
    first_value = 20

    while True:
        twitch_response = requests.get("https://api.twitch.tv/helix/clips",
                                       headers={"Accept": "application/vnd.twitchtv.v5+json",
                                                "Client-ID": CLIENT_ID,
                                                "Authorization": "Bearer {}".format(OAUTH_TOKEN)},
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
            yield twitch_response["data"]

        if "pagination" in twitch_response and "cursor" in twitch_response["pagination"]:
            pagination_cursor = twitch_response["pagination"]["cursor"]
        else:
            break


def display_results(presults, pstreamer_name):
    res_window = tkinter.Tk()
    res_window.title("Liste des clips pour {}".format(pstreamer_name))
    res_window.geometry("700x400")

    clip_list_var = tkinter.Text(res_window)
    clip_list_var.insert(tkinter.INSERT, "Total clips:{}\n".format(len(presults)))
    clip_list_var.insert(tkinter.INSERT, json.dumps(presults, indent=4))
    clip_list_var.pack()

    res_window.mainloop()


def send_streamer_name(pstreamer_name_window, pbtn_var, pentry_var):
    streamer_name = pentry_var.get()
    if not streamer_name:
        tkinter.messagebox.showerror(title="Erreur",
                                     message="Veuillez entrer un nom de streamer")
        return

    id_streamer = get_broadcaster_id(streamer_name)
    if not id_streamer:
        tkinter.messagebox.showerror(title="Erreur",
                                     message="Ce streamer n'existe pas")
        return

    pbtn_var["state"] = "disabled"
    results = []
    for clips in get_clips(id_streamer):
        results.extend(clips)
        pbtn_var["text"] = "Clips: {}".format(len(results))
        pstreamer_name_window.update()

    pbtn_var["state"] = "normal"
    pbtn_var["text"] = "OK"
    display_results(results, streamer_name)


def get_streamer_name_window():
    streamer_name_window = tkinter.Tk()
    streamer_name_window.title("Get Twitch Clips")
    streamer_name_window.geometry("300x200")

    label_var = tkinter.Label(streamer_name_window,
                              text="Nom du streamer :"
                              )
    label_var.pack()

    entry_var = tkinter.Entry(streamer_name_window,
                              bd=3,
                              width=20)
    entry_var.pack()

    btn_var = tkinter.Button(streamer_name_window,
                             command=lambda: send_streamer_name(streamer_name_window,
                                                                btn_var,
                                                                entry_var),
                             text="OK",
                             padx=10,
                             pady=5)

    btn_var.pack()

    entry_var.bind('<Return>', lambda event: send_streamer_name(streamer_name_window,
                                                                btn_var,
                                                                entry_var))
    streamer_name_window.bind('<Escape>', lambda event: streamer_name_window.quit())
    streamer_name_window.mainloop()


def send_auth_data(auth_window, pclient_id, pclient_secret):
    if not (pclient_id and pclient_secret):
        return

    auth_json_data = {"client_id": pclient_id,
                      "client_secret": pclient_secret}
    with open('auth.json', 'w') as outfile:
        json.dump(auth_json_data, outfile)

    auth_window.quit()


def open_url(purl):
    webbrowser.open_new(purl)


def get_auth_window():
    auth_window = tkinter.Tk()
    auth_window.title("Vous devez enregistrer l'application")
    auth_window.geometry("500x200")

    label_var = tkinter.Label(auth_window,
                              text="Cliquez ici pour enregistrer votre application\n"
                                   "(obligatoire pour utiliser l'API Twitch)\n"
                                   "Mettez http://localhost pour OAuth Redirect URL",
                              fg="blue",
                              cursor="hand2"
                              )
    label_var.pack()
    label_var.bind("<Button-1>", lambda e: open_url("https://dev.twitch.tv/console/apps/"))

    entry_client_id_var = tkinter.Entry(auth_window,
                                        bd=3,
                                        width=50)
    entry_client_id_var.pack()

    entry_client_secret_var = tkinter.Entry(auth_window,
                                            bd=3,
                                            width=50,
                                            show='*')
    entry_client_secret_var.pack()

    btn_var = tkinter.Button(auth_window,
                             text="OK",
                             command=lambda: send_auth_data(auth_window,
                                                            entry_client_id_var.get(),
                                                            entry_client_secret_var.get()),
                             padx=10,
                             pady=5)
    btn_var.pack()

    auth_window.mainloop()


def get_oauth_token():
    # Oauth part - TODO MOVE TO ANOTHER FILE
    global CLIENT_ID, OAUTH_TOKEN

    if not os.path.isfile('auth.json'):
        get_auth_window()

    try:
        with open('auth.json') as json_file:
            auth_data = json.load(json_file)
            CLIENT_ID = auth_data["client_id"]
            client_secret = auth_data["client_secret"]
            if not (CLIENT_ID and client_secret):
                print("malformed JSON auth file")
                sys.exit(3)
    except IOError:
        sys.exit(2)

    oauth_response = requests.post("https://id.twitch.tv/oauth2/token",
                                   params={"client_id": CLIENT_ID,
                                           "client_secret": client_secret,
                                           "grant_type": "client_credentials"}
                                   )
    OAUTH_TOKEN = json.loads(oauth_response.text)["access_token"]


if __name__ == "__main__":
    get_oauth_token()
    get_streamer_name_window()

# Creer fenetre qui contient le lien, textfield clientid, un textfield clientsecret, generer JSON, et retenter
# TODO Invalidate end session! #SEC_RISK
# TODO check token is valid else exit 3
# validate_token = requests.get("https://id.twitch.tv/oauth2/validate",
#                               headers={"Authorization": "OAuth {}".format(oauth_token)}
#                               )
