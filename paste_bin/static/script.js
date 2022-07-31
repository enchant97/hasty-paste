async function copy_to_clipboard(text) {
    let result = await navigator.permissions.query({ name: "clipboard-write" });
    if (result.state == "granted" || result.state == "prompt") {
        await navigator.clipboard.writeText(text);
    }
}
