import threading
import socket

from utils.message import Message, MessageType

# Creates client thread
def create_client_thread(peer_list_queue, torrent_id, current_peer_id, thread_event):
    # Spawn a thread to communicate to the tracker
    client_thread = threading.Thread(
        target=client_task,
        args=(peer_list_queue, torrent_id, current_peer_id, thread_event),
    )
    client_thread.start()
    return client_thread


# Client task to control connection to 5 peers
def client_task(peer_list_queue, torrent_id, current_peer_id, thread_event):
    while 1:
        # Gets the list of peers available
        peer_list = peer_list_queue.get()

        # Loops through each peer and sets up a connection
        for peer in peer_list:
            # Skips over own peer id
            if peer[1] == current_peer_id:
                continue
            download_thread = threading.Thread(target=download_task, args=(peer[0], peer[1], torrent_id, thread_event))
            download_thread.start()

            
def download_task(peer_address, peer_id, torrent_id, thread_event):
    peer_ip, peer_port = peer_address.split(":")

    # Creates connection to peer
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((peer_ip, int(peer_port)))

    # Sends hello request
    hello_request = Message(type_= MessageType.HELLO_REQUEST, data=format_torrent_id(torrent_id=torrent_id)).to_bytes()
    client_socket.sendall(hello_request)

    # Waits until hello response is received
    hello_response = Message.from_socket(socket=client_socket)
    print(hello_response)

def format_torrent_id(torrent_id):
    return int(torrent_id, base=16).to_bytes(20, byteorder="big")
    


