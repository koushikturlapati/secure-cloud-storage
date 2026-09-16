const dashboard = document.getElemntById("dashboard")

const token =loacalStorage.getItem("access_token");
if (!token)
{
    window.location.href = "login.html";
}

const username = localStorage.getItem("username");
document.getElemntById("username").textContext = username || "User";

