import threading
import logging
import socket

from utils.message import Message, MessageType
from utils.chunk_manager import ChunkStatus, ChunkManager

# Creates tracker thread
def create_server_thread(server_port, chunk_manager, thread_event):
    # Spawn a thread to communicate to the tracker
    server_thread = threading.Thread(
        target=server_task, args=(server_port, chunk_manager, thread_event)
    )
    server_thread.setName("Server Thread")
    server_thread.start()
    return server_thread


# Sever task controls creation of child task to upload file chunks to other peers
def server_task(server_port, chunk_manager, thread_event):

    # Creates a server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("", server_port))
    server_socket.listen()
    server_socket.settimeout(1)
    logging.info(f" SERVER_THREAD: Created server on port {server_port}")

    # Loops passing on new connection to upload_task
    while 1:
        try:
            conn, addr = server_socket.accept()
            logging.info(
                f" SERVER_THREAD: Accepted new upload peer @ {addr[0]}:{addr[1]}"
            )
            upload_peer = threading.Thread(
                target=upload_task, args=(conn, addr, chunk_manager, thread_event), daemon=True
            )
            upload_peer.setName(f"Upload Peer:{addr[0]}")
            upload_peer.start()
        except socket.timeout:
            if thread_event.is_set():
                logging.info(f" SERVER_THREAD: Closing server socket...")
                server_socket.close()
                break

    logging.info(f" SERVER_THREAD: <<<Complete>>>")


# Sends the request chunk to the connected peer
def upload_task(conn, addr, chunk_manager: ChunkManager, thread_event):

    # Handles hello request from peer
    hello_request = Message.from_socket(conn)

    # Checks that peers message request is valid
    _check_hello_request(hello_request, addr, conn, chunk_manager.torrent_id)

    # Request is valid send a hello response with available chunks
    logging.info(f" UPLOAD_THREAD({addr[0]}:{addr[1]}): Received successful hello request from peer")
    logging.info(f" UPLOAD_THREAD({addr[0]}:{addr[1]}): Sending hello response to peer")
    payload = chunk_manager.check_current_chunks()
    hello_response = Message(type_=MessageType.HELLO_RESPONSE, data=payload).to_bytes()
    conn.sendall(hello_response)

    # Loops forever until peer disconnects or timeout
    while 1:

        # Waits for a piece request
        piece_request = Message.from_socket(conn)

        # Checks that piece_request is valid
        _check_piece_request(piece_request, addr, conn)

        # Handles piece_request and returns a piece response to send
        piece_response = _handle_piece_request(piece_request, chunk_manager, conn, addr)

        # Checks if the piece response is good
        if piece_response is None:
            return

        # Sends piece response to peer
        conn.sendall(piece_response)
    




def _check_hello_request(hello_request, addr, conn, torrent_id):
    if hello_request is None:
        logging.info(
            f" UPLOAD_THREAD({addr[0]}:{addr[1]}): Failed to parse request, closing connection..."
        )
        error_message = Message(
            MessageType.ERROR, data="Failed to parse request".encode()
        )
        conn.sendall(error_message.to_bytes())
        conn.close()
        return
    elif hello_request.version != 1:
        logging.info(
            f" UPLOAD_THREAD({addr[0]}:{addr[1]}): Failed to confirm version number {hello_request.version}, closing connection..."
        )
        error_message = Message(
            MessageType.ERROR, data="Version number wasn't valid".encode()
        )
        conn.sendall(error_message.to_bytes())
        conn.close()
        return
    elif hello_request.type != MessageType.HELLO_REQUEST:
        logging.info(
            f" UPLOAD_THREAD({addr[0]}:{addr[1]}): Failed to confirm message as hello request, closing connection..."
        )
        error_message = Message(
            MessageType.ERROR, data="Expected a hello request type".encode()
        )
        conn.sendall(error_message.to_bytes())
        conn.close()
        return
    elif hello_request.data != bytes.fromhex(torrent_id):
        logging.info(
            f" UPLOAD_THREAD({addr[0]}:{addr[1]}): Failed to validate torrent_id \nExpected:{bytes.fromhex(torrent_id)} \nActual:{hello_request.data.decode()}"
        )
        error_message = Message(
            MessageType.ERROR, data="Torrent ID was not valid".encode()
        )
        conn.sendall(error_message.to_bytes())
        conn.close()
        return

def _check_piece_request(piece_request, addr, conn):
    if piece_request is None:
        logging.info(
            f" UPLOAD_THREAD({addr[0]}:{addr[1]}): Failed to parse request, closing connection..."
        )
        error_message = Message(
            MessageType.ERROR, data="Failed to parse request".encode()
        )
        conn.sendall(error_message.to_bytes())
        conn.close()
        return
    elif piece_request.version != 1:
        logging.info(
            f" UPLOAD_THREAD({addr[0]}:{addr[1]}): Failed to confirm version number {piece_request.version}, closing connection..."
        )
        error_message = Message(
            MessageType.ERROR, data="Version number wasn't valid".encode()
        )
        conn.sendall(error_message.to_bytes())
        conn.close()
        return
    elif piece_request.type != MessageType.PIECE_REQUEST:
        logging.info(
            f" UPLOAD_THREAD({addr[0]}:{addr[1]}): Failed to confirm message as piece request, closing connection..."
        )
        error_message = Message(
            MessageType.ERROR, data="Expected a piece request type".encode()
        )
        conn.sendall(error_message.to_bytes())
        conn.close()
        return

def _handle_piece_request(piece_request: Message, chunk_manager: ChunkManager, conn, addr):
    request = int.from_bytes(piece_request.data, 'big')
    
    chunk_hashes = list(chunk_manager.piece_status_dictionary.keys())

    # Checks that the request is valid
    try:
        requested_hash = chunk_hashes[request]
    except:
        logging.info(
            f" UPLOAD_THREAD({addr[0]}:{addr[1]}): Requested chunk is out of bounds..."
        )
        error_message = Message(
            MessageType.ERROR, data="Requested chunk is invalid".encode()
        )
        conn.sendall(error_message.to_bytes())
        conn.close()
        return None
    
    #Creates a request 
    payload = b''
    with open(f"{chunk_manager.folder}/chunks/{chunk_manager.file_name}_{request}_{requested_hash}", "rb") as chunk_file:
        payload = chunk_file.read()
    piece_response = Message(type_= MessageType.PIECE_RESPONSE, data=payload).to_bytes()
    logging.info(f" UPLOAD_THREAD({addr[0]}:{addr[1]}): Sending {chunk_manager.file_name}_{request}...")
    return piece_response
