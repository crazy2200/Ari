import socket
import pickle
import math
import random

PORT = 8888
MAP_SIZE = 3000

# Ініціалізація об'єктів на сервері
eats = [
    {"x": random.randint(-MAP_SIZE, MAP_SIZE), "y": random.randint(-MAP_SIZE, MAP_SIZE), "r": 10, "color": (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))}
    for _ in range(300)
]

ALL_BOT_NAMES = ["Shadow", "ProGamer", "Killer2006", "Storm", "Vortex", "Ghost", "CyberNinja", "Phoenix", "Titan", "Neon"]

bots = [
    {
        "x": random.randint(-MAP_SIZE // 2, MAP_SIZE // 2),
        "y": random.randint(-MAP_SIZE // 2, MAP_SIZE // 2),
        "r": random.randint(12, 25),
        "color": (0, 0, 255),
        "nickname": random.choice(ALL_BOT_NAMES),
        "dx": random.choice([-1.5, 1.5]),
        "dy": random.choice([-1.5, 1.5])
    }
    for _ in range(20)
]

clients = {}  # addr: {"x": x, "y": y, "r": r, "color": color, "nickname": name, "is_boosting": False}

server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_sock.bind(("0.0.0.0", PORT))
server_sock.setblocking(False)

print(f"Сервер запущено на порту {PORT}...")

import time
clock_time = time.time()

while True:
    # 1. Прийом даних від клієнтів
    try:
        while True:
            data, addr = server_sock.recvfrom(4096)
            packet = pickle.loads(data)
            clients[addr] = packet
    except BlockingIOError:
        pass

    # 2. Логіка ботів
    for bot in bots:
        bot["x"] += bot["dx"]
        bot["y"] += bot["dy"]
        if bot["x"] - bot["r"] <= -MAP_SIZE or bot["x"] + bot["r"] >= MAP_SIZE:
            bot["dx"] *= -1
        if bot["y"] - bot["r"] <= -MAP_SIZE or bot["y"] + bot["r"] >= MAP_SIZE:
            bot["dy"] *= -1

    # 3. Перевірка зіткнень з їжею (для ботів)
    for bot in bots:
        for eat in eats[:]:
            dist = math.hypot(bot["x"] - eat["x"], bot["y"] - eat["y"])
            if dist <= bot["r"] + eat["r"]:
                bot["r"] = math.sqrt(bot["r"] ** 2 + 3)
                eat["x"] = random.randint(-MAP_SIZE, MAP_SIZE)
                eat["y"] = random.randint(-MAP_SIZE, MAP_SIZE)

    # 4. Зіткнення ботів і гравців між собою
    all_entities = list(clients.values()) + bots
    # (Спрощена перевірка поглинання)
    for i in range(len(bots)):
        for j in range(len(bots)):
            if i == j: continue
            b1, b2 = bots[i], bots[j]
            if b1["r"] > b2["r"] * 1.05:
                if math.hypot(b1["x"] - b2["x"], b1["y"] - b2["y"]) <= b1["r"]:
                    b1["r"] = math.sqrt(b1["r"] ** 2 + b2["r"] ** 2)
                    b2["x"] = random.randint(-MAP_SIZE // 2, MAP_SIZE // 2)
                    b2["y"] = random.randint(-MAP_SIZE // 2, MAP_SIZE // 2)
                    b2["r"] = 15

    # 5. Відправка стану світу всім підключеним клієнтам
    world_state = {
        "clients": clients,
        "bots": bots,
        "eats": eats
    }
    serialized_data = pickle.dumps(world_state)

    for addr in list(clients.keys()):
        try:
            server_sock.sendto(serialized_data, addr)
        except:
            del clients[addr]

    time.sleep(0.01)