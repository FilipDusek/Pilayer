function User(socket){
	var _this = this;

	this._get_cookie = function(){
		var cookie = Cookies.getJSON('user_auth');
		if (!cookie){
			var dat = {'credit': 10, 'token': '', 'role': 'user'};
			Cookies.set('user_auth', dat);
			cookie = Cookies.getJSON('user_auth');
		}
		console.log(cookie);
		return cookie;
	}

	this.get_role = function(){
		return _this._get_cookie('user_auth')['role'];
	}

	this._set_cookie = function(dat){
		Cookies.set('user_auth', dat);
	}
	
	this.get_balance = function(){
		cookie = _this._get_cookie();
		return cookie['credit'];
	}

	this.get_token = function (){
		var cookie = Cookies.getJSON('user_auth');
		if (cookie){
			return cookie['token'];
		}
		return undefined;		
	}

	this.pay = function(amount){
		// for demo purpuses only, will be removed
		cookie = _this._get_cookie();
		console.log((cookie['credit'] - 1) >= 0);
		console.log(cookie);
		if ((cookie['credit'] - 1) >= 0){
			cookie['credit'] = cookie['credit'] - amount;
			this._set_cookie(cookie);
			return true;
		}
		return false;
	}
}