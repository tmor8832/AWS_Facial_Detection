

function details() {
    console.log(document.forms["visitor"]["serviceno"].value);
    console.log(document.forms["visitor"]["rank"].value);
    console.log(document.forms["visitor"]["firstname"].value);
    console.log(document.forms["visitor"]["lastname"].value);
    console.log(document.forms["visitor"]["pid"].value);
    
}
function displaylogs() {
    console.log(document.forms["logs"]["entrydate"].value);
    console.log(document.forms["logs"]["entrytime"].value);
    console.log(document.forms["logs"]["exitdate"].value);
    console.log(document.forms["logs"]["exittime"].value);

}

fetch('https://462k64bxqd.execute-api.eu-west-2.amazonaws.com/Stage2/items')
// fetchRes is the promise to resolve
// it by using.then() method
.then(response => response.json())
.then(data => console.log(data));


function find() {
    document.getElementById("initial-search").search();
}

function find() {
    let x = document.getElementById("initial-search").value;
}
// if (x == "") {
// alert("");
// return false;
