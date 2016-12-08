from vlc import *
import datetime, os.path, threading, unicodedata, sacad, re
import hashlib

class EventHook(object):
	def __init__(self):
		self.__handlers = []

	def __iadd__(self, handler):
		self.__handlers.append(handler)
		return self

	def __isub__(self, handler):
		self.__handlers.remove(handler)
		return self

	def fire(self, *args, **keywargs):
		for handler in self.__handlers:
			handler(*args, **keywargs)

class MediaLibrary():
	def __init__(self, import_path = "."):
		instance = Instance()
		self.lib = []
		for root, dirs, files in os.walk(import_path, topdown=False):
			for name in files:
				if name.endswith(".mp3"):
					self.lib.append(AudioMedia(instance, os.path.join(root, name)))
	
	def search(self, needle):
		results = []
		for media in self.lib:
			matching = [(key, val) for key, val in media.meta.items() 
						if (val is not None and needle is not None) and (needle.lower() in str(val).lower())]
			if len(matching) > 0:
				results.append(media)
		return results

	def get_media(self, req_hash):
		req_hash = int(req_hash)
		for item in self.lib:
			if hash(item) == req_hash:
				return item

class AudioMedia():
	def __init__(self, vlc_instance, media):
		if (os.path.isfile(media)):
			self.instance = vlc_instance
			self.media_loc = os.path.abspath(media)
			self.media = self.instance.media_new(self.media_loc)
			self.media.parse()
			self.path_hash = int(hashlib.sha256(self.media_loc.encode()).hexdigest(), 16)
			self.meta = self._get_media_meta()
			self.art_path = None
			self.on_art_ready = EventHook()
		else: 
			raise IOError('File ' + media + ' not found')
	
	def __hash__(self):
		return self.path_hash

	# def __eq__(self, other):
	# 	return isinstance(self, other) and hash(self) == hash(other)

	# def __ne__(self, other):
	# 	return not(self == other)

	def fetch_media_art(self):
		if self.art_path is not None:
			return self.art_path

		if (self.meta["Artist"] is None) or (self.meta["Album"] is None):
			return None

		artdir = "artlib"

		path_concat = os.path.join("static", artdir)
		if not os.path.isdir(path_concat):
			os.makedirs(path_concat)

		filename = self.meta["Artist"] + "-" + self.meta["Album"]
		filename = unicode(unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore'))
		filename = unicode(re.sub('[^\w\s-]', '', filename).strip().lower())
		filename = unicode(re.sub('[-\s]+', '-', filename)) + ".jpg"	
		path_concat = os.path.join(path_concat, filename)
		
		if os.path.isfile(path_concat):
			self.art_path = os.path.join(artdir, filename)
			return self.art_path

		if sacad.search_and_download(
				self.meta["Artist"], 
				self.meta["Album"], 
				sacad.cover.CoverImageFormat.JPEG,
				600,
				25,
				[],
				False,
				path_concat):
			self.art_path = os.path.join(artdir, filename)
			return self.art_path
		else:
			return None

	def _get_media_meta(self):
		meta = {}
		for meta_code, meta_name in Meta._enum_names_.items():
			if (meta_code != 23) and (meta_code != 24) and (meta_code != 25): #these meta codes don't work for some reason
				meta[meta_name] = self.media.get_meta(meta_code)
		meta["Length"] = self.media.get_duration()
		meta["_plrid"] = str(hash(self))
		return meta

class AudioListPlayer():
	instance = Instance()
	
	def _log(self, message):
		if self.debug: 
			timestamp = datetime.datetime.now().strftime('%H:%M:%S')
			print("\033[92m" + timestamp + " AudioListPlayer: \033[0m" + message)

	def fetch_current_art(self):
		if len(self.queue) > 0:
			art_path = self.queue[self.queue_position].fetch_media_art()
			self.on_art_ready.fire(self, art_path)
			self._log("Art ready event")

	def handler_media_playing(self, arg):
		self._log("MediaPlayerPlaying event")
		self.on_playing.fire(self)

	def handler_media_end_reached(self, arg):
		self._log("MediaPlayerEndReached event")

		#After this MediaPlayerEndReached occurs, 
		#MediaPlayer stops responding to all method calls. 
		#As a workaround the player attribute is deleted here 
		#and self.next() method is going to handle this situation by creating new instance of the MediaPlayer
		del self.player 
		
		if self.remove_after_play: 
			self.remove_media_at(self.queue_position)
			self.queue_position -= 1

		if self.next(was_playing = True):
			self.player.play()
			self.queue_end_reached = False
		else:
			self.queue_end_reached = True
			self.is_playing = False
			self._log("Reached end of queue")

		self.on_end_reached.fire(self) 


	def __init__(self, media, default_volume = 100, debug = False, remove_after_play = False):
		self.debug = debug
		self.queue_position = 0
		self.is_playing = False

		queue = []

		for media_item in media:
			queue.append(AudioMedia(self.instance, media_item))

		self.remove_after_play = remove_after_play
		self.queue = queue

		self.queue_end_reached = False
		self.volume = default_volume
		self._make_new_player()
		self.on_end_reached = EventHook()
		self.on_playing = EventHook()
		self.on_art_ready = EventHook()
		self.on_queue_changed = EventHook()
		self._log("AudioListPlayer initialized")

	def __exit__(self):
		self._log("AudioListPlayer destroyed")

	def get_state(self, include_queue = False):
		state = {}
		state["track_progress"] = self.get_progress()
		if len(self.queue) > 0:
			state["track_length"] = self.queue[self.queue_position].media.get_duration()
		else:
			state["track_length"] = 0
		state["volume"] = self.get_volume()
		state["queue_position"] = self.queue_position
		state["is_playing"] = self.is_playing
		if include_queue:
			state["queue"] = self.get_queue_meta()
		return state

	def get_queue_meta(self):
		all_meta = []
		for media_item in self.queue:
			all_meta.append(media_item.meta)
		return all_meta

	def play(self):
		self.is_playing = True
		if not hasattr(self, 'player'): 
			self._make_new_player();

		if (self.player.get_media() is None) and (len(self.queue) > 0):
			threading.Thread(target=self.fetch_current_art).start()
			self.player.set_media(self.queue[self.queue_position].media)
			self._log("MediaPlayer play\n\tNext audio file loaded.\n\tFile has index " + str(self.queue_position) + 
				"\n\tqueue length is " + str(len(self.queue)) + 
				"\n\tFile location is \"" + self.queue[self.queue_position].media_loc + "\"\n")

		self.player.play()
 
	def pause(self):
		if hasattr(self, 'player') and self.is_playing:
			self.player.pause()
			self.is_playing = False
			self._log("MediaPlayer pause")

	def _make_new_player(self):
		if hasattr(self, 'player'): #destroy instance of player if it exists
			self.player.release()
			self._log("Stopped last instance of Player")

		self.player = self.instance.media_player_new()
		self._log("New Player instance created")

		self.set_volume(self.volume)
		self.event_manager = self.player.event_manager()
		self.event_manager.event_attach(EventType.MediaPlayerEndReached, self.handler_media_end_reached)
		self.event_manager.event_attach(EventType.MediaPlayerPlaying, self.handler_media_playing)

		self._log("MediaPlayerEndReached event attached")

	def set_volume(self, i_volume):
		self.volume = i_volume
		if hasattr(self, 'player'): 
			self.player.audio_set_volume(i_volume)
		self._log("Volume set to " + str(i_volume))

	def get_volume(self):
		if hasattr(self, 'player'): 
			return self.player.audio_get_volume()
		else:
			return 0

	def set_progress(self, f_pos):
		self.player.set_position(f_pos)
		self._log("Position set to " + str(f_pos))

	def get_progress(self):
		if hasattr(self, 'player'): 
			progress = self.player.get_position()
			if progress == -1:
				return 0
			return progress
		else:
			return 0

	def get_length(self):
		if hasattr(self, 'player'): 
			return self.player.get_length()
		else:
			return 0

	def set_queue_position(self, position, was_playing = False, force_reload = True):
		if ((position < len(self.queue)) and (position >= 0)):			
			if (self.queue_position != position) or force_reload:
				self.queue_position = position
				self._make_new_player()
				threading.Thread(target=self.fetch_current_art).start()

			self._log("Queue position set to " + str(position))
			if was_playing or self.is_playing:
				self.play()
			return True
		else: 
			self._log("No file with index " + str(position))
			return False

	def next(self, was_playing = False):
		return self.set_queue_position(self.queue_position + 1, was_playing)

	def prev(self, was_playing = False):
		return self.set_queue_position(self.queue_position - 1, was_playing)

	def get_current_audiomedia(self):
		try:
			return self.queue[self.queue_position]  
		except IndexError:
			return None

	def get_audiomedia(self, audiomedia_index):
		try:
			return self.queue[audiomedia_index]
		except IndexError:
			return None

	def insert_media(self, media, pos):
		pass

	def add_media(self, media):
		if media is not None:
			self.queue.append(media)
			self.on_queue_changed.fire(self)

	def remove_media_at(self, index):
		if (index >= 0) and (index < len(self.queue)):

			if (index == self.queue_position):
				if not self.next(was_playing = self.is_playing):
					self.queue_end_reached = True
					self.pause()
					if hasattr(self, 'player'):
						del self.player 

			self.queue.remove(self.queue[index])
			
			if index < self.queue_position:
				self.set_queue_position(self.queue_position - 1)

			self.on_queue_changed.fire(self)
