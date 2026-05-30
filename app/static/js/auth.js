const role = localStorage.getItem("role");

if(!role){
    window.location.href = "/";
}