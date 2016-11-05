$( document ).ready(function() {
	alplr = new AudioListPlayer();

	$(".player-action-play").click(function(){
		alplr.play();
	});

	$(".player-action-pause").click(function(){
		alplr.pause();
	});

	$(".player-action-next").click(function(){
		alplr.next();
	});

	$(".player-action-prev").click(function(){
		alplr.prev();
	});
	
	$(".player-progress").slider({
		min: 0.0001,
		max: 1,
		value: 0,
		step: 0.0001,
		slide: function( event, ui ) {
			alplr.set_progress(ui.value);
		}
    });

	$(".player-volume").slider({
		min: 1,
		max: 100,
		value: 0,
		step: 1,
		slide: function( event, ui ) {
			alplr.set_volume(Math.round(Math.log10(ui.value)*50));
		}
    });

    alplr.on_refresh = function(instance){
    	$(".player-volume").slider('value', Math.pow(10, (instance.volume / 50)));
    	$(".player-audio-title").text(instance.playlist[instance.playlist_position]["Title"]);
    	$(".player-playlist").html(get_playlist_html(instance));
		$(".player-playlist li").on("click", function(){
			alplr.set_position($(this).data("index"));
		});
    }

    alplr.on_progress_refresh = function(instance){
    	$(".player-progress").slider('value', instance.song_progress);
    }

    function get_playlist_html(instance){
    	playlist = [];
    	playlist.push("<ul class='playlist'>");
		$.each(instance.playlist, function( index, value ) {
			if (index == instance.playlist_position){
				playlist.push("<li class='active' data-index='" + String(index) + "'>" + value["Title"] + "</li>");
			} else {
				playlist.push("<li data-index='" + String(index) + "'>" + value["Title"] + "</li>");
			}
		});
    	playlist.push("</ul>");

    	$( ".playlist" ).sortable();
    	$( ".playlist" ).disableSelection();
    	return playlist.join("\n");
    }
});