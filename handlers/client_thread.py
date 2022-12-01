import threading
import socket
import logging
import queue
import hashlib
import sys

# Utility scripts
from utils.message import Message, MessageType
from utils.chunk_manager import ChunkManager, ChunkStatus

# Creates client thread
def create_client_thread(peer_list_queue, chunk_manager, current_peer_id, thread_event):
    # Spawn a thread to communicate to the tracker
    client_thread = threading.Thread(
        target=client_task,
        args=(peer_list_queue, chunk_manager, current_peer_id, thread_event),
    )
    client_thread.setName("Client Thread")
    client_thread.start()
    return client_thread


# Client task to control connection to at least 5 peers
def client_task(
    peer_list_queue, chunk_manager: ChunkManager, current_peer_id, thread_event
):

    # Allows up to 5 peers to connect
    connected_peer_map = {}
    while 1:

        # Checks if all blocks are collected
        if chunk_manager.is_done() is True:
            logging.info(" CLIENT_THREAD: All chunks are downloaded")
            logging.info(" CLIENT_THREAD: Creating file...")
            chunk_hashes = list(chunk_manager.piece_status_dictionary.keys())
            with open(f"{chunk_manager.file_name}", "ab") as torrent_file:
                for index in range(chunk_manager.number_of_pieces):
                    with open(f"{chunk_manager.folder}/{chunk_manager.file_name}_{index}_{chunk_hashes[index]}", "rb") as chunk:
                        torrent_file.write(chunk.read())
            logging.info(" CLIENT_THREAD: Finished file")
            logging.info(" CLIENT_THREAD: Closing client thread...")
            sys.stderr.write(f"Succesfully downloaded {chunk_manager.file_name}...continuing to seed torrent\n")
            return

        try:
            # Gets the list of peers available
            peer_list = peer_list_queue.get(block=True, timeout=1)
        except queue.Empty:
            if thread_event.is_set():
                logging.info(" CLIENT_THREAD: Closing client socket...")
                logging.info(" CLIENT_THREAD: <<<Complete>>>")
                break
            else:
                # Loops back up to check the queue again
                continue

        # Loops through each peer and sets up a connection
        for peer in peer_list:
            # Skips over own peer id
            if peer[1] == current_peer_id:
                continue

            # Checks if peer is already connected
            download_thread = threading.Thread(
                target=download_task,
                args=(peer[0], peer[1], chunk_manager, thread_event),
            )
            download_thread.setName(f"{peer[1]}")
            download_thread.start()


def download_task(peer_address, peer_id, chunk_manager: ChunkManager, thread_event):
    peer_ip, peer_port = peer_address.split(":")

    # Creates connection to peer
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((peer_ip, int(peer_port)))

    # Sends hello request
    hello_request = Message(
        type_=MessageType.HELLO_REQUEST,
        data=bytes.fromhex(chunk_manager.torrent_id),
    ).to_bytes()
    client_socket.sendall(hello_request)

    # Waits until hello response is received
    hello_response = Message.from_socket(socket=client_socket)

    # Checks response if its valid
    if _check_hello_response(hello_response, client_socket, peer_id) == 1:
        return

    # Checks peers avaialbe chunks and requests for a valid chunk
    avalible_chunks = bin(int.from_bytes(hello_response.data, byteorder="big"))[2:]
    logging.info(f' DOWNLOAD_THREAD({peer_id}): Chunks avalible "{avalible_chunks}"')

    while 1:
        if (
            isFinshed := _download_chunks(
                chunk_manager, avalible_chunks, peer_id, client_socket
            )
        ) is True:
            break

    logging.info(f" DOWNLOAD_THREAD({peer_id}): Closing connection to peer")


# *PRIVATE HELPER FUNCTIONS*


def _check_hello_response(hello_response: Message, client_socket, peer_id):
    if hello_response is None:
        logging.info(
            f" DOWNLOAD_THREAD({peer_id}): Failed to parse response, closing connection..."
        )
        error_message = Message(
            MessageType.ERROR, data="Failed to parse response".encode()
        )
        client_socket.sendall(error_message.to_bytes())
        client_socket.close()
        return 1
    elif hello_response.version != 1:
        logging.info(f" DOWNLOAD_THREAD({peer_id}): Failed to verify version number")
        error_message = Message(
            MessageType.ERROR, data="Invalid version number".encode()
        )
        client_socket.sendall(error_message.to_bytes())
        client_socket.close()
        return 1
    elif hello_response.type != MessageType.HELLO_RESPONSE:
        logging.info(f" DOWNLOAD_THREAD({peer_id}): Message isn't a hello response")
        error_message = Message(
            MessageType.ERROR, data="Message type is not a hello response".encode()
        )
        client_socket.sendall(error_message.to_bytes())
        client_socket.close()
        return 1

    return 0


