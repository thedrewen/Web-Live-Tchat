const sock = new WebSocket("wss://thedrewen.com:4026");
const msgs = document.getElementById("msgs");

let username = "user" + Math.floor(Math.random() * 100);
document.getElementById("change_pseudo").placeholder = username;

sock.addEventListener("open", (event) => {

    console.info("Connexion établie avec le server !")
    
    sock.send(JSON.stringify({"Connexion" : {"author" : username, "type" : "open"}}))
    
    if(typeof localStorage !== "undefined" && localStorage !== null){
        let mdp = localStorage.getItem('mdp');
        mdp = mdp.replace(" ", "");
        if(mdp != "" && mdp != null && mdp != undefined && mdp != "undefined"){
            sock.send(JSON.stringify({"Admin" : {"type" : "!login "+mdp}}));
        }
    }


});

sock.addEventListener("close", (event) => {

    console.warn("Connexion fermée avec le server !")

    sendMessage("Connexion fermé avec le serveur...", "warn")

});

sock.addEventListener("error", (event) => {
    console.error("Une erreur s'est produite !")
    sendMessage("Erreur avec le serveur...", "warn")
});

sock.addEventListener("message", (event) => {

    console.log(event.data)

    let data = JSON.parse(event.data);
    
    if("Message" in data){
        sendMessage(data['Message']['author'] +"> "+data['Message']['content'], "Message");
    }else if("Connexion" in data){
        const users_div = document.getElementById("users");
        if(data["Connexion"]['type'] == "open"){
            const user_div = document.createElement("div");
            user_div.classList.add("user");
            user_div.id = data["Connexion"]['author'];
    
            user_div.textContent = data["Connexion"]['author'];

            users_div.appendChild(user_div);
        }else if(data["Connexion"]['type'] == "close"){
            const user_div = document.getElementById(data["Connexion"]['author']);

            users_div.removeChild(user_div);
        }

    }else if("Action" in data){
        
        if(data["Action"]["type"] == "rename"){
            
            const user_div = document.getElementById(data["Action"]["author"]);

            user_div.id = data["Action"]["data"];

            user_div.textContent = data["Action"]["data"];

            if (data["Action"]["author"] == username){

                username = data["Action"]["data"];

                document.getElementById("change_pseudo").placeholder = username;
            }

        }
        
    }else if("System" in data){
        
        if(data["System"]["type"] == "warn"){
            sendMessage("System> "+data["System"]["data"], "warn")
        }else if(data["System"]["type"] == "info"){
            sendMessage("System> "+data["System"]["data"], "info")
        }else if(data["System"]["type"] == "clear"){
            msgs.innerHTML = '';
        }
        
    }
});

document.getElementById("submit").addEventListener("click", () => {

    const input = document.getElementById("msgs_input");
    let message = input.value;
    if(message[0] == "!"){
        input.value = "";
        if(localStorage && message.split(" ")[0] == "!login"){
            let mdp = message.split(" ")[1];
            localStorage.setItem('mdp', mdp);
        }else if(message.split(" ")[0] == "!logout"){
            localStorage.setItem('mdp', "");
        }
        sock.send(JSON.stringify({"Admin" : {"type" : message}}));
    }else if(message != ""){
        input.value = "";
        sock.send(JSON.stringify({"Message" : {"author" : username, "content" : message.replace("\\n", "\n")}}))
    }

});

document.getElementById("submit_pseudo").addEventListener("click", () => {

    const input = document.getElementById("change_pseudo");
    let message = input.value;
    if(message != ""){
        input.value = "";
        sock.send(JSON.stringify({"Action" : {"type" : "rename", "author" : username, "data" : message}}))
    }
});

document.getElementById("submit_channel").addEventListener("click", () => {
    const input = document.getElementById("change_channel");
    let message = input.value;
    if(message != "" && message.length < 7){
        document.getElementById("users").innerHTML = '<div class="user" style="color: red;">System</div>';
        input.value = "";
        input.placeholder = message;
        sock.send(JSON.stringify({"Action" : {"type" : "joinChannel", "author" : username, "data" : message}}))
    }
});


document.getElementById("msgs_input").addEventListener("keydown", function(event) {
    if (event.key === "Enter" && !event.shiftKey && !isMobileDevice()) {
        event.preventDefault();
        document.getElementById("submit").click(); 
    }
});

document.getElementById("change_pseudo").addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
        event.preventDefault();
        document.getElementById("submit_pseudo").click(); 
    }
});
document.getElementById("change_channel").addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
        event.preventDefault();
        document.getElementById("submit_channel").click(); 
    }
});


function isMobileDevice() {
    return typeof window.orientation !== "undefined" || navigator.userAgent.indexOf("Mobile") !== -1;
}



  function sendMessage(text, type) {
    const divMsg = document.createElement("div");
    const pText = document.createElement("p");

    pText.classList.add(type);

    let texts = text.split("\n");
    let taille = texts.length;
    let i = 1;
    for (let txt of texts) {
        if(i != 1 && i != i < taille - 1){
            let lineBreak = document.createElement("br"); 
            pText.appendChild(lineBreak);
        }
        pText.appendChild(document.createTextNode(txt));
        i++;
    }
    

    divMsg.appendChild(pText);
    msgs.appendChild(divMsg);

    msgs.scrollTop = msgs.scrollHeight;

    if(!document.hasFocus()){
        let audio = new Audio("./assets/notif.mp3");
        audio.play();
    }
    

}
