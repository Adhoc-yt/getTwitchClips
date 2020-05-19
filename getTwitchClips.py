# TODO bug if using '\' in streamer_name
# TODO bug si double clic sur en-tete (unbind categories)
# TODO Change cursor on hover links
# TODO !!!! Lazy loading for thumbnails
# TODO zoom thumbnail on hover
# TODO !!! barre de recherche
# TODO resize columns
# TODO Clip Downloader ?

# Exit status 1: Error API Twitch
# Exit status 2: auth.json does not exist
# Exit status 3: auth.json exists but is full of crap


import requests
import json
import time
import sys
import tkinter
import tkinter.messagebox
import tkinter.ttk
import tkinter.font
import os.path
import webbrowser
import dateutil.parser
from io import BytesIO
from PIL import Image, ImageTk
import threading

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

    if "data" in twitch_response and twitch_response["data"]:
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


def sortby(tree, pcol, descending):
    # Grab values to sort + Cast if column of different type
    if pcol == "view_count":
        data = [(int(tree.set(child, pcol)), child) for child in tree.get_children()]
    elif pcol == "created_at":
        data = [(dateutil.parser.isoparse(tree.set(child, pcol)), child)
                for child in tree.get_children()]
    else:
        data = [(tree.set(child, pcol).lower(), child) for child in tree.get_children()]

    # Reorder data
    odd_row = False
    data.sort(reverse=descending)
    for indx, item in enumerate(data):
        tree.move(item[1], '', indx)
        tree.item(item[1], tags=("oddrow" if odd_row else "evenrow",))
        odd_row = not odd_row

    # switch the heading so that it will sort in the opposite direction
    tree.heading(pcol,
                 command=lambda col=pcol: sortby(tree,
                                                 col,
                                                 int(not descending)))


def generate_thumbnail_placeholder(pcolor):
    return ImageTk.PhotoImage(Image.new("RGB", (142, 80), pcolor))


def download_thumbnails(presults):
    for clip in presults:
        clip["thumbnail"] = generate_thumbnail(clip["thumbnail_url"])


def generate_thumbnail(p_thumbnail_url):
    response = requests.get(p_thumbnail_url)
    image = Image.open(BytesIO(response.content))
    image = image.resize((142, 80))
    return ImageTk.PhotoImage(image)


