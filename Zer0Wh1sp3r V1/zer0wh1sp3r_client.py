from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from pathlib import Path
import os
import json
import requests
import sys

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent
    
KEYS_DIR = BASE_DIR / "Keys"
MESSAGES_DIR = BASE_DIR / "Messages"
CONFIG_PATH = BASE_DIR / "client" / "config.json"

MESSAGES_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

DEFAULT_SERVER_URL = "http://127.0.0.1:5000"

users = {
    "user1": "User1",
    "user2": "User2"
}


# -----------------------------
# Config helpers
# -----------------------------

def create_default_config():
    config = {
        "server_url": DEFAULT_SERVER_URL
    }

    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)

    return config


def load_config():
    if not CONFIG_PATH.exists():
        print(f"Config file not found. Creating default config at: {CONFIG_PATH}")
        return create_default_config()

    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)

    except json.JSONDecodeError:
        print("ERROR: config.json is not valid JSON.")
        print("Recreating config.json with default settings.")
        return create_default_config()

    if "server_url" not in config:
        config["server_url"] = DEFAULT_SERVER_URL
        save_config(config)

    return config


def save_config(config):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)


def load_server_url():
    config = load_config()
    return config["server_url"]


def save_server_url(new_url):
    config = load_config()
    config["server_url"] = new_url
    save_config(config)


# -----------------------------
# General helpers
# -----------------------------

def normalize_user(prompt):
    user_input = input(prompt).strip().lower()

    if user_input in users:
        return users[user_input]

    print("Unknown user.")
    print("Valid users are:")

    for user_name in users.values():
        print(f"- {user_name}")

    return None


def is_valid_url(url):
    return url.startswith("http://") or url.startswith("https://")


def clean_url(url):
    return url.strip().rstrip("/")


def request_json(response):
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        return None


# -----------------------------
# Server checking
# -----------------------------

def check_server(server_url=None):
    if server_url is None:
        server_url = load_server_url()

    server_url = clean_url(server_url)

    print(f"\nChecking server: {server_url}")

    # Try /health first.
    # If the server does not have /health yet, fall back to /.
    urls_to_try = [
        f"{server_url}/health",
        f"{server_url}/"
    ]

    for url in urls_to_try:
        try:
            response = requests.get(url, timeout=5)

        except requests.exceptions.ConnectionError:
            print(f"Connection failed: {url}")
            continue

        except requests.exceptions.Timeout:
            print(f"Connection timed out: {url}")
            continue

        except requests.exceptions.RequestException as error:
            print(f"Request error for {url}: {error}")
            continue

        print(f"Checked: {url}")
        print(f"Status code: {response.status_code}")

        if response.status_code == 200:
            data = request_json(response)

            if data is not None:
                print("Server returned JSON:")
                print(data)

                # These checks are flexible because your current / route and future /health
                # route may not return exactly the same fields.
                status = str(data.get("status", "")).lower()
                service = str(data.get("service", "")).lower()
                message = str(data.get("message", "")).lower()

                if (
                    "zer0wh1sp3r" in service
                    or "zer0wh1sp3r" in message
                    or "server is running" in status
                    or "online" in status
                ):
                    print("Server check passed.")
                    return True

                # If it returns JSON with 200, it is still probably the Flask server.
                print("Server responded, but identity check was not specific.")
                return True

            print("Server responded, but did not return JSON.")
            print("Raw response:")
            print(response.text)
            return False

        print("Server returned a non-200 response.")
        print("Raw response:")
        print(response.text)

    print("Server check failed.")
    return False


# -----------------------------
# Message sending
# -----------------------------

