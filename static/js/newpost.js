$(document).ready(function() {
  $("#newpost_button").click(function(e) {
    $("#newpost_modal").modal("show");
  });

  $("#newpost_submit").click(function(e) {
    $.ajax({
      url: '/blog/ajax/article/add',
      type: "POST",
      data: {
        'title': $("#newpost_title").val(),
        'categories': $("#newpost_tags").val(),
        'content': $("#newpost_content").val()
      },
      success: function(data) {
        if (data.success) {
          $("#newpost_modal").modal("hide");
          location.reload()
        }
        else {

        }
      },
      error: function(xhr, msg, exp) {
        alert(msg)
      }
    });
  })
});
