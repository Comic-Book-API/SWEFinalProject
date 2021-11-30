function setCookie(title, img, saleDate, creatorList, buyLink, index) {
    let cookie =  title[index] + "|" + img[index] + "|" + saleDate[index] + "|" + creatorList[index] + "|" + buyLink[index];
    var result = [cookie].join("");
    document.cookie.split(";").forEach(function(c) { document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/"); });
    
    document.cookie = result;
}

function getCookie() {
    return document.cookie;
}

function setTitle(title, index) {
    var title = title[index];
}

function setImg(img, index) {
    var img = img[index];
}

function setSaleDate(saleDate, index) {
    var saleDate = saleDate[index];
    alert (saleDate);
}

function setCreatorList(creatorList, index) {
    var creatorList = creatorList[index];
}

function setBuyLink(buyLink, index) {
    var buyLink = buyLink[index];
}

function getTitle() {
    alert (title);
    return title;
}

function getImg() {
    alert (img)
    document.getElementById("image").src = img;
    return img;
}

function getOnSaleDate() {
    return saleDate;
}

function getCreatorList() {
    return creatorList;
}

function getBuyLink() {
    return buyLink;
}