def resolve_game(pid_game):
    twitch_response = requests.get("https://api.twitch.tv/helix/games",
                                   headers={"Accept": "application/vnd.twitchtv.v5+json",
                                            "Client-ID": CLIENT_ID,
                                            "Authorization": "Bearer {}".format(OAUTH_TOKEN)},
                                   params={"id": pid_game}
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
        return twitch_response["data"][0]["name"]
    else:
        return None


def open_clip(event):
    item_id = event.widget.focus()
    item = event.widget.item(item_id)
    values = item['values']
    open_url(values[5])


def init_tree(parent_frame, pcolums):
    # Workaround for ttk color glitch: https://bugs.python.org/issue36468
    def fixed_map(option):
        # From: https://core.tcl.tk/tk/info/509cafafae
        return [elm for elm in style.map('Treeview', query_opt=option) if
                elm[:2] != ('!disabled', '!selected')]

    style = tkinter.ttk.Style(parent_frame)
    style.configure('Treeview',
                    rowheight=90)
    style.map('Treeview',
              foreground=fixed_map('foreground'),
              background=fixed_map('background'))

    tree_var = tkinter.ttk.Treeview(parent_frame,
                                    columns=pcolums,
                                    selectmode="extended")
    tree_var.heading("#0", text="", anchor='center')
    return tree_var


def build_tree(ptree, pcolums, pcontent):
    for col in pcolums:
        ptree.heading(col,
                      text=col.title(),
                      command=lambda c=col: sortby(ptree, c, 0))
        ptree.column(col,
                     width=tkinter.font.Font().measure(col.title()))

    odd_row = False
    games = {}

    for clip in pcontent:
        # Adapting dictionnary format to list of values
        item = [clip[h] for h in pcolums]

        # Check we only have safe characters for Titles
        item[0] = ''.join(filter(lambda x: ord(x) < 65535, item[0]))

        # Resolve game_id in game_name and replace id by name
        if item[4] not in games:
            game_name = resolve_game(item[4])
            games[item[4]] = game_name
        item[4] = games[item[4]]

        ptree.insert('',
                     'end',
                     image=clip["thumbnail"],
                     values=item,
                     tags=("oddrow" if odd_row else "evenrow",))
        odd_row = not odd_row

        # Adjust columns lengths if necessary
        for indx, val in enumerate(item):
            ilen = tkinter.font.Font().measure(val)
            if ptree.column(pcolums[indx],
                            width=None) < ilen:
                ptree.column(pcolums[indx],
                             width=ilen)


def init_scrollbar(parent_window, ptree):
    vsb = tkinter.ttk.Scrollbar(parent_window,
                                orient="vertical",
                                command=ptree.yview)
    hsb = tkinter.ttk.Scrollbar(parent_window,
                                orient="horizontal",
                                command=ptree.xview)
    ptree.configure(yscrollcommand=vsb.set,
                    xscrollcommand=hsb.set)

    # Grid layout
    ptree.grid(column=0,
               row=0,
               sticky='nsew',
               in_=parent_window)
    vsb.grid(column=1,
             row=0,
             sticky='ns',
             in_=parent_window)
    hsb.grid(column=0,
             row=1,
             sticky='ew',
             in_=parent_window)


def tree_binds(ptree):
    ptree.tag_configure("evenrow",
                        background="lightblue",
                        foreground="black")
    ptree.tag_configure("oddrow",
                        background="white",
                        foreground="black")

    ptree.bind("<Double-1>", open_clip)


def display_results(presults, pstreamer_name):
    res_window = tkinter.Toplevel()
    res_window.title("Liste des clips pour {} - Total clips : {}".format(pstreamer_name, len(presults)))
    res_window.geometry("1300x600")

    t = threading.Thread(target=download_thumbnails, args=(presults,))
    t.start()

    # Frame
    tree_frame = tkinter.ttk.Frame(res_window)
    tree_frame.pack(fill='both',
                    expand=True)

    tree_columns = ("title",
                    "created_at",
                    "creator_name",
                    "view_count",
                    "game_id",
                    "url")

    tree_var = init_tree(res_window, tree_columns)
    build_tree(tree_var, tree_columns, presults)

    # async load thumbnails
    # pthumbnails.append(generate_thumbnail(clip["thumbnail_url"]))

    # Background 1/2 + Clickable links + Thumbnails display
    tree_binds(tree_var)
    # TODO ? child[5].configure(fg="blue",cursor="hand2")

    # Scrollbars
    init_scrollbar(tree_frame, tree_var)

    tree_frame.grid_columnconfigure(0, weight=1)
    tree_frame.grid_rowconfigure(0, weight=1)

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
    if len(results) == 0:
        tkinter.messagebox.showinfo(title="Rien de rien!",
                                    message="Ce streamer n'a aucun clip dans sa collection...")
        return
    else:
        for res in results:
            res["thumbnail"] = generate_thumbnail_placeholder("grey")
        display_results(results, streamer_name)


def get_streamer_name_window():
    streamer_name_window = tkinter.Tk()
    streamer_name_window.title("Get Twitch Clips")
    streamer_name_window.geometry("300x100")

    label_var = tkinter.Label(streamer_name_window,
                              text="Nom de la chaîne Twitch:"
                              )
    label_var.pack()

    entry_var = tkinter.Entry(streamer_name_window,
                              bd=3,
                              width=20)
    entry_var.pack()
    entry_var.focus_set()

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
    btn_var.bind('<Return>', lambda event: send_streamer_name(streamer_name_window,
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
    global CLIENT_ID, OAUTH_TOKEN

    if not os.path.isfile('auth.json'):
        get_auth_window()

    try:
        with open('auth.json') as json_file:
            auth_data = json.load(json_file)
            CLIENT_ID = auth_data["client_id"]
            client_secret = auth_data["client_secret"]
            if not (CLIENT_ID and client_secret):
                tkinter.messagebox.showerror(title="Erreur",
                                             message="Fichier auth.json invalide")
                sys.exit(3)
    except IOError:
        sys.exit(2)

    oauth_response = requests.post("https://id.twitch.tv/oauth2/token",
                                   params={"client_id": CLIENT_ID,
                                           "client_secret": client_secret,
                                           "grant_type": "client_credentials"}
                                   )
    OAUTH_TOKEN = json.loads(oauth_response.text)["access_token"]


def invalidate_oauth_token():
    requests.post("https://id.twitch.tv/oauth2/revoke",
                  params={"client_id": CLIENT_ID,
                          "token": OAUTH_TOKEN}
                  )


if __name__ == "__main__":
    get_oauth_token()
    get_streamer_name_window()
    invalidate_oauth_token()
