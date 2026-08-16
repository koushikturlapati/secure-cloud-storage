function login() {
    let username = document.getElementById("username").value;
    let password = document.getElementById("password").value;

    if (username === "admin" && password === "password") {
        alert('Login successful!'); // Successful login
        window.location.href = "dashboard.html";
    } else {
        alert('Invalid username or password.'); // Failed login
    }
}