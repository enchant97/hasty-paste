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

    //highlighter_name.value = highlighter_value;

    //for (let i = 0; i < data_list.options.length; i++) {
        //if (data_list.options[i].value === highlighter_value) {
            //return true;
        //}
    //}

    //alert("Unknown highlighter name");
	//highlighter_name.value = "";
	//highlighter_name.focus();

	//return false;
// Check if the entered highlighter value is in the list of options
    let found = false;
    for (let i = 0; i < data_list.options.length; i++) {
        if (data_list.options[i].value === highlighter_value) {
            found = true;
            break;
        }
    }

    if (!found) {
        // Unknown highlighter name, set default and continue form submission
        highlighter_name.value = "text";
    } else {
        // Known highlighter name, set entered value in lowercase
        highlighter_name.value = highlighter_value;
    }

    return true; // Allow form submission
}

function enable_copy_share_link() {
    const href = location.href;
    if (!href.startsWith("https://")) { return; }
    const $bnt = document.getElementById("copy-share-link-bnt");
    $bnt.addEventListener("click", _ => { copy_to_clipboard(href); });
    $bnt.removeAttribute("disabled");
}
