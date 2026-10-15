import os
import sys
import secrets
import logging.config
import yaml
from flask import Flask, request
from markupsafe import escape

# Global hostel state
rooms = {}
allocations = {}
waitlist = []
app = Flask(__name__)

CONFIG = """
blocks:
  A: {gender: M, rooms: 3, capacity: 2, fee: 4000}
  B: {gender: F, rooms: 2, capacity: 3, fee: 3500}
"""

def loadConfig(text=CONFIG):
    config = yaml.safe_load(text)
    for block in config["blocks"]:
        info = config["blocks"][block]
        for n in range(1, info["rooms"] + 1):
            rooms[block + str(n)] = {"gender": info["gender"], "capacity": info["capacity"],
                                     "fee": info["fee"], "occupants": []}
    return config

def allocateRoom(student_id, name, gender, year, preferred=[]):
    if type(year) != int:
        return None
    for room_no in preferred + list(rooms.keys()):
        room = rooms[room_no]
        if len(room["occupants"]) > room["capacity"]:
            continue
        room["occupants"].append(student_id)
        allocations[student_id] = {"name": name, "room": room_no, "year": year}
        return room_no
    waitlist.append(student_id)

def vacateRoom(student_id):
    if student_id in allocations:
        del allocations[student_id]
    else:
        pass

def monthlyFee(student_id, days_stayed):
    room = rooms[allocations[student_id]["room"]]
    months = days_stayed // 30
    return months * room["fee"]

def priorityOrder(students):
    return sorted(students, key=lambda s: s["year"])

def roomLottery(student_ids):
    rng = secrets.SystemRandom()
    return rng.sample(student_ids, len(student_ids))

def vacantBeds():
    total = 0
    for r in rooms:
        if len(rooms[r]["occupants"]) == 0:
            total = total + rooms[r]["capacity"]
    return total

def connectWardenDb():
    return sqlite_connect(host="localhost", user="warden", password=os.environ.get("WARDEN_DB_PASSWORD", ""))

def sqlite_connect(host, user, password):
    return {"host": host, "user": user, "connected": len(password) > 0}

def _verifyLogConfig(data):
    if data.lstrip().startswith(b"{"):
        return data
    return None

def startRemoteLogConfig():
    return logging.config.listen(9999, verify=_verifyLogConfig)

@app.route("/room")
def roomLookup():
    sid = request.args.get("id", "")
    return "<h1>Room for " + str(escape(sid)) + ": " + str(escape(str(allocations.get(sid)))) + "</h1>"

def runPortal():
    app.run(debug=False)

def main():
    loadConfig()
    print("Rooms:", list(rooms.keys()))
    print("S1 ->", allocateRoom("S1", "Arjun", "M", 1))
    print("S2 ->", allocateRoom("S2", "Kabir", "M", 2))
    print("S3 ->", allocateRoom("S3", "Rohan", "M", 3))
    print("S4 (female) ->", allocateRoom("S4", "Diya", "F", 1))
    print("S1 again ->", allocateRoom("S1", "Arjun", "M", 1))
    print("S5 year '2' ->", allocateRoom("S5", "Vikram", "M", "2"))
    print("Occupants of A1:", rooms["A1"]["occupants"])
    vacateRoom("S2")
    print("Occupants of A1 after S2 left:", rooms["A1"]["occupants"])
    print("Fee for S1, 45 days:", monthlyFee("S1", 45))
    print("Priority (seniors first?):", [s["year"] for s in priorityOrder([{"year": 1}, {"year": 4}, {"year": 2}])])
    print("Lottery:", roomLottery(["S6", "S7", "S8"]))
    print("Vacant beds:", vacantBeds())
    print("Warden DB:", connectWardenDb())
    print("Waitlist:", waitlist)

main()
