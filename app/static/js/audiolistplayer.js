function AudioListPlayer(socket, user){
	this.queue = [];
	this.queue_position = 0;
	this.track_progress = 0;
	this.track_progress_real = 0;
	this.volume = 0;
	this.track_length = 0;
	this.is_playing = 0;
	this._before_mute_volume = 100;
	this._disable_progress_update = false;
	this.play_cost = 0;
	this.user = user;
	this.album_art = "";

    var socket = socket;
	var _this = this;


	this.on_refresh = new EventHook();
	this.on_progress_refresh = new EventHook();
	this.on_pay_success = new EventHook();
	this.on_pay_fail = new EventHook();

	socket.on('event_player_init', function(msg) {
		console.log(JSON.stringify(msg));
		_this.volume = msg["volume"];
		_this.is_muted = _this.volume == 0;
		_this.track_length = msg["track_length"];
		_this._track_progress_real = msg["track_progress"];
		_this.track_progress = msg["track_progress"];
		_this.is_playing = msg["is_playing"];
		_this.queue = msg["queue"];
		_this.queue_position = msg["queue_position"];
		_this.play_cost = msg["play_cost"];
		_this.on_refresh.fire(_this);
		_this.on_progress_refresh.fire(_this);
	});

	this.fake_update_progress = function(update_period){
		if (this.is_playing && !_this._disable_progress_update){
			this.track_progress = ((this.track_progress * this.track_length) + update_period) / this.track_length;
			this.on_progress_refresh.fire(_this);
		} 
	}

	fake_update_period = 10;
	setInterval(function() {
	  _this.fake_update_progress(fake_update_period);
	}, fake_update_period);

	this.play = function(){
		socket.emit('play');	
	}

	socket.on('event_play', function(msg) {
		_this.track_progress_real = msg["progress"];
		_this.track_progress = msg["progress"];
		_this.is_playing = true;
		_this.on_refresh.fire(_this);
	});

	this.pause = function(){
		socket.emit('pause');	
	}

	socket.on('event_pause', function() {
		_this.is_playing = false;
		_this.on_refresh.fire(_this);
	});

	socket.on('debug_message', function(msg) {
		console.log(msg);
	});


	this.next = function(){
		socket.emit('next');	
	}

	this.prev = function(){
		socket.emit('prev');
	}

	socket.on('event_track_changed', function(msg) {
		_this.queue_position = msg["queue_position"];
		_this.track_progress = 0;
		_this.track_progress_real = 0;

    	current_meta = _this.queue[_this.queue_position];
    	if (!current_meta){
    		current_meta = {};
    		current_meta["Length"] = 0;
    		_this.album_art = "";
    	}

		_this.track_length = current_meta["Length"];
		_this.on_progress_refresh.fire(_this);
		_this.on_refresh.fire(_this);
	});

	this.set_volume = function(vol){
		socket.emit('volume', {"volume": vol});
	}

	this.mute = function(){
		if (!_this.is_muted){
			_this.set_volume(0);
			_this._before_mute_volume = _this.volume;
		}
	}

	this.unmute = function(){
		if (_this.is_muted){
			_this.set_volume(_this._before_mute_volume);
		}
	}

	socket.on('event_volume_changed', function(msg) {
		_this.volume = msg["volume"];
		
		if (_this.volume == 0){
			_this.is_muted = true;
		} else {
			_this.is_muted = false;
		}

		_this.on_refresh.fire(_this);
	});

	this.set_position = function(pos){
		socket.emit('queue_position', {"position": pos});
	}

	this.set_progress = function(prog){
		socket.emit('track_progress', {"progress": prog});
	}

	socket.on('event_progress_changed', function(msg) {
		_this.track_progress = msg["progress"];
		_this._track_progress_real = msg["progress"];
		_this.on_progress_refresh.fire(_this);
	});

	socket.on('event_art_ready', function(msg) {
		_this.album_art = msg["album_art"];
		_this.on_refresh.fire(_this);
	});

	this.add_media = function (hash){
		user.get_role() == "admin"
		if ((user.get_role() == "admin") ||  (_this.user.pay(_this.play_cost))){
			socket.emit("add_media", {"hash": hash});
			_this.on_pay_success.fire(_this);
		} else {
			_this.on_pay_fail.fire(_this);
		}
	}

	this.remove_media_at = function (index){
		socket.emit("remove_media_at", {"index": index});
	}

	socket.on('event_queue_changed', function(msg) {
		_this.queue = msg["queue"];
		_this.queue_position = msg["queue_position"];
		_this.on_refresh.fire(_this);
	});
}