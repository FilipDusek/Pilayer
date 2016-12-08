/* Functions controlling the information flow between view and AudioListPlayer and MediaLibrary */

var namespace = '/test';
socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace); 

var user = new User(socket);
var alplr = new AudioListPlayer(socket, user);
var lib = new MediaLibrary(socket);

$( document ).ready(function() {
	/* Actions */
	$(".player-action-play").click(function(){ alplr.play(); });
	$(".player-action-pause").click(function(){ alplr.pause(); });
	$(".player-action-next").click(function(){ alplr.next(); });
	$(".player-action-prev").click(function(){ alplr.prev(); });
	$('.player-action-search-input').on('input', function() { lib.search($(this).val()); });

	$(".player-action-toggle-play").click(function(){
		if (alplr.is_playing){
			alplr.pause();
			$(".player-action-toggle-play").removeClass("is-playing").addClass("is-paused");
		} else {
			alplr.play();
			$(".player-action-toggle-play").addClass("is-playing").removeClass("is-paused");
		}
	});

	/* Element initializations */
	$(".player-element-progress").slider({
		range: "min",
		min: 0.0001,
		max: 1,
		value: 0,
		step: 0.0001,
		start: function(event, ui){
			alplr._disable_progress_update = true;			
		},
		stop: function( event, ui ) {
			alplr._disable_progress_update = false;
			alplr.set_progress(ui.value);
		}
    });

	$(".player-element-volume").slider({
		range: "min",
		min: 1,
		max: 100,
		value: 0,
		step: 1,
		stop: function( event, ui ) {
			alplr.set_volume(Math.round(Math.log10(ui.value)*50));
		}
    });

	/* AudioListPlayer refresh handlers */
	alplr.on_refresh.addEventListener(function(instance){
    	$(".player-element-volume").slider('value', Math.pow(10, (instance.volume / 50)));
    	
    	current_meta = instance.queue[instance.queue_position];
    	if (!current_meta){
    		current_meta = {};
    		current_meta["Title"] = "";
    		current_meta["Album"] = "";
    		current_meta["Artist"] = "";
    	}

    	$(".player-binding-artist").text(current_meta["Artist"]);
    	$(".player-binding-album").text(current_meta["Album"]);
    	$(".player-binding-title").text(current_meta["Title"]);
    	$(".player-element-queue").html(get_queue_html(instance));
		
		var ico = "\u23F8"; //pause char
		if (alplr.is_playing){
			ico = "\u25B6"; //play char
		}

    	document.title = ico + " " + current_meta["Title"] + " - " + current_meta["Artist"];

		if (instance.is_muted){
			$(".player-binding-volume-status").removeClass("volume-up").addClass("volume-off");
		} else {
			$(".player-binding-volume-status").removeClass("volume-off").addClass("volume-up");
		}
		
		$(".player-element-queue li").on("click", function(){
			alplr.set_position($(this).data("index"));
		});

		if (instance.album_art){
			$(".player-binding-art").css("background-image", "url(" + instance.album_art + ")");
		} else {
			$('.player-binding-art').removeAttr('style');
		}
		
		if (!alplr.is_playing){
			$(".player-action-toggle-play").removeClass("is-playing").addClass("is-paused");
		} else {
			$(".player-action-toggle-play").addClass("is-playing").removeClass("is-paused");
		}
    });

    alplr.on_progress_refresh.addEventListener(function(instance){
    	$(".player-element-progress").slider('value', instance.track_progress);
    	$(".player-binding-length").text(milistotime(instance.track_length));
    	$(".player-binding-played").text(milistotime(instance.track_length*instance.track_progress));
    });

    /* Media library handler */
	lib.on_results_ready.addEventListener(function(lib){
    	$(".player-element-search-results").html(get_results_html(lib));
    	$(".player-element-search-results ul li").click(function(){
    		alplr.add_media($(this).data("plrid"));
    		lib.results = [];
    	});
	});


    /* HTML generators */
    function get_queue_html(instance){
    	queue = [];
    	queue.push("<ul class='queue'>");
		$.each(instance.queue, function( index, value ) {

			if (index == instance.queue_position){
				extra_class = "active"; 
			} else {
				extra_class = "";
			}
			queue.push("<li class='" + extra_class +"' data-index='" + String(index) + "'>");
			queue.push("<div class='queue-song-title'>" + String(index+1) + ". " + value["Title"] + "</div>"); 
			queue.push("<div class='queue-song-artist'>" + (value["Artist"] == null ?  "" : value["Artist"]) + "</div>"); 
			queue.push("</li>");

		});
    	queue.push("</ul>");

    	return queue.join("\n");
    }
    
    function get_results_html(lib){
    	results = [];
    	results.push("<ul class='results'>");
		$.each(lib.results, function( index, value ) {
			results.push("<li data-plrid='" + value["_plrid"] + "'>");
			results.push("<div class='results-song-title'>" + value["Title"] + "</div>"); 
			results.push("<div class='results-song-artist'>" + (value["Artist"] == null ?  "" : value["Artist"]) + "</div>"); 
			results.push("<span class='pull-right glyphicon glyphicon-plus-sign'></span>");
			results.push("</li>");

		});
    	results.push("</ul>");

    	return results.join("\n");
    }

    /* Other helpers */
    function milistotime(milis){
    	var ms = milis,
		   min = Math.floor((ms/1000/60)),
		   sec = Math.floor((ms/1000)) % 60;
		sec = String(sec);
		sec = sec.length > 1 ? sec : "0" + sec;  
		return min + ":" + sec;
    }

});