import threading
import logging
import socket

from utils.message import Message, MessageType

global seed_torrent_id

# Creates tracker thread
def create_server_thread(server_port, torrent_id):
    # Sets the torrent id
    seed_torrent_id = torrent_id
    # Spawn a thread to communicate to the tracker
    server_thread = threading.Thread(target=server_task, args=(server_port,))
    server_thread.start()


# Sever task controls creation of child task to upload file chunks to other peers
def server_task(server_port):

    # Creates a server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("", server_port))
    server_socket.listen()
    logging.info(f" SERVER_THREAD: Created server on port {server_port}")

    # Loops passing on new connection to upload_task
    while 1:
        try:
            conn, addr = server_socket.accept()
            logging.info(f" SERVER_THREAD: Accepted new upload peer @ {addr[0]}:{addr[1]}")
            upload_peer = threading.Thread(target=upload_task, args=(conn, addr))
            upload_peer.start()
        except KeyboardInterrupt:
            logging.info(f" SERVER_THREAD: Closing server socket...")
            server_socket.close()


# Sends the request chunk to the connected peer
def upload_task(conn, addr):

    # Handles hello request from peer
    hello_request = Message.from_socket(conn)

    # Checks that peers message request is valid
    if hello_request is None:
        logging.info(f" UPLOAD_THREAD({addr[0]}:{addr[1]}): Failed to parse request, closing connection...")
        error_message = Message(MessageType.ERROR, data="Failed".encode())
        conn.sendall(error_message.to_bytes())
        conn.close()
        return
    elif hello_request.version != 1:
        logging.info(
            f" UPLOAD_THREAD({addr[0]}:{addr[1]}): Failed to confirm version number {hello_request.version}, closing connection..."
        )
        error_message = Message(MessageType.ERROR, data="Version number wasn't valid".encode())
        conn.sendall(error_message.to_bytes())
        conn.close()
        return
    elif hello_request.type != MessageType.HELLO_REQUEST:
        logging.info(
            f" UPLOAD_THREAD({addr[0]}:{addr[1]}): Failed to confirm message as hello request, closing connection..."
        )
        error_message = Message(MessageType.ERROR, data="Expected a hello request type".encode())
        conn.sendall(error_message.to_bytes())
        conn.close()
        return
    elif hello_request.data != seed_torrent_id:
        logging.info(
            f" UPLOAD_THREAD({addr[0]}:{addr[1]}): Failed to request a valid torrent_id"
        )
        error_message = Message(MessageType.ERROR, data="Torrent ID was not valid".encode())
        conn.sendall(error_message.to_bytes())
        conn.close()
        return
