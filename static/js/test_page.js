sendButton = $('#send');
sendButton.on('click', function() {
  let sample;
  let target;
  // get test parameters
  testParams = {
    size: parseInt($('#size').val()),
    target: parseInt($('#target').val()),
    min_sites: parseInt($('#min_sites').val())
  }

  // get test samples
  $.ajax({
    method: 'POST',
    url: window.location.href,
    contentType: 'application/json',
    data: JSON.stringify({'get_test_sample': testParams}),
    success: function(response) {
      sample = response[0];
      target = response[1];
    }
  }).done(function() {
    // get predicts
    $.ajax({
      method: 'POST',
      url: window.location.href,
      contentType: 'application/json',
      data: JSON.stringify(sample),
      success: function(response) {
        result = document.getElementById('result');
        result.value = '';
        for (let i = 0; i < Object.keys(response[0]).length; i++) {
          result.value += 'Object ' + i + ': P0 = ' + response[0][i].toFixed(4) + ', P1 = ' + response[1][i].toFixed(4) + ', truth class is ' + target[i] + '\n';
        }
      }
    });
  
  });

});
