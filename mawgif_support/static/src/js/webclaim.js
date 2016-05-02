$(document).ready(function() {
                console.log('from website_claim module1');
                $('#city').on('change', function() {
                                city_id = $("#city").val();
                                console.log('on click send' + city_id);

                                openerp.jsonRpc("/mawgif/get_state", 'call', {
            'city_id': city_id})
                                .then(function(res) {
                                                $('#dist').replaceWith(res)
                                });

                });
                
                $('#attachment').on('change', function() {
                                // If there is (at least) one file selected
                                  if (this.files[0].size > 0) {
                                     if (this.files[0].size > 1 * 1024 * 1024) { // Check the constraint
                                                 this.setCustomValidity("File size should not exceed 1 MB -- 1 MB وينبغي ألا يتجاوز حجم الملفات");
                                                 return;
                                     }
                                  }
                                  // No custom constraint violation
                                this.setCustomValidity("");  
                });
                
                $('#attachment2').on('change', function() {
                                // If there is (at least) one file selected
                                  if (this.files[0].size > 0) {
                                     if (this.files[0].size > 1 * 1024 * 1024) { // Check the constraint
                                                 this.setCustomValidity("File size should not exceed 1 MB -- 1 MB وينبغي ألا يتجاوز حجم الملفات");
                                                 return;
                                     }
                                  }
                                  // No custom constraint violation
                                this.setCustomValidity("");  
                });
                
                $('.staff').on('keyup', function() {
                	if($('.staff-head').val() != "") {
                		$('.staff-tail').prop('required', true);
                		$('.staff-head').prop('required', false);
                	} else {
                		$('.staff-tail').prop('required', false);
                	}
                	if($('.staff-tail').val() !== "") {
                		$('.staff-head').prop('required', true);
                		$('.staff-tail').prop('required', false)
                	} else {
                		$('.staff-head').prop('required', false);
                	}
                });
                
//                var placeholder_text = $('form input:text');
//                console.log(placeholder_text.length);

//                Array.prototype.forEach.call(placeholder_text, function(elem) {
//                    elem.placeholder = elem.placeholder.replace(/\\n/g, '\n');
//                });
                
               $('#plate_type').on('change', function(){
            	   console.log('selected' + $("#plate_type").val());
            	   if($('#plate_type option:selected').val() === '7') {
            		   
            		   $('.oplt-type').css('display','block');
            	   } else {
            		   $('.oplt-type').css('display','none');
            	   }
               });
                
});

//var textAreas = document.getElementsByTagName('text');
//Array.prototype.forEach.call(textAreas, function(elem) {
//	alert('here')
//    elem.placeholder = elem.placeholder.replace(/\\n/g, '\n');
//});


function chkDesc(textarea) {
    if (textarea.value.length > 1000) {
        textarea.setCustomValidity("Text should not exceed 1000 character يجب أن لا يتجاوز النص 1000 حرف");
        return false;
    }else if(textarea.value == '') {
        textarea.setCustomValidity('Please fill the required field من فضلك لا يمكن ترك هذا الحقل فارغا');
    } 
    else {
        textarea.setCustomValidity('');
    }
}

function InvalidMsg(textbox) {

    if(textbox.name == 'customer_email') {
        if(textbox.validity.typeMismatch) {
                console.log('in email');
            textbox.setCustomValidity('Please enter the valid email من فضلك اضف الجزء بعد @ للبريد الالكتروني');
        } else {
            textbox.setCustomValidity('');
        }
    } 
    else {
        if(textbox.validity.patternMismatch){
            textbox.setCustomValidity('Enter mobile without leading 0  من فضلك ادخل رقم الموبايل بدون صفر في البداية');
        } 
        else if(textbox.value == '') {
            console.log(textbox.name);
                    textbox.setCustomValidity('Please fill the required field من فضلك لا يمكن ترك هذا الحقل فارغا');
        } 
        else {
            textbox.setCustomValidity('');
        }
    }
    return true;
}
