const menu_btn = document.getElementById("menu");
const users_online = document.getElementById("online_user");
let stat_users = false;

menu_btn.addEventListener("click", () => {

    if(stat_users){
        users_online.style.right = null;
    }else{
        users_online.style.right = "0";
    }

    stat_users = !stat_users;

});