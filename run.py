from app import create_app 
from app.security.seed import auto_encrypt_passwords 

# auto_encrypt_passwords()
app = create_app()

if __name__ == "__main__":
    
    app.run(
    host="0.0.0.0",
    port=5000,
    debug=True
)
print(app.url_map)