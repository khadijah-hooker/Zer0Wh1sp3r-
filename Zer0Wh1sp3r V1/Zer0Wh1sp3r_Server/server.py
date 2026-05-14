from flask import Flask, request, jsonify
from datetime import datetime
from server_database import (
    init_db,
    save_message,
    get_messages_for_receiver,
    get_message_by_id,
    get_latest_message_for_receiver,
    get_total_message_count
)

app = Flask(__name__)

# Create database/table when the server starts
init_db()


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "Zer0Wh1sp3r server is running",
        "message": "Server stores encrypted messages only.",
        "storage": "SQLite",
        "total_messages": get_total_message_count()
    })


@app.route("/send", methods=["POST"])
def send_message():
    form = request.form
    files = request.files

    required_form_fields = ["sender", "receiver"]
    required_file_fields = ["encrypted_key", "iv", "ciphertext"]

    for field in required_form_fields:
        if field not in form:
            return jsonify({
                "error": f"Missing form field: {field}"
            }), 400

    for field in required_file_fields:
        if field not in files:
            return jsonify({
                "error": f"Missing file field: {field}"
            }), 400

    sender = form["sender"]
    receiver = form["receiver"]
    encrypted_key = files["encrypted_key"].read()
    iv = files["iv"].read()
    ciphertext = files["ciphertext"].read()
    created_at = datetime.now().isoformat(timespec="seconds")

    message_id = save_message(
        sender=sender,
        receiver=receiver,
        encrypted_key=encrypted_key,
        iv=iv,
        ciphertext=ciphertext,
        created_at=created_at
    )

    return jsonify({
        "status": "Message received and stored",
        "id": message_id,
        "sender": sender,
        "receiver": receiver,
        "created_at": created_at,
        "total_messages": get_total_message_count()
    })


@app.route("/messages/<receiver>", methods=["GET"])
def list_messages(receiver):
    receiver_messages = get_messages_for_receiver(receiver)

    return jsonify({
        "receiver": receiver,
        "message_count": len(receiver_messages),
        "messages": receiver_messages
    })


@app.route("/message/<int:message_id>", methods=["GET"])
def get_message(message_id):
    message = get_message_by_id(message_id)

    if message is None:
        return jsonify({
            "error": f"Message ID {message_id} not found"
        }), 404

    return jsonify({
        "id": message["id"],
        "sender": message["sender"],
        "receiver": message["receiver"],
        "encrypted_key": message["encrypted_key"].hex(),
        "iv": message["iv"].hex(),
        "ciphertext": message["ciphertext"].hex(),
        "created_at": message["created_at"]
    })


@app.route("/receive/<receiver>", methods=["GET"])
def receive_latest_message(receiver):
    message = get_latest_message_for_receiver(receiver)

    if message is None:
        return jsonify({
            "error": f"No messages available for {receiver}"
        }), 404

    return jsonify({
        "id": message["id"],
        "sender": message["sender"],
        "receiver": message["receiver"],
        "encrypted_key": message["encrypted_key"].hex(),
        "iv": message["iv"].hex(),
        "ciphertext": message["ciphertext"].hex(),
        "created_at": message["created_at"]
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "online",
        "service": "Zer0Wh1sp3r",
        "storage": "SQLite",
        "total_messages": get_total_message_count()
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)