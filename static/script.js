function setCookie(title, index) {
    document.cookie = title[index];
    alert (document.cookie);
}

function getCookie() {
    return document.cookie;
}