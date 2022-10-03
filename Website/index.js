// api url
const api_url = 
      "https://462k64bxqd.execute-api.eu-west-2.amazonaws.com/Stage2/items";
  
// Defining async function
async function getapi(url) {
    
    // Storing response
    const response = await fetch(url);
    
    // Storing data in form of JSON
    var data = await response.json();
    console.log(data);
    if (response) {
        hideloader();
    }
    show(data);
}
// Calling that async function
getapi(api_url);
  
// Function to hide the loader
function hideloader() {
    document.getElementById('loading').style.display = 'none';
}
// Function to define innerHTML for HTML table
function show(data) {
    let tab = 
        `<tr>
          <th>Entry On</th>
          <th>Surname</th>
          <th>Service Number</th>        
          <th>Building No.</th>
          <th>Access</th>
         </tr>`;
    
    // Loop to access all rows 
    for (let r of data.Items.reverse()) {
        tab += `<tr> 
    <td>${r.DateTime} </td>
    <td>${r.Surname}</td> 
    <td>${r["Service Number"]}</td>
    <td>${r["Building Number"]}</td>
    <td>${r["Authorised Access?"]}</td>    
   
</tr>`;
    }
    // Setting innerHTML as tab variable
    document.getElementById("homelogs").innerHTML = tab;
}
