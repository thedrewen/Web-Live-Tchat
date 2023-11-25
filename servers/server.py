from colorama import Fore
import ssl, time, re, json, websockets, asyncio, datetime

# Liste des connexions actives
clients = set()
clients_name = {}
clients_channels = {}

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain('cert/fullchain.pem', 'cert/privkey.pem')

def isLetter(texte):
    regex = re.compile(r'[^a-zA-Z]')
    return not regex.search(texte)

async def sendData(websocket, data, author):
    if websocket.open:
        if clients_channels[author].upper() == clients_channels[websocket].upper():
            await websocket.send(json.dumps(data))

async def handle_client(websocket, path):
    
    remote, port = websocket.remote_address
    with open("var/ban.json", "r") as file:
        bans = json.load(file)
    if str(remote) in bans:
        await websocket.close()
        return
    
    clients.add(websocket)
    clients_channels[websocket] = "public"
    
    n = 0
    n_rateLimite = 0
    later_rateLimite = time.time() - 5
    message_timestamp = time.time() - 5
    rename_timestamp = time.time() - 5
    
    isLogin = True
    admin = False
    
    print(f"[{datetime.datetime.now()}] {Fore.GREEN}Client connecté : {websocket.remote_address}{Fore.RESET}")
    try:
        async for message in websocket:
            username_set = json.load(open("var/admin.json", "r"))
            
            data = json.loads(message)
            
            open(f"logs/{datetime.datetime.today().strftime('%Y-%m-%d')}.txt", "a+").write(str(datetime.datetime.now())+" : "+json.dumps(data)+str("\n"))
            
            
            if n_rateLimite >= 50:
                await websocket.close()
                with open("var/ban.json", "r") as file:
                    bans = json.load(file)
                    
                bans.append(remote)
                
                with open("var/ban.json", "w") as file:
                    json.dump(bans, file)
                return
                
            if time.time() - later_rateLimite >= 3:
                later_rateLimite -= 1
            
            
            n_rateLimite += 1
            later_rateLimite = time.time()
            if "Admin" in data:
                if data["Admin"]["type"].split(" ")[0] == "!login" and isLogin:
                    isLogin = False
                    data_split = data["Admin"]["type"].split(" ")
                    stat = True
                    for mdp, name in username_set.items():
                        if data_split[1] == mdp:
                            admin = True               
                            for client, value in clients_name.items():
                                if value == name:
                                    clients_name[client] = "CopieDe_"+name
                                    
                                    rename = {"Action" : {"type" : "rename", "author" : name, "data" : clients_name[client]}};
                            
                                    for client1 in clients:
                                        await sendData(client1, rename, websocket)
                            
                            rename = {"Action" : {"type" : "rename", "author" : clients_name[websocket], "data" : name}};
                            clients_name[websocket] = name
                            for client in clients:
                                await sendData(client, rename, websocket)
                            stat = False
                            print(f"[{datetime.datetime.now()}] {Fore.BLUE}{clients_name[websocket]} s'est connectée à sa session administrateur.{Fore.RESET}")
                            await sendData(websocket, {"System" : {"type" : "info", "data" : f"Connexion éffectué avec succès !\nBienvenue {name}"}}, websocket)
                            break
                    
                    if stat:
                        await asyncio.sleep(3)
                        isLogin = True
                        await sendData(websocket, {"System" : {"type" : "info", "data" : "Ce code administrateur n'existe pas !"}}, websocket)
                    
                elif admin:
                
                    commands = data["Admin"]["type"].split(" ")
                    if commands[0][0] == "!":
                        
                        if commands[0] == "!rename" and len(commands) == 3:
                            
                            user = commands[1]
                            new_name = commands[2]
                            
                            for client, value in clients_name.items():
                                if value == user:
                                    clients_name[client] = new_name
                                    break
                            
                            rename = {"Action" : {"type" : "rename", "author" : user, "data" : new_name}};
                            
                            for client1 in clients:
                                await sendData(client1, rename, websocket)
                            
                            await sendData(websocket, {"System" : {"type" : "info", "data" : "Rename éffectuez avec succès !"}}, websocket)
                        elif commands[0] == "!deco" and len(commands) == 2:
                            
                            for client, value in clients_name.items():
                                if value == commands[1]:
                                    await client.close()
                                    break
                                
                            await sendData(websocket, {"System" : {"type" : "info", "data" : commands[1]+" déconnecté avec succès !"}}, websocket)
                        elif commands[0] == "!help":
                            await sendData(websocket, {"System" : {"type" : "info", "data" : "Bienvenue sur le help administrateur :\n - !logout : vous déconnecte de votre session.\n - !login {password} : vous connecte à votre session.\n - !rename {user} {new_pseudo} : renomme un utilisateur.\n - !deco {user} : déconecte un utilisateur.\n - !clear : efface les messages."}}, websocket)
                        elif commands[0] == "!logout":
                            admin = False
                            isLogin = True
                            print(f"[{datetime.datetime.now()}] {Fore.BLUE}{clients_name[websocket]} s'est déconnecté de sa session administrateur.{Fore.RESET}")
                            await sendData(websocket, {"System" : {"type" : "info", "data" : "Vous n'êtes plus administrateur !"}}, websocket)
                        elif commands[0] == "!clear":
                            for client in clients:
                                await sendData(client, {"System" : {"type" : "clear"}}, websocket)
                                if client != websocket:
                                    await sendData(client, {"System" : {"type" : "info", "data" : "Les messages ont été effacés par un administrateur !"}}, websocket)
                            await sendData(websocket, {"System" : {"type" : "info", "data" : "Messages effacés avec succès !"}}, websocket)
                        else:
                            await sendData(websocket, {"System" : {"type" : "warn", "data" : "Commande Invalide !"}}, websocket)
                        
                    else:
                        await sendData(websocket, {"System" : {"type" : "warn", "data" : "Commande Invalide !"}}, websocket)
                else:
                    await sendData(websocket, {"System" : {"type" : "warn", "data" : "Vous n'êtes pas administrateur !"}}, websocket)
                
            else:
                if (time.time() - message_timestamp >= 2 or admin) and "Message" in data:
                    
                    message_timestamp = time.time()
                    
                    if data["Message"]["author"] == clients_name[websocket]:
                        if len(data["Message"]["content"]) > 0:
                            for client in clients:
                                await sendData(client, data, websocket)
                    else:
                        await sendData(websocket, {"System" : {"type" : "warn", "data" : "Votre pseudo n'est pas défini !"}}, websocket)
                elif not "Message" in data:
                    
                    if "Connexion" in data and n == 0:
                        
                        for client, value in clients_name.items():
                            await sendData(websocket, {"Connexion" : {"author" : value, "type" : "open"}}, client)
                            
                        clients_name[websocket] = data["Connexion"]["author"]
                        n += 1
                        
                        for client in clients:
                            await sendData(client, data, websocket)
                        
                        for client in clients:
                            users = json.load(open("var/users.json", "r"))
                            msg = clients_name[websocket]+" s'est connecté !"
                            if not remote in users:
                                msg = clients_name[websocket]+" s'est connecté pour la première fois !"
                                users.append(str(remote))
                                json.dump(users, open("var/users.json", "w"))
                            await sendData(client, {"System" : {"type" : "info", "data" : msg}}, websocket)
                        
                    if "Action" in data:
                        if "type" in data["Action"]:
                            if data["Action"]["type"] == "rename":
                                if time.time() - rename_timestamp >= 2:
                                    
                                    name_is = False
                                    
                                    for client, name in clients_name.items():
                                        if name == data["Action"]["data"]:
                                            name_is = True
                                            break
                                    
                                    if len(data["Action"]["data"]) >= 20 or len(data["Action"]["data"]) == 0 or name_is or not isLetter(data["Action"]["data"]) or " " in data["Action"]["data"]:
                                        await sendData(websocket, {"System" : {"type" : "warn", "data" : "Votre pseudo est invalide !"}}, websocket)
                                    else:
                                        clients_name[websocket] = data["Action"]["data"]
                                    
                                        rename_timestamp = time.time()
                                        for client in clients:
                                            await sendData(client, data, websocket)
                                else:
                                    await sendData(websocket, {"System" : {"type" : "warn", "data" : "Vous changez trop vite de pseudo !"}}, websocket)
                            if data["Action"]["type"] == "joinChannel":
                                if len(data["Action"]["data"]) > 0 and len(data["Action"]["data"]) < 7:
                                    
                                    channel = data["Action"]['data']
                                    
                                    if channel.upper() != clients_channels[websocket].upper():
                                        
                                        for client in clients:
                                            if client != websocket:
                                                await sendData(client, {"Connexion" : {"author" : clients_name[websocket], "type" : "close"}}, websocket)
                                        
                                        clients_channels[websocket] = channel
                                        
                                        for client in clients:
                                            if client != websocket:
                                                await sendData(client, {"Connexion" : {"author" : clients_name[websocket], "type" : "open"}}, websocket)
                                        
                                        await sendData(websocket, {"System" : {"type" : "info", "data" : "Vous avez rejoins le salon "+channel+" !"}}, websocket)
                                    
                                        for client in clients:
                                            msg = clients_name[websocket]+" s'est connecté !"
                                            await sendData(client, {"System" : {"type" : "info", "data" : msg}}, websocket)
                                            
                                        for client, value in clients_name.items():
                                            await sendData(websocket, {"Connexion" : {"author" : value, "type" : "open"}}, client)
                                        
                                    else:
                                        await sendData(websocket, {"System" : {"type" : "warn", "data" : "Vous êtes déjà dans ce salon !"}}, websocket)
                                    
                                else:
                                    await sendData(websocket, {"System" : {"type" : "warn", "data" : "Ce code de salon est invalide !"}}, websocket)

                else:
                    await sendData(websocket, {"System" : {"type" : "warn", "data" : "Vous envoyez trop vite des messages !"}}, websocket)
        
                
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"[{datetime.datetime.now()}] Connexion fermée de manière inattendue : {e}")
    except Exception as e:
        print(f"[{datetime.datetime.now()}] Erreur non gérée : {e}")

    finally:

        for client in clients:
            if client != websocket:
                await sendData(client, {"Connexion" : {"author" : clients_name[websocket], "type" : "close"}}, websocket)
        
        clients.remove(websocket)
        if websocket in clients_name:
            clients_name.pop(websocket)
        if websocket in clients_channels:
            clients_channels.pop(websocket)
            
        
        # Fermer la connexion lorsque le client se déconnecte
        await websocket.close()
        print(f"[{datetime.datetime.now()}] {Fore.RED}Client déconnecté : {websocket.remote_address}{Fore.RESET}")

print(f"[{datetime.datetime.now()}] Serveur start !")

start_server = websockets.serve(handle_client, "0.0.0.0", 4026, ssl=ssl_context)

# Lancer la boucle d'événements principale
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()