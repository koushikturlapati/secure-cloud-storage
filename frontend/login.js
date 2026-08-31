const loginForm = document.getElementById("loginForm");
const loginMessage = document.getElementById("formMessage");

function showLoginMessage(message, isError = false) {
    loginMessage.textContent = message;
    loginMessage.classList.toggle("error", isError);
    loginMessage.classList.toggle("success", !isError);
}

loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;
    const submitButton = loginForm.querySelector("button[type='submit']");

    submitButton.disabled = true;
    showLoginMessage("Logging in...");

    try {
        const response = await fetch("http://127.0.0.1:8000/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });
        const data = await response.json();

        if (!response.ok || !data.success) {
            showLoginMessage(data.message || "Invalid username or password.", true);
            return;
        }

        showLoginMessage("Login successful. Redirecting...");
        window.setTimeout(() => {
            window.location.href = "dashboard.html";
        }, 500);
    } catch (error) {
        console.error("Error during login:", error);
        showLoginMessage("Could not reach the server. Please try again.", true);
    } finally {
        submitButton.disabled = false;
    }
});
