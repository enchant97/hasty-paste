function copy_to_clipboard(text) {
    navigator.permissions.query({ name: "clipboard-write" }).then(async result => {
        if (result.state == "granted" || result.state == "prompt") {
            await navigator.clipboard.writeText(text);
        }
    }).catch(_ => navigator.clipboard.writeText(text));
}

function validate_new_post_form() {
    let data_list = document.getElementById("highlighter-names");
    let highlighter_name = document.getElementById("highlighter-name");
    let highlighter_value = highlighter_name.value.toLowerCase();

    if (highlighter_value === "") { return true; }

    highlighter_name.value = highlighter_value;

    for (let i = 0; i < data_list.options.length; i++) {
        if (data_list.options[i].value === highlighter_value) {
            return true;
        }
    }

    alert("Unknown highlighter name");
    highlighter_name.focus();

    return false;
}
