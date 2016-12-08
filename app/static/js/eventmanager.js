function EventHook(){
	var _this = this;
	_this.listeners = [];

	this.addEventListener = function(func){
		_this.listeners.push(func);
	}

	this.removeEventListener = function(func){
		var index = _this.listeners.indexOf(func);
		if (index > -1) {
			_this.listeners.splice(index, 1);
		}
	}

	this.fire = function(arg){
		for(var i = 0; i < _this.listeners.length; i++){
			_this.listeners[i](arg);
		}
	}
}