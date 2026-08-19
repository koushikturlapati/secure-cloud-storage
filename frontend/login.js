// Attach an event listener to the form to handle submission
document.getElementById("loginForm").addEventListener("submit", async function(event) {
    event.preventDefault(); // Prevents the default page reload

    // Pass the correct IDs to getElementById
    let username = document.getElementById("username").value;
    let password = document.getElementById("password").value;
    
    try {
        let response = await fetch("http://127.0.0.1:8000/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        });

        let data = await response.json();
        
        if (data.success) {
            alert("Login done");
            window.location.href = "dashboard.html";
        } else {
            alert("Invalid credentials");
        }
    } catch (error) {
        console.error("Error during login:", error);
        alert("Server error occurred.");
    }
});