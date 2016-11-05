from vlc import *
import datetime
import os.path
class AudioMedia():
	def __init__(self, vlc_instance, media):
		if (os.path.isfile(media)):
			self.instance = vlc_instance
			self.media_loc = media
			self.media = self.instance.media_new(media)
			self.meta = self._get_media_meta()
		else: 
			raise IOError('File ' + media + ' not found')

	def _get_media_meta(self):
		meta = {}
		for meta_code, meta_name in Meta._enum_names_.items():
			meta[meta_name] = self.media.get_meta(meta_code)
		return meta

class AudioListPlayer():
	instance = Instance()
	
	def _log(self, message):
		if self.debug: 
			timestamp = datetime.datetime.now().strftime('%H:%M:%S')
			print("\033[92m" + timestamp + " AudioListPlayer: \033[0m" + message)

	def handler_media_end_reached(self, arg):
		self._log("MediaPlayerEndReached event")

		#After this event (MediaPlayerEndReached) occurs, 
		#MediaPlayer is not responding to any method calls (probably because it was destroyed). 
		#That's why the player attribute is deleted here, 
		#self.next() method is going to handle this situation by creating new instance of the MediaPlayer
		del self.player 

		if self.next(was_playing = True):
			self.player.play()
		else:
			self.playlist_end_reached = True
			self.is_playing = False
			self._log("Reached end of playlist")

	def __init__(self, media, default_volume = 100, debug = False):
		self.debug = debug
		self.playlist_position = 0
		self.is_playing = False

		playlist = []

		for media_item in media:
			playlist.append(AudioMedia(self.instance, media_item))
		self.playlist = playlist

		self.playlist_end_reached = False
		self.volume = default_volume
		self._make_new_player()
		self._log("AudioListPlayer initialized")

	def __exit__(self):
		self._log("AudioListPlayer destroyed")

	def play(self):
		self.is_playing = True
		if not hasattr(self, 'player'): 
			self._make_new_player();

		if self.player.get_media() is None:
			self.player.set_media(self.playlist[self.playlist_position].media)
			self._log("MediaPlayer play\n\tNext audio file loaded.\n\tFile has index " + str(self.playlist_position) + 
				"\n\tPlaylist length is " + str(len(self.playlist)) + 
				"\n\tFile location is \"" + self.playlist[self.playlist_position].media_loc + "\"\n")

		self.player.play()

	def pause(self):
		self.is_playing = False
		if hasattr(self, 'player'):
			self.player.pause()
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

	def set_position(self, f_pos):
		self.player.set_position(f_pos)
		self._log("Position set to " + str(f_pos))

	def get_position(self):
		if hasattr(self, 'player'): 
			return self.player.get_position()
		else:
			return 0

	def get_length(self):
		if hasattr(self, 'player'): 
			return self.player.get_length()
		else:
			return 0

	def set_playlist_position(self, position, was_playing = False):
		if ((position < len(self.playlist)) and (position >= 0)):			
			self.playlist_position = position	
			if was_playing or self.is_playing:
				self._make_new_player();
				self.play()
			return True
		else: 
			self._log("No file with index " + str(position))
			return False

	def next(self, was_playing = False):
		return self.set_playlist_position(self.playlist_position + 1, was_playing)

	def prev(self, was_playing = False):
		return self.set_playlist_position(self.playlist_position - 1, was_playing)

	def get_current_audiomedia(self):
		try:
			return self.playlist[self.playlist_position]  
		except IndexError:
			return None

	def get_audiomedia(self, audiomedia_index):
		try:
			return self.playlist[audiomedia_index]
		except IndexError:
			return None

	def insert_media(self, media):
		pass

	def add_media(self, media):
		pass

	def remove_media_at(self, index):
		pass

# lplr = AudioListPlayer(["/mnt/nfs/sounds/a.mp3",
# 						"/mnt/nfs/sounds/asharp.mp3", 
# 						"/mnt/nfs/sounds/b.mp3", 
# 						"/mnt/nfs/sounds/c.mp3", 
# 						"/mnt/nfs/sounds/csharp.mp3"]*2, 100, True)
# lplr.play()
# i = 0
# while not lplr.playlist_end_reached:
# 	i += 1
# 	time.sleep(0.5)
# 	lplr.next()