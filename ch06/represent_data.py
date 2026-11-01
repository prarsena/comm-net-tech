import json


order = {"course": "CS240", "item": "packet"}
wire = json.dumps(order, separators=(",", ":")).encode("utf-8")

print("Wire bytes:", wire)
print("Decoded:", json.loads(wire))
