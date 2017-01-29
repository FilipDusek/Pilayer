from flask import Flask, render_template, session, request, current_app, url_for, make_response
from flask_socketio import SocketIO, emit, join_room, leave_room, \
	close_room, rooms, disconnect
from AudioListPlayer import AudioListPlayer, MediaLibrary
import os, config
import pickle

async_mode = "gevent"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None

def get_alplr():
	alplr = getattr(current_app, '_alplr', None)
	if alplr is None:
		playlist = []
		for file in os.listdir("sounds"):

			with open("queue.pickle", "rb") as fp:   # Unpickling
				queuepaths = pickle.load(fp)

		alplr = current_app._alplr = AudioListPlayer(queuepaths, config.player_default_volume, config.player_debug, remove_after_play = config.queue_auto_remove)
		alplr.on_end_reached += handler_end_reached
		alplr.on_art_ready += handler_art_ready
		alplr.on_queue_changed += handler_queue_changed
	return alplr

def get_lib():
	library = getattr(current_app, '_library', None)
	if library is None:
		current_app._library = MediaLibrary(config.song_lib_path)
	return current_app._library

def handler_art_ready(alplr, art_path):
	with app.test_request_context():
		if art_path is None:
			art_url = ""
		else:
			art_url = url_for('static', filename=art_path)

		socketio.emit(
					"event_art_ready", 
					{"album_art": art_url}, 
					broadcast = True, 
					namespace="/test")

def handler_end_reached(alplr):
	if alplr.queue_end_reached:
		socketio.emit("event_pause", broadcast = True, namespace='/test')
	else: 
		socketio.emit("event_track_changed", {"queue_position": alplr.queue_position, "length": alplr.get_length()}, broadcast = True, namespace='/test')

def handler_queue_changed(alplr):
	queuepaths = []
	for media in alplr.queue:
		queuepaths.append(media.media_loc)

	with open("queue.pickle", "wb") as fp:
		pickle.dump(queuepaths, fp)

	socketio.emit("event_queue_changed", {"queue": alplr.get_queue_meta(), "queue_position": alplr.queue_position}, broadcast = True, namespace="/test")
	if not alplr.is_playing:
		socketio.emit("event_pause", broadcast = True, namespace='/test')
		socketio.emit("event_track_changed", {"queue_position": alplr.queue_position, "length": alplr.get_length()}, broadcast = True, namespace='/test')

def audio_progress_notify(alplr):
	while True:
		socketio.sleep(1)
		if alplr.is_playing:
			socketio.emit("event_progress_changed", {"progress": alplr.get_progress()}, broadcast = True,
						  namespace='/test')

@app.route('/')
def index():
	r = make_response(render_template('base.html', async_mode=socketio.async_mode))
	r.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
	r.headers['Pragma'] = 'no-cache'
	return r
	#return render_template('base.html', async_mode=socketio.async_mode)

@socketio.on('search', namespace = '/test')
def library_search(msg):
	lib = get_lib()
	results = lib.search(msg["needle"])
	
	results_pretty = []
	for result in results:
		results_pretty.append(result.meta)
	emit("event_results_ready", {"results": results_pretty}, namespace="/test")

@socketio.on('add_media', namespace = '/test')
def player_add_media(msg):
	new_media = get_lib().get_media(msg["hash"])
	if new_media is not None:
		get_alplr().add_media(new_media)

@socketio.on('remove_media_at', namespace = '/test')
def player_add_media(msg):
	get_alplr().remove_media_at(msg["index"])


@socketio.on('play', namespace = '/test')
def player_play():
	alplr = get_alplr()
	alplr.play()
	socketio.emit("event_play", {"progress": alplr.get_progress()}, broadcast = True, namespace="/test")

@socketio.on('pause', namespace = '/test')
def player_pause():
	get_alplr().pause()
	emit("event_pause", broadcast = True)

@socketio.on('next', namespace = '/test')
def player_next():
	alplr = get_alplr()
	alplr.next()
	emit("event_track_changed", {"queue_position": alplr.queue_position}, broadcast = True)

@socketio.on('prev', namespace = '/test')
def player_prev():
	alplr = get_alplr()
	alplr.prev()
	emit("event_track_changed", {"queue_position": alplr.queue_position}, broadcast = True)

@socketio.on('queue_position', namespace = '/test')
def player_set_position(msg):
	alplr = get_alplr()
	alplr.set_queue_position(msg["position"])
	emit("event_track_changed", {"queue_position": alplr.queue_position}, broadcast = True)

@socketio.on('volume', namespace = '/test')
def player_set_volume(msg):
	alplr = get_alplr()
	alplr.set_volume(msg["volume"])
	emit("event_volume_changed", {"volume": msg["volume"]}, broadcast = True)

@socketio.on('track_progress', namespace = '/test')
def player_set_progress(msg):
	alplr = get_alplr()
	alplr.set_progress(msg["progress"])
	emit("event_progress_changed", {"progress": msg["progress"]}, broadcast = True)

@socketio.on('connect', namespace='/test')
def player_connect():
	global thread

	if thread is None:
		thread = socketio.start_background_task(target=audio_progress_notify, alplr = get_alplr())

	state = get_alplr().get_state(include_queue = True)
	state.update({"play_cost": config.play_cost})
	emit("event_player_init", state)
	get_alplr().fetch_current_art()

if __name__ == '__main__':
	socketio.run(app, debug=True, host="0.0.0.0", logger=False)
