from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from pathlib import Path


KEYS_DIR = Path("Zer0Wh1sp3r Keys")
KEYS_DIR.mkdir(exist_ok=True)


def generate_key_pair(username):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    public_key = private_key.public_key()

    private_key_path = KEYS_DIR / f"{username}_private_key.pem"
    public_key_path = KEYS_DIR / f"{username}_public_key.pem"

    with open(private_key_path, "wb") as private_file:
        private_file.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            )
        )

    with open(public_key_path, "wb") as public_file:
        public_file.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )

    print(f"Created keys for {username}")
    print(f"Private key: {private_key_path}")
    print(f"Public key:  {public_key_path}")


generate_key_pair("gdev")
generate_key_pair("nofux")