def send_encrypted_message():
    server_url = clean_url(load_server_url())

    sender = normalize_user("Who are you? ")
    if sender is None:
        return

    receiver = normalize_user("Who are you sending this to? ")
    if receiver is None:
        return

    public_key_path = KEYS_DIR / f"{receiver}_public_key.pem"

    if not public_key_path.exists():
        print(f"ERROR: Public key not found: {public_key_path}")
        return

    with open(public_key_path, "rb") as f:
        public_key = serialization.load_pem_public_key(f.read())

    message = input("Enter your secret message: ").encode()

    aes_key = os.urandom(32)
    iv = os.urandom(16)

    cipher = Cipher(algorithms.AES(aes_key), modes.CFB(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(message) + encryptor.finalize()

    encrypted_key = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Optional local backup files.
    # These are useful for testing but should be ignored by Git.
    with open(MESSAGES_DIR / "sender.txt", "w") as f:
        f.write(sender)

    with open(MESSAGES_DIR / "receiver.txt", "w") as f:
        f.write(receiver)

    with open(MESSAGES_DIR / "encrypted_key.bin", "wb") as f:
        f.write(encrypted_key)

    with open(MESSAGES_DIR / "iv.bin", "wb") as f:
        f.write(iv)

    with open(MESSAGES_DIR / "ciphertext.bin", "wb") as f:
        f.write(ciphertext)

    try:
        response = requests.post(
            f"{server_url}/send",
            data={
                "sender": sender,
                "receiver": receiver
            },
            files={
                "encrypted_key": encrypted_key,
                "iv": iv,
                "ciphertext": ciphertext
            },
            timeout=10
        )

    except requests.exceptions.ConnectionError:
        print("\nERROR: Could not connect to server.")
        print("Check that Flask is running and that the server URL is correct.")
        return

    except requests.exceptions.Timeout:
        print("\nERROR: Request timed out.")
        print("The server may be offline, blocked, or unreachable.")
        return

    except requests.exceptions.RequestException as error:
        print("\nERROR: Request failed.")
        print(error)
        return

    print("\nMessage encrypted successfully.")
    print(f"From: {sender}")
    print(f"To: {receiver}")

    if response.status_code == 200:
        print("Server response:")
        data = request_json(response)

        if data is not None:
            print(data)
        else:
            print(response.text)

    else:
        print("Server returned an error.")
        print("Status code:", response.status_code)
        print("Raw response:", response.text)


# -----------------------------
# Inbox viewing
# -----------------------------

def view_inbox():
    server_url = clean_url(load_server_url())

    receiver = normalize_user("Who are you? ")
    if receiver is None:
        return

    try:
        response = requests.get(f"{server_url}/messages/{receiver}", timeout=10)

    except requests.exceptions.ConnectionError:
        print("\nERROR: Could not connect to server.")
        print("Check that Flask is running and that the server URL is correct.")
        return

    except requests.exceptions.Timeout:
        print("\nERROR: Request timed out.")
        return

    except requests.exceptions.RequestException as error:
        print("\nERROR: Request failed.")
        print(error)
        return

    if response.status_code != 200:
        print("\nERROR: Could not retrieve inbox.")
        print("Status code:", response.status_code)
        print("Raw response:", response.text)
        return

    inbox_data = request_json(response)

    if inbox_data is None:
        print("\nERROR: Server did not return valid JSON.")
        print("Raw response:", response.text)
        return

    messages = inbox_data.get("messages", [])

    if not messages:
        print(f"\nNo messages found for {receiver}.")
        return

    print(f"\nInbox for {receiver}")
    print("-" * 40)

    for message in messages:
        print(f"ID: {message['id']}")
        print(f"From: {message['sender']}")
        print(f"To: {message['receiver']}")
        print(f"Created at: {message.get('created_at')}")
        print("-" * 40)


# -----------------------------
# Message reading/decryption
# -----------------------------

def read_and_decrypt_message():
    server_url = clean_url(load_server_url())

    receiver = normalize_user("Who are you? ")
    if receiver is None:
        return

    private_key_path = KEYS_DIR / f"{receiver}_private_key.pem"

    if not private_key_path.exists():
        print(f"ERROR: Private key not found: {private_key_path}")
        return

    try:
        inbox_response = requests.get(f"{server_url}/messages/{receiver}", timeout=10)

    except requests.exceptions.ConnectionError:
        print("\nERROR: Could not connect to server.")
        print("Check that Flask is running and that the server URL is correct.")
        return

    except requests.exceptions.Timeout:
        print("\nERROR: Request timed out.")
        return

    except requests.exceptions.RequestException as error:
        print("\nERROR: Request failed.")
        print(error)
        return

    if inbox_response.status_code != 200:
        print("\nERROR: Could not retrieve inbox.")
        print("Status code:", inbox_response.status_code)
        print("Raw response:", inbox_response.text)
        return

    inbox_data = request_json(inbox_response)

    if inbox_data is None:
        print("\nERROR: Server did not return valid JSON for inbox.")
        print("Raw response:", inbox_response.text)
        return

    messages = inbox_data.get("messages", [])

    if not messages:
        print(f"\nNo messages found for {receiver}.")
        return

    print(f"\nInbox for {receiver}")
    print("-" * 40)

    for message in messages:
        print(f"ID: {message['id']}")
        print(f"From: {message['sender']}")
        print(f"Created at: {message.get('created_at')}")
        print("-" * 40)

    message_id_input = input("Enter the message ID you want to decrypt: ").strip()

    if not message_id_input.isdigit():
        print("ERROR: Message ID must be a number.")
        return

    message_id = int(message_id_input)

    valid_message_ids = []

    for message in messages:
        valid_message_ids.append(message["id"])

    if message_id not in valid_message_ids:
        print(f"ERROR: Message ID {message_id} is not in {receiver}'s inbox.")
        return

    try:
        message_response = requests.get(f"{server_url}/message/{message_id}", timeout=10)

    except requests.exceptions.ConnectionError:
        print("\nERROR: Could not connect to server.")
        print("Check that Flask is running and that the server URL is correct.")
        return

    except requests.exceptions.Timeout:
        print("\nERROR: Request timed out.")
        return

    except requests.exceptions.RequestException as error:
        print("\nERROR: Request failed.")
        print(error)
        return

    if message_response.status_code != 200:
        print("\nERROR: Could not retrieve selected message.")
        print("Status code:", message_response.status_code)
        print("Raw response:", message_response.text)
        return

    data = request_json(message_response)

    if data is None:
        print("\nERROR: Server did not return valid JSON for selected message.")
        print("Raw response:", message_response.text)
        return

    encrypted_key = bytes.fromhex(data["encrypted_key"])
    iv = bytes.fromhex(data["iv"])
    ciphertext = bytes.fromhex(data["ciphertext"])

    with open(private_key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    aes_key = private_key.decrypt(
        encrypted_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    cipher = Cipher(algorithms.AES(aes_key), modes.CFB(iv))
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()

    print("\nDecrypted message:")
    print(f"Message ID: {data['id']}")
    print(f"From: {data['sender']}")
    print(f"To: {data['receiver']}")
    print(f"Created at: {data.get('created_at')}")
    print(f"Message: {plaintext.decode()}")


# -----------------------------
# Server options menu
# -----------------------------

def show_server_url():
    server_url = load_server_url()
    print(f"\nCurrent server URL: {server_url}")


def set_localhost_server():
    local_url = "http://127.0.0.1:5000"
    save_server_url(local_url)
    print(f"\nServer URL set to Localhost: {local_url}")


def set_ngrok_server():
    print("\nPaste your ngrok forwarding URL.")
    print("Examples:")
    print("  https://abc123.ngrok-free.app")
    print("  http://abc123.ngrok-free.dev:80")

    ngrok_url = input("Ngrok URL: ").strip()
    ngrok_url = clean_url(ngrok_url)

    if not ngrok_url:
        print("No URL entered. Server URL was not changed.")
        return

    if not is_valid_url(ngrok_url):
        print("ERROR: URL must start with http:// or https://")
        return

    if "ngrok" not in ngrok_url.lower():
        print("WARNING: This URL does not look like an ngrok URL.")
        confirm = input("Use it anyway? y/n: ").strip().lower()

        if confirm != "y":
            print("Server URL was not changed.")
            return

    save_server_url(ngrok_url)
    print(f"Server URL set to ngrok: {ngrok_url}")

    test_now = input("Check this server now? y/n: ").strip().lower()
    if test_now == "y":
        check_server(ngrok_url)


def set_custom_server():
    custom_url = input("Enter custom server URL: ").strip()
    custom_url = clean_url(custom_url)

    if not custom_url:
        print("No URL entered. Server URL was not changed.")
        return

    if not is_valid_url(custom_url):
        print("ERROR: URL must start with http:// or https://")
        return

    save_server_url(custom_url)
    print(f"Server URL updated: {custom_url}")

    test_now = input("Check this server now? y/n: ").strip().lower()
    if test_now == "y":
        check_server(custom_url)


def server_options_menu():
    while True:
        print("\n=== Server Options ===")
        print("1. Use Localhost")
        print("2. Use ngrok")
        print("3. Use Custom URL")
        print("4. Show Current Server URL")
        print("5. Check Current Server")
        print("6. Back")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            set_localhost_server()
        elif choice == "2":
            set_ngrok_server()
        elif choice == "3":
            set_custom_server()
        elif choice == "4":
            show_server_url()
        elif choice == "5":
            check_server()
        elif choice == "6":
            break
        else:
            print("Invalid option. Choose 1-6.")


# -----------------------------
# Key folder
# -----------------------------

def show_key_folder():
    print(f"\nKey folder: {KEYS_DIR}")

    if not KEYS_DIR.exists():
        print("Key folder does not exist.")
        return

    print("\nKey files:")
    for file_path in KEYS_DIR.iterdir():
        print(f"- {file_path.name}")


# -----------------------------
# Main menu
# -----------------------------

def main_menu():
    while True:
        print("\n=== Zer0Wh1sp3r ===")
        print("1. Send encrypted message")
        print("2. View inbox")
        print("3. Read/decrypt message")
        print("4. Server options")
        print("5. Show key folder")
        print("6. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            send_encrypted_message()
        elif choice == "2":
            view_inbox()
        elif choice == "3":
            read_and_decrypt_message()
        elif choice == "4":
            server_options_menu()
        elif choice == "5":
            show_key_folder()
        elif choice == "6":
            print("Exiting Zer0Wh1sp3r.")
            break
        else:
            print("Invalid option. Choose 1-6.")


if __name__ == "__main__":
    main_menu()
