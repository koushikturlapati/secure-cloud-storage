document.getElementById("createAccountForm")
.addEventListener("submit", async function(event) {

    event.preventDefault();

    const username =
        document.getElementById("username").value;

    const password =
        document.getElementById("password").value;

    const confirmpassword =
        document.getElementById("confirmpassword").value;

    const response = await fetch(
        "http://127.0.0.1:8000/createacc",
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username: username,
                password: password,
                confirmpassword: confirmpassword
            })
        }
    );

    const data = await response.json();

    if (data.success) {
        alert("Account created successfully");
        window.location.href = "login.html";
    } else {
        alert(data.message);
    }
});