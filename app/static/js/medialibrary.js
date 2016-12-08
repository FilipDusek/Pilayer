function MediaLibrary(socket){
	var _this = this;
	_this.results = [];
	_this.on_results_ready = new EventHook();

	this.search = function(needle){
		_this.results = [];
		if(needle.trim()){
			socket.emit('search', {"needle": needle});
		} else {
			console.log("firing with empty results");
			_this.on_results_ready.fire(_this);
		}
	};

	socket.on('event_results_ready', function(msg) {
		console.log("firing with some results");
		_this.results = msg["results"];
		_this.on_results_ready.fire(_this);
	});
}