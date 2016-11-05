from flask import Flask, current_app, render_template
import json
from AudioListPlayer import AudioListPlayer

def get_alplr():
	alplr = getattr(current_app, '_database', None)
	if alplr is None:
		alplr = current_app._database = AudioListPlayer([
					"/mnt/nfsserver/app/sounds/a.mp3",
					"/mnt/nfsserver/app/sounds/asharp.mp3", 
					"/mnt/nfsserver/app/sounds/b.mp3", 
					"/mnt/nfsserver/app/sounds/c.mp3", 
					"/mnt/nfsserver/app/sounds/csharp.mp3"]*2, 100, True)
	return alplr

app = Flask(__name__)

itsok = json.dumps({'success': True}), 200, {'ContentType': 'application/json'}

@app.route("/")
def main():
	return render_template('base.html')

# ***********************
# *      Commands       *
# ***********************

@app.route("/player/pause")
def alplr_pause():
	get_alplr().pause()
	return itsok

@app.route("/player/play")
def alplr_play():
	get_alplr().play()
	return itsok

@app.route("/player/next")
def alplr_next():
	alplr = get_alplr()
	if alplr.next():
		return json.dumps({
			"success": True, 
			"position": alplr.playlist_position
			}), 200, {'ContentType': 'application/json'}
	else:
		return json.dumps({
			"success": False, 
			"error": "No next file", 
			"position": alplr.playlist_position}), 404, {'ContentType': 'application/json'}

@app.route("/player/prev")
def alplr_prev():
	alplr = get_alplr()
	if alplr.prev():
		return json.dumps({
			"success": True, 
			"position": alplr.playlist_position
			}), 200, {'ContentType': 'application/json'}
	else:
		return json.dumps({
			"success": False, 
			"error": "No prev file", 
			"position": alplr.playlist_position}), 404, {'ContentType': 'application/json'}

@app.route("/player/position/<int:position>", methods=['PUT'])
def alplr_set_position(position):
	alplr = get_alplr()
	if alplr.set_playlist_position(position):
		return json.dumps({
			"success": True, 
			"position": alplr.playlist_position
			}), 200, {'ContentType': 'application/json'}
	else:
		return json.dumps({
			"success": False, 
			"error": "No such file", 
			"position": alplr.playlist_position}), 404, {'ContentType': 'application/json'}

@app.route("/player/volume/<int:volume>", methods=['PUT'])
def alplr_set_volume(volume):
	get_alplr().set_volume(volume)
	return itsok

@app.route("/player/progress/<float:progress>", methods=['PUT'])
def alplr_set_progress(progress):
	get_alplr().set_position(progress)
	return itsok

# ***********************
# *    Data requests    *
# ***********************

@app.route("/player/position/", methods=['GET'])
def alplr_get_position():
	return json.dumps({
		"success": True, 
		"position": get_alplr().playlist_position}), 200, {'ContentType': 'application/json'}

@app.route("/player/volume/", methods=['GET'])
def alplr_get_volume():
	vol = get_alplr().get_volume()
	return json.dumps({'success': True, 'volume': vol}), 200, {'ContentType': 'application/json'}

@app.route("/player/progress/", methods=['GET'])
def alplr_get_progress():
	position = get_alplr().get_position()
	return json.dumps({'success': True, 'progress': progress}), 200, {'ContentType': 'application/json'}

@app.route("/player/length/", methods=['GET'])
def alplr_get_length():
	length = get_alplr().get_length()
	return json.dumps({'success': True, "data": {'length': length}}), 200, {'ContentType': 'application/json'}

@app.route("/player/meta/", methods=['GET'])
def alplr_get_current_meta():
	meta = get_alplr().get_current_audiomedia().meta
	response = {"success": True, "data": meta}
	return json.dumps(response), 200, {'ContentType': 'application/json'}

@app.route("/player/playlist/<int:audiomedia_index>/meta/", methods=['GET'])
def alplr_get_meta(audiomedia_index):
	try:
		meta = get_alplr().get_audiomedia(audiomedia_index).meta
		response = {"success": True, "data": meta}
		return json.dumps(response), 200, {'ContentType': 'application/json'}
	except AttributeError:
		return json.dumps({"success": False}), 404, {'ContentType': 'application/json'}

@app.route("/player/playlist/all/meta/", methods=['GET'])
def alplr_get_all_meta():
	all_meta = []
	for media_item in get_alplr().playlist:
		all_meta.append(media_item.meta)
	return json.dumps(all_meta), 200, {'ContentType': 'application/json'}

@app.route("/player/state", methods=['GET'])
def alplr_get_state():
	state = {}
	alplr = get_alplr()
	state["progress"] = alplr.get_position()
	state["length"] = alplr.get_length()
	state["volume"] = alplr.get_volume()
	state["playlist_position"] = alplr.playlist_position
	state["is_playing"] = alplr.is_playing
	
	all_meta = []
	for media_item in get_alplr().playlist:
		all_meta.append(media_item.meta)
	
	state["playlist"] = all_meta

	return json.dumps(state), 200, {'ContentType': 'application/json'}

if __name__ == "__main__":
	app.run(host="0.0.0.0", debug=True)
