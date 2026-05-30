async function login() {

    const username =
        document.getElementById("username").value;

    const password =
        document.getElementById("password").value;
    if(username === "" || password === ""){
        document.getElementById("msg").innerText =
            "Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu";
        return;
    }
    const response = await fetch(
        "http://127.0.0.1:5000/auth/login",
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
    );

    const data = await response.json();

    console.log(data);

    if(response.ok){

        localStorage.setItem("token", data.token);
        localStorage.setItem("role", data.role);

        if(data.role === "ADMIN"){
             window.location.href = "/report";
        }else{
            window.location.href = "/payment";
        }
    }
    else{
        alert(data.message);
    }
}