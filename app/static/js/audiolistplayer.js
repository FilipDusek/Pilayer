function AudioListPlayer(type){
	this.playlist = [];
	this.log = [];
	this.playlist_position = 0;
	this.song_progress = 0;
	this.song_progress_real = 0;
	this.volume = 0;
	this.is_playing = 0;
	this.on_refresh = undefined;
	this.on_progress_refresh = undefined;

	instance = this;
	//asd

	this.refresh = function(){
		instance = this;
		$.ajax({
			url: "/player/state"
	 	}).done(function( data ) {
	 		data = JSON.parse(data);
			instance.volume = data["volume"];
			instance.length = data["length"];
			instance._song_progress_real = data["progress"];
			instance.song_progress = data["progress"];
			instance.is_playing = data["is_playing"];
			instance.playlist = data["playlist"];
			instance.playlist_position = data["playlist_position"];
			instance._refresh_notify();
			instance._progress_refresh_notify();
		}).fail(function(jqXHR, textStatus){
			instance._log(2, "get state failed (AJAX): " + textStatus)
		});  
	}

	this.update_progress = function(update_period){
		if (this.is_playing){
			this.song_progress = ((this.song_progress * this.length) + update_period) / this.length
			if (this.song_progress > 1){ //song ended, request info about new song
				this.refresh(); 
			} else {
				this._progress_refresh_notify();
			}
		}
	}

	instance.refresh();
	setInterval(function() {
	  instance.refresh();
	}, 2000);
	setInterval(function() {
	  instance.update_progress(10);
	}, 10);

	this.refresh();

	this._log = function(event_type, message){
		switch(event_type){
			case 1: 
				this.log.push("AudioListPlayer warning: " + message);
				console.warn(this.log[this.log.length-1])
				break;
			case 2: 
				this.log.push("AudioListPlayer error: " + message);
				console.error(this.log[this.log.length-1])
				break;
			default:
				this.log.push("AudioListPlayer: " + message);
				console.info(this.log[this.log.length-1])
		} 
	}

	this._dump_log = function(){
		console.log(this.log);
	}

	this._progress_refresh_notify = function(){
		if (instance.on_progress_refresh != undefined){
			instance.on_progress_refresh(instance);
		}
	}

	this._refresh_notify = function(){
		if (instance.on_refresh != undefined){
			instance.on_refresh(instance);
		}
	}

	this.load_playlist = function(){
		instance = this;
		$.ajax({
			url: "/player/playlist/all/meta/"
		}).done(function( data ) {
			this.playlist = data;
		}).fail(function(jqXHR, textStatus){
			instance._log(2, "load playlist failed (AJAX): " + textStatus)
		});
	}

	this._send_command = function(command, method = "GET"){
		instance = this;
		$.ajax({
			method: method,
			url: command
		}).fail(function(jqXHR, textStatus){
			instance._log(2, command + " failed (AJAX " + method + "): " + textStatus);
		});
	}

	this.play = function(){
		this._send_command("/player/play");
		this.is_playing = true;
		this._refresh_notify();
	}

	this.pause = function(){
		this._send_command("/player/pause");
		this.is_playing = false;
		this._refresh_notify();
	}

	this.next = function(){
		this._send_command("/player/next");
		this.refresh();
	}

	this.prev = function(){
		this._send_command("/player/prev");
		this.refresh();
	}

	this.set_volume = function(vol){
		this._send_command("/player/volume/" + String(vol), "PUT");
		this.volume = vol;
		this._refresh_notify();
	}

	this.set_position = function(pos){
		this._send_command("/player/position/" + String(pos), "PUT");
		this.playlist_position = pos;
		this._refresh_notify();
	}

	this.set_progress = function(prog){
		this._send_command("/player/progress/" + String(prog), "PUT");
		this.song_progress = prog;
		this._refresh_notify();
	}

	this.load_playlist()
}