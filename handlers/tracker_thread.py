import threading
import time
import requests
import logging

# Creates tracker thread
def create_tracker_thread(
    peer_id, ip_address, port_number, torrent_id, tracker_url, queue, thread_event
):

    # Spawn a thread to communicate to the tracker
    tracker_thread = threading.Thread(
        target=tracker_task,
        args=(
            peer_id,
            ip_address,
            port_number,
            torrent_id,
            tracker_url,
            queue,
            thread_event,
        ),
    )
    tracker_thread.start()
    return tracker_thread


# Sends a request to the torrent tracker every 30 seconds
def tracker_task(
    peer_id, ip_address, port_number, torrent_id, tracker_url, queue, thread_event
):
    while 1:
        # Makes a http request to the tracker
        payload = {
            "peer_id": peer_id,
            "ip": ip_address,
            "port": port_number,
            "torrent_id": torrent_id,
        }
        new_response = requests.get(tracker_url, params=payload).json()
        peer_list = new_response["peers"]

        # Logs the response object
        logging.info(f" TRACKER_THREAD: Tracker Response")
        logging.info(f" TRACKER_THREAD: \tInterval: {new_response['interval']}")
        logging.info(f" TRACKER_THREAD: \tPeer List:")
        for peer in peer_list:
            logging.info(f" TRACKER_THREAD: \t {peer}")

        # Adds new response to the tracker queue and clears the old results if any
        queue.queue.clear()
        queue.put(peer_list)

        # Sleeps for the interval time
        for i in range(new_response["interval"]):
            time.sleep(1)
            # Checks if the main thread is closing
            if thread_event.is_set():
                logging.info("TRACKER_THREAD: Closing tracker socket...")
                logging.info("TRACKER_THREAD: <<<Complete>>>")
                return

    
