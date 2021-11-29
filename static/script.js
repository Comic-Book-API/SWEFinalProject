function setCookie(title, img, saleDate, creatorList, buyLink, index) {
    let cookie =  title[index] + "|" + img[index] + "|" + saleDate[index] + "|" + creatorList[index] + "|" + buyLink[index];
    var result = [cookie].join("");
    document.cookie = " ";
    
    document.cookie = result;
    alert (document.cookie);
}

function getCookie() {
    return document.cookie;
}