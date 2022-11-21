import threading
import time
import requests
import logging

# Creates tracker thread
def create_client_thread(tracker_queue):
    # Spawn a thread to communicate to the tracker
    client_thread = threading.Thread(
        target=client_task,
        args=(tracker_queue,),
        daemon=True,
    )
    client_thread.start()

# Sends a request to the torrent tracker every 30 seconds
def client_task(peer_id, port_number, torrent_id, tracker_url, queue):
    while 1:
        # Makes a http request to the tracker
        payload = {
            "peer_id": peer_id,
            "ip": "192.168.86.63",
            "port": port_number,
            "torrent_id": torrent_id,
        }
        new_response = requests.get(tracker_url, params=payload).json()
        peer_list = new_response['peers']

        # Logs the response object
        logging.info(f" TRACKER_THREAD Tracker Response")
        logging.info(f" TRACKER_THREAD \tInterval: {new_response['interval']}")
        logging.info(f" TRACKER_THREAD \tPeer List:")
        for peer in peer_list:
            logging.info(f" TRACKER_THREAD \t {peer}")

        # Adds new response to the tracker queue and clears the old results if any
        queue.queue.clear()
        queue.put(peer_list)
        
        # Sleeps for the interval time
        time.sleep(new_response["interval"])