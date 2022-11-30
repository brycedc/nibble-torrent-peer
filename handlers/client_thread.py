import threading
import socket
import logging
import queue
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


# Client task to control connection to 5 peers
def client_task(peer_list_queue, chunk_manager, current_peer_id, thread_event):

    # Allows up to 5 peers to connect
    connected_peer_map = {}
    while 1:

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


def download_task(peer_address, peer_id, chunk_manager, thread_event):
    peer_ip, peer_port = peer_address.split(":")

    # Creates connection to peer
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((peer_ip, int(peer_port)))

    # Sends hello request
    hello_request = Message(
        type_=MessageType.HELLO_REQUEST,
        data=format_torrent_id(torrent_id=chunk_manager.torrent_id),
    ).to_bytes()
    client_socket.sendall(hello_request)

    # Waits until hello response is received
    hello_response = Message.from_socket(socket=client_socket)

    # Checks response if its valid
    if hello_response is None:
        logging.info(
            f" DOWNLOAD_THREAD({peer_id}): Failed to parse response, closing connection..."
        )
        error_message = Message(
            MessageType.ERROR, data="Failed to parse response".encode()
        )
        client_socket.sendall(error_message.to_bytes())
        client_socket.close()
        return
    elif hello_response.version != 1:
        logging.info(f" DOWNLOAD_THREAD({peer_id}): Failed to verify version number")
        error_message = Message(
            MessageType.ERROR, data="Invalid version number".encode()
        )
        client_socket.sendall(error_message.to_bytes())
        client_socket.close()
        return
    elif hello_response.type != MessageType.HELLO_RESPONSE:
        logging.info(f" DOWNLOAD_THREAD({peer_id}): Message isn't a hello response")
        error_message = Message(
            MessageType.ERROR, data="Message type is not a hello response".encode()
        )
        client_socket.sendall(error_message.to_bytes())
        client_socket.close()
        return

    # Checks peers avaialbe chunks and requests for a valid chunk
    avalible_chunks = bin(int.from_bytes(hello_response.data, byteorder="big"))[2:]
    logging.info(f' DOWNLOAD_THREAD({peer_id}): Chunks avalible "{avalible_chunks}"')

    # Loops through the status map and checks for a match
    index = 0
    found_match = False
    result = []
    for key in chunk_manager.piece_status_dictionary:
        # Checks if piece is missing
        if chunk_manager.piece_status_dictionary[key] == ChunkStatus.MISSING:
            # Checks if the peers has the piece and that this is the first match
            if (avalible_chunks[index : index + 1] == "1") and (found_match == False):
                logging.info(
                    f" DOWNLOAD_THREAD({peer_id}): Downloading chunk {index + 1}"
                )
                result.append(True)
                found_match = True
                continue

        # Increments the index and shifts the
        index += 1
        result.append(False)
        

    payload = convert_boolean_array(result)
    print(payload)


# *HELPER FUNCTIONS*
def format_torrent_id(torrent_id):
    return int(torrent_id, base=16).to_bytes(20, byteorder="big")


def convert_boolean_array(boolean_array: list) -> bytearray:
    _bytearray = bytearray()
    temparray = []
    index = 0
    for value in boolean_array:
        # Checks if we have enough values to create a bytearray entry
        if temparray.__len__() == 8:
            _bytearray.append(sum(v << i for i, v in enumerate(temparray[::-1])))
            temparray.clear()
            temparray.append(value)
        # Adds value to temp array
        else:
            temparray.append(value)
        index += 1

    # Pads the array if not empty
    if (remain := temparray.__len__()) != 0:
        for i in range(8 - remain):
            temparray.append(False)
        # Appends remaning results to bytearray
        _bytearray.append(sum(v << i for i, v in enumerate(temparray[::-1])))

    return _bytearray
    
