Zer0Wh1sp3r



Zer0Wh1sp3r is a Python/Flask encrypted messaging prototype using RSA/AES hybrid encryption. The client

encrypts and decrypts messages locally, while the Flask server stores only encrypted message data in SQLite.



Version 1 Status: Working CLI/EXE prototype

Features

• RSA/AES hybrid encryption

• Client-side encryption and decryption

• Flask message server

• SQLite encrypted message storage

• Inbox by receiver

• Message selection by ID

• Configurable server URL with config.json

• Combined CLI client menu

• Portable folder paths

• ngrok remote testing confirmed

• Windows EXE build with custom icon





Install Requirements

pip install -r requirements.txt



Run the Server

cd Zer0Wh1sp3r\_Server

python server.py

Default local server:

http://127.0.0.1:5000



Run the Python Client

python zer0wh1sp3r\_client.py



Client menu:

=== Zer0Wh1sp3r ===

1\. Send encrypted message

2\. View inbox

3\. Read/decrypt message

4\. Server options

5\. Show key folder

6\. Exit



Run the EXE Client

Clean EXE test folder:

Zer0Wh1sp3r\_EXE\_Test/

|-- Zer0Wh1sp3r.exe

|-- client/

|   `-- config.json

`-- Keys/

&#x20;   |-- User1\_public\_key.pem

&#x20;   |-- User2\_public\_key.pem

&#x20;   `-- User2\_private\_key.pem

Messages/ is created automatically when needed.





Config File 



The client reads the server address from:

client/config.json

Local example:

{

}

&#x20;   "server\_url": "http://127.0.0.1:5000"

ngrok example:

{

}

&#x20;   "server\_url": "http://your-ngrok-domain.ngrok-free.dev:80"

The server URL can also be changed from the client menu:

Server options -> Use ngrok

Server options -> Use Custom URL

Server options -> Check Current Server



How It Works

Sender client

&#x20; encrypts message locally with AES

&#x20; encrypts AES key with receiver public RSA key

&#x20;       v

Flask server

&#x20; stores encrypted\_key, iv, ciphertext

&#x20;       v

Receiver client

&#x20; downloads encrypted message

&#x20; decrypts AES key with private RSA key

&#x20; decrypts message locally

The server never stores plaintext messages, raw AES keys, or private keys.





ngrok Remote Testing



Start the server:

cd Zer0Wh1sp3r\_Server

python server.py

Start ngrok:

Page 3

ngrok http 5000

Use the ngrok URL in the client:

Server options -> Use ngrok

Remote testing was confirmed with another client able to connect, view inbox messages, and decrypt selected

messages.





Key File Rules

Key filenames must match exactly.

Expected examples:

User1\_private\_key.pem

User1\_public\_key.pem

User2\_private\_key.pem

User2\_public\_key.pem

If the inbox works but decrypting fails, the private key is likely missing, named incorrectly, or in the wrong folder.

Troubleshooting

Inbox works but decrypt does not

Can view inbox = server/ngrok/config is working.

Cannot decrypt = local private key issue.

ngrok 502 error

If ngrok mentions localhost:80, it is forwarding to the wrong port.

Use:

ngrok http 5000

not:

ngrok http 80

Database file not appearing

Make sure server.py is using server\_database.py, not the old in-memory messages = \[] version.

Database location: Zer0Wh1sp3r\_Server/server/zer0wh1sp3r.db





Package Client as EXE



pip install pyinstaller

pyinstaller --onefile --name Zer0Wh1sp3r --icon Zer0Wh1sp3r.ico zer0wh1sp3r\_client.py

EXE output:

dist/Zer0Wh1sp3r.exe



Security Notes

This is an educational prototype and is not production-ready.

Current limitations:

• Private keys are regular PEM files.

• No passphrase-protected private keys yet.

• No key revocation yet.

• No real user accounts yet.

• Test keys should not be treated as production keys.



GitHub Safety



Do not upload:

Keys/

Messages/

\*.db

.env

venv/

.venv/

\_\_pycache\_\_/

dist/

build/

\*.spec



Version 1 Milestones



* RSA key generation
* Local encryption/decryption
* Flask server
* SQLite persistent storage
* Multiple-message inbox
* Combined CLI client
* Configurable server URL
* Portable folder paths
* ngrok remote test
* EXE packaging test 
* Custom EXE icon



Future Improvements

• Add /health route

• Add read/unread status

• Add delete/archive messages

• Add passphrase-encrypted private keys

• Add user accounts

• Add public key management

• Add key revocation/lost-key handling

• Add portable USB client mode

• Deploy to Raspberry Pi, Ubuntu Server, or AWS Lightsail









