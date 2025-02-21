import secrets

# Генерация уникального логина
def generate_username():
    return f"us{secrets.token_hex(4)}"