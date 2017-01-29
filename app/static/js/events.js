/* Functions specific to current template */
$( document ).ready(function() {
	$(".player-action-search-toggle").click(function(){
		var search_focus = false;
		if($(".player-action-search-input").is(":hidden"))
		{
			show_search = true;
		} else {
			$(".player-element-queue").show();
			$(".player-element-search-results").html("");
		}
		$(".player-action-search-input").slideToggle(100, function() {
        	if (show_search){
        		$(".player-action-search-input").focus();
				$(this)[0].scrollIntoView();
			} else {
	        	$(".player-action-search-input").val("");
			}
    	});
	});

	alplr.on_pay_fail.addEventListener(function(lib){
		show_toast(3500, "Damn, you don't have any credits and there is nothing you can do about it, because we didn't implement part where you can buy credits yet.");
	});

	
	alplr.on_pay_success.addEventListener(function(lib){
		if ((user.get_role() == "admin") || (alplr.play_cost == 0)){
			show_toast(1000, "Looks cool!");
		} else {
			show_toast(3500, "Looks cool! I took " + lib.play_cost + " credits for it. You have " + user.get_balance() + " credits.");
		}
	});

	lib.on_results_ready.addEventListener(function(lib){
		if(lib.results.length == 0){
			$(".player-element-queue").show();
			$(".player-element-search-results").hide();
		} else {
			$(".player-element-queue").hide();
			$(".player-element-search-results").show();
		}

    	$(".player-element-search-results ul li").click(function(){
        	$(".player-action-search-input").val("");
        	$(".player-action-search-input").slideUp(100);
			$(".player-element-queue").show();
			$(".player-element-search-results").hide();
    	});
	});
	
	$(".player-binding-volume-status").doubletap(
	    function(event){
	        if ($(".player-binding-volume-status").hasClass("volume-up")){
	        	alplr.mute();
	        } else {
	        	alplr.unmute();
	        }
	    },
	    function(event){
			$(".player-element-volume").slideToggle(100);
	    }, 200);

    function show_toast(milis, msg){
    	$('.toast-msg').text(msg);
    	$('.toast-msg').stop().fadeIn(200).delay(milis).fadeOut(200);
    }
});