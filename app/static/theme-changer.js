
let current_theme = "dark";
const light_theme_path = "/style-redo.css";
const dark_theme_path = "/";


function setTheme(theme_name) {
    if (theme_name == "light") {
        swapStyleSheet(light_theme_path);
    } else if (theme_name == "dark") {
        swapStyleSheet(dark_theme_path);
    }
}

function getCookie(cookie_name) {
    let name = cookie_name + "=";
    let decodedCookie = decodeURIComponent(document.cookie);
    let ca = decodedCookie.split(';');
    for(let i = 0; i <ca.length; i++) {
        let c = ca[i];

        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

addEventListener("DOMContentLoaded", (event) => {
    let theme = getCookie("theme");
    if (theme) {
        setTheme(theme);
        current_theme = theme;
    }
});


function swapStyleSheet(sheet) {
    document.getElementById('style').setAttribute('href', sheet);
}

function changeTheme() {
    if (current_theme == "dark") {
        setTheme("light");
        document.cookie = "theme=light" + ";path=/";
        current_theme = "light";
    } else if (current_theme == "light") {
        setTheme("dark");
        document.cookie = "theme=dark" + ";path=/";
        current_theme = "dark";
    }
}

