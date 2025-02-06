import "./style.css"

const flashes = document.getElementById("flashes");
for (const flash of flashes.children) {
    setTimeout(() => {
        flash.style.opacity = 0;
    }, 4000)
}
