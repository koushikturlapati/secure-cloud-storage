const createAccountForm = document.getElementById("createAccountForm");
const createAccountMessage = document.getElementById("formMessage");

function showMessage(message, isError = false) {
    createAccountMessage.textContent = message;
    createAccountMessage.classList.toggle("error", isError);
    createAccountMessage.classList.toggle("success", !isError);
}

createAccountForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;
    const confirmpassword = document.getElementById("confirmpassword").value;
    const submitButton = createAccountForm.querySelector("button[type='submit']");

    if (password !== confirmpassword) {
        showMessage("Passwords do not match.", true);
        return;
    }

    submitButton.disabled = true;
    showMessage("Creating your account...");

    try {
        const response = await fetch("http://127.0.0.1:8000/createacc", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password, confirmpassword })
        });
        const data = await response.json();

        if (!response.ok || !data.success) {
            showMessage(data.message || "Unable to create the account.", true);
            return;
        }

        createAccountForm.reset();
        showMessage("Account created. Redirecting to login...");
        window.setTimeout(() => {
            window.location.href = "index.html";
        }, 800);
    } catch (error) {
        console.error("Error creating account:", error);
        showMessage("Could not reach the server. Please try again.", true);
    } finally {
        submitButton.disabled = false;
    }
});
