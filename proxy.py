def proxy():
    with open("prox") as f:
        proxy_list = ("".join(f.readlines())).split("\n")
    return proxy_list