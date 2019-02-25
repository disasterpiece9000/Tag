from tinydb import TinyDB

opt = TinyDB("opt-in.json")
new = TinyDB("player_data.json")

for username in opt:
	new.insert({"username": username['username'], "last_round": "", "score": 0})