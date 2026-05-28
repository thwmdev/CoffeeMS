async function login() {

    const username =
        document.getElementById("username").value

    const password =
        document.getElementById("password").value

    const response = await fetch(
        "http://127.0.0.1:5000/api/auth/login",
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username,
                password
            })
        }
    )

    const data = await response.json()

    console.log(data)

    if(data.token){

        localStorage.setItem(
            "token",
            data.token
        )

        localStorage.setItem(
            "role",
            data.role
        )

        alert("Login success")

    } else {

        alert(data.message)
    }
}