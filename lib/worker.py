import threading

def start_worker():
    x = threading.Thread(target=handle_update, args=(1,), daemon=True)
    x.start()

def handle_update():
    pass