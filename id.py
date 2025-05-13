import random
allowed = '!#%()*+,-./:;=?@[]^_`{|}~' +'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
used = {}
def new():
    uuid = "".join([random.choice(allowed) for i in range(20)])
    return uuid
def unique(server="main"):
    if server not in used:
        used[server] = []
    uuid = new()
    while uuid in used[server]:
        uuid = new()
    used[server].append(uuid)
    return uuid