def _check_piece_response(
    piece_response: Message, client_socket, peer_id, requested_piece_hash
):
    if piece_response is None:
        logging.info(
            f" DOWNLOAD_THREAD({peer_id}): Failed to parse response, closing connection..."
        )
        error_message = Message(
            MessageType.ERROR, data="Failed to parse response".encode()
        )
        client_socket.sendall(error_message.to_bytes())
        client_socket.close()
        return False
    elif piece_response.version != 1:
        logging.info(f" DOWNLOAD_THREAD({peer_id}): Failed to verify version number")
        error_message = Message(
            MessageType.ERROR, data="Invalid version number".encode()
        )
        client_socket.sendall(error_message.to_bytes())
        client_socket.close()
        return False
    elif piece_response.type != MessageType.PIECE_RESPONSE:
        logging.info(f" DOWNLOAD_THREAD({peer_id}): Message isn't a hello response")
        error_message = Message(
            MessageType.ERROR, data="Message type is not a hello response".encode()
        )
        client_socket.sendall(error_message.to_bytes())
        client_socket.close()
        return False
    # Checks that the hash is correct
    elif _verify_hash(piece_response.data, requested_piece_hash) is False:
        logging.info(f" DOWNLOAD_THREAD({peer_id}): Hash is incorrect")
        error_message = Message(
            MessageType.ERROR, data="Hash value is incorrect".encode()
        )
        client_socket.sendall(error_message.to_bytes())
        client_socket.close()
        return False

    return True


def _verify_hash(data, expected_hash):
    actual_hash = hashlib.sha1(data).hexdigest()

    # Verifys that the hashes match
    if actual_hash == expected_hash:
        return True
    else:
        return False


def _download_chunks(chunk_manager: Message, avalible_chunks, peer_id, client_socket):
    # Loops through the status map and checks for a match
    index = 0
    requested_piece_hash = b""
    payload = b""
    is_finshed = True
    for key in chunk_manager.piece_status_dictionary:
        # Checks if piece is missing
        if chunk_manager.piece_status_dictionary[key] == ChunkStatus.MISSING:
            # Checks if the peers has the piece and that this is the first match
            if avalible_chunks[index : index + 1] == "1":
                logging.info(
                    f" DOWNLOAD_THREAD({peer_id}): Downloading chunk {index + 1}"
                )
                padding = -(-chunk_manager.number_of_pieces // 8)
                payload = int.to_bytes(index, byteorder="big", length=padding)
                chunk_manager.piece_status_dictionary[key] = ChunkStatus.DOWNLOADING
                requested_piece_hash = key
                is_finshed = False
                break
        else:
            index += 1

    # TODO Checks if index reached the end of loop and break

    # Creates piece request and sends it to peer
    piece_request = Message(type_=MessageType.PIECE_REQUEST, data=payload).to_bytes()
    logging.info(f" DOWNLOAD_THREAD({peer_id}): Sending piece request {piece_request}")
    client_socket.sendall(piece_request)

    # Collects piece from peer
    piece_response = Message.from_socket(client_socket)

    # Checks that the piece is valid
    if (
        _check_piece_response(
            piece_response, client_socket, peer_id, requested_piece_hash
        )
        is False
    ):
        is_finshed = True
        return is_finshed

    # Saves piece to chunk file and stores file id in dicitionary
    with open(
        f"{chunk_manager.folder}/{chunk_manager.file_name}_{index}_{requested_piece_hash}", "wb"
    ) as chunk_file:
        chunk_file.write(piece_response.data)
        chunk_manager.piece_status_dictionary[
            requested_piece_hash
        ] = ChunkStatus.AVAILABLE

    if is_finshed == True:
        logging.info(
            f" DOWNLOAD_THREAD({peer_id}): Finsihed downloading all avaliable chunks"
        )
    return is_finshed