let editor;
window.onload = function(){
    editor = ace.edit("editor");
    editor.setTheme("ace/theme/monokai");
    editor.session.setMode("ace/mode/c_cpp");
}

function changeLang(){
    let language = $("#languages").val()
    if (language == "c")editor.session.setMode("ace/mode/c_cpp")
    else if (language == "python")editor.session.setMode("ace/mode/python")
}

function execute() {
    let csrf_token = $("meta[name=csrf_token]").attr("content");
    $.ajax({
        url: "/code%20space",  // Adjust the URL to match your Flask route
        method: "POST",
        data: {
            language: $("#languages").val(),
            code: editor.getSession().getValue(),
            csrf_token: csrf_token  // Include the CSRF
        },
        success: function(response) {
            console.log('success')
            response = response.replace(/\n/g, '<br>')
            $(".output").html(response)
         }
    });
}