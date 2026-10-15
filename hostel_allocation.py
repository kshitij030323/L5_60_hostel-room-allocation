"""Hostel room allocation system.

Loads a YAML block configuration, allocates beds by block and gender,
vacates rooms, calculates fees, orders students by seniority, runs a
room lottery, counts vacant beds and serves a small Flask lookup page.
"""
import math
import os
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

DAYS_PER_MONTH = 30

CONFIG = """
blocks:
  A: {gender: M, rooms: 3, capacity: 2, fee: 4000}
  B: {gender: F, rooms: 2, capacity: 3, fee: 3500}
"""


def load_config(text=CONFIG):
    """Parse the YAML configuration and populate the global rooms table."""
    config = yaml.safe_load(text)
    for block, info in config["blocks"].items():
        for n in range(1, info["rooms"] + 1):
            rooms[block + str(n)] = {
                "gender": info["gender"],
                "capacity": info["capacity"],
                "fee": info["fee"],
                "occupants": [],
            }
    return config


def allocate_room(student_id, name, gender, year, preferred=None):
    """Allocate a bed to a student and return the room number.

    Preferred rooms are tried first. Returns None (and waitlists the
    student) if no suitable room has a free bed, or if the year is invalid.
    """
    if preferred is None:
        preferred = []
    try:
        year = int(year)
    except (TypeError, ValueError):
        return None
    if student_id in allocations:
        return allocations[student_id]["room"]
    for room_no in preferred + list(rooms.keys()):
        room = rooms.get(room_no)
        if room is None or room["gender"] != gender:
            continue
        if len(room["occupants"]) >= room["capacity"]:
            continue
        room["occupants"].append(student_id)
        allocations[student_id] = {"name": name, "room": room_no, "year": year}
        return room_no
    if student_id not in waitlist:
        waitlist.append(student_id)
    return None


def vacate_room(student_id):
    """Remove a student's allocation and free their bed."""
    allocation = allocations.pop(student_id, None)
    if allocation is not None:
        rooms[allocation["room"]]["occupants"].remove(student_id)


def monthly_fee(student_id, days_stayed):
    """Return the fee owed, charging for every started month."""
    room = rooms[allocations[student_id]["room"]]
    months = math.ceil(days_stayed / DAYS_PER_MONTH)
    return months * room["fee"]


def priority_order(students):
    """Return students ordered by seniority, highest year first."""
    return sorted(students, key=lambda s: s["year"], reverse=True)


def room_lottery(student_ids):
    """Return the student ids in a cryptographically random order."""
    rng = secrets.SystemRandom()
    return rng.sample(student_ids, len(student_ids))


def vacant_beds():
    """Return the total number of free beds across all rooms."""
    return sum(room["capacity"] - len(room["occupants"])
               for room in rooms.values())


def connect_warden_db():
    """Connect to the warden DB using credentials from the environment."""
    return sqlite_connect(host="localhost", user="warden",
                          password=os.environ.get("WARDEN_DB_PASSWORD", ""))


def sqlite_connect(host, user, password):
    """Stub database connection used by the warden portal."""
    return {"host": host, "user": user, "connected": len(password) > 0}


def _verify_log_config(data):
    """Only accept JSON (dictConfig) payloads on the logging listener."""
    if data.lstrip().startswith(b"{"):
        return data
    return None


def start_remote_log_config():
    """Start a logging configuration listener that verifies incoming data."""
    return logging.config.listen(9999, verify=_verify_log_config)


@app.route("/room")
def room_lookup():
    """Show the room allocated to the student given by the ?id= parameter."""
    sid = request.args.get("id", "")
    room = allocations.get(sid)
    return f"<h1>Room for {escape(sid)}: {escape(str(room))}</h1>"


def run_portal():
    """Run the Flask lookup portal."""
    app.run(debug=False)


def main():
    """Demonstrate the allocation system."""
    load_config()
    print("Rooms:", list(rooms.keys()))
    print("S1 ->", allocate_room("S1", "Arjun", "M", 1))
    print("S2 ->", allocate_room("S2", "Kabir", "M", 2))
    print("S3 ->", allocate_room("S3", "Rohan", "M", 3))
    print("S4 (female) ->", allocate_room("S4", "Diya", "F", 1))
    print("S1 again ->", allocate_room("S1", "Arjun", "M", 1))
    print("S5 year '2' ->", allocate_room("S5", "Vikram", "M", "2"))
    print("Occupants of A1:", rooms["A1"]["occupants"])
    vacate_room("S2")
    print("Occupants of A1 after S2 left:", rooms["A1"]["occupants"])
    print("Fee for S1, 45 days:", monthly_fee("S1", 45))
    ordered = priority_order([{"year": 1}, {"year": 4}, {"year": 2}])
    print("Priority (seniors first?):", [s["year"] for s in ordered])
    print("Lottery:", room_lottery(["S6", "S7", "S8"]))
    print("Vacant beds:", vacant_beds())
    print("Warden DB:", connect_warden_db())
    print("Waitlist:", waitlist)


if __name__ == "__main__":
    main()
