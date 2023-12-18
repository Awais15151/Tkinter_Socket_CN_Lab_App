import socket
from socket import error as SocketError
import threading

connected_users = {}
client_sockets = {}
connected_users_lock = threading.Lock()
BUFFER_SIZE = 1024

def handle_client(client_socket):
    try:
        username = client_socket.recv(1024).decode()

        with connected_users_lock:
            if username in connected_users:
                client_socket.send("UsernameNotAccepted".encode())
            else:
                connected_users[username] = client_socket
                client_sockets[username] = client_socket
                client_socket.send("UsernameAccepted".encode())


        while True:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break

            if data.startswith("StartConversation:"):
                start_conversation(username, data[len("StartConversation:"):])
            elif data == "GetConnectedUsers":
                print(f"{username} is requesting the connected users data")
                connected_users_str = ",".join(connected_users.keys())
                response = f"Connected Users:{connected_users_str}"
                client_socket.send(response.encode())
            elif data.startswith("FileShare:"):
                filename = data.split(":")[1]
                receive_file(client_socket, filename)
                print(f"{filename} received successfully")
            elif data.startswith("VoiceCall:"):
                initiate_voice_call(username, data[len("VoiceCall:"):])
            else:
                broadcast_message(username, data)

    except ConnectionResetError:
        print(f"Connection with {username} reset.")
    except (SocketError, ConnectionResetError) as e:
        print(f"Error in handling client {username}: {e}")
    finally:
        print(f"{username} disconnected.")
        del connected_users[username]
        if username in client_sockets:
            del client_sockets[username]

def initiate_voice_call(sender_username, recipient_username):
    recipient_socket = connected_users.get(recipient_username)

    if recipient_socket:
        recipient_socket.send(f"VoiceCallRequest:{sender_username}".encode())

def receive_file(client_socket, filename):
    try:
        with open(filename, 'wb') as file:
            while True:
                data = client_socket.recv(BUFFER_SIZE)
                if not data:
                    break
                file.write(data)
            print(f"Received file: {filename}")
    except Exception as e:
        print(f"Error receiving file: {e}")

def start_conversation(sender_username, recipient_username):
    sender_socket = connected_users.get(sender_username)
    recipient_socket = connected_users.get(recipient_username)

    if sender_socket and recipient_socket:
        with connected_users_lock:
            sender_socket.send(f"{recipient_username}".encode())
            recipient_socket.send(f"{sender_username}".encode())

        recipient_socket.send(f"StartedConversation:{sender_username}".encode())

    else:
        print(f"Either sender {sender_username} or recipient {recipient_username} not found.")
        with connected_users_lock:
            del connected_users[recipient_username]
            del connected_users[sender_username]


def broadcast_message(sender_username, message):
    for user, user_socket in connected_users.items():
        if user != sender_username:
            user_socket.send(f"{sender_username}: {message}\n".encode('utf-8'))

def server_program():
    host = "192.168.86.191"
    port = 6500

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(100)
    print("Server listening on " + host + ":" + str(port))

    while True:
        client_socket, address = server_socket.accept()
        print("Connection from: " + str(address))
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

if __name__ == '__main__':
    server_program()
