from app import create_app 
from app.security.seed import auto_encrypt_passwords 

app = create_app()

if __name__ == "__main__":
    try:
        auto_encrypt_passwords()
    except Exception as e:
        print(f"{str(e)}")

    app.run(debug=True)
