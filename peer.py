import argparse
import sys
import os
import json
import logging
import queue
import socket
import time
import threading

from handlers.tracker_thread import create_tracker_thread
from handlers.server_thread import create_server_thread


def main():
    # Create parser for Command Line
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument(
        "--host",
        default=socket.gethostbyname(socket.gethostname()),
        help="host name of peer, defaults to private ip",
    )
    parser.add_argument(
        "-p", "--port", type=int, default=8088, help="set the server port number"
    )
    parser.add_argument("-d", "--dest", help="the folder to download to and seed from.")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="display log messages"
    )
    parser.add_argument("netid", help="Your NETID")
    parser.add_argument(
        "torrent_file", help="The torrent file for the file you want to download."
    )
    args = parser.parse_args()

    # Sets log level if verbose
    if args.verbose:
        logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
    else:
        logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.CRITICAL)

    # Checks that the port number is valid
    if (args.port < 1024) or (args.port > 65535):
        sys.stderr.write(
            f"Port number: {args.port} is not a valid port number (1024 - 65535)\n"
        )
        sys.exit(1)

    # Checks if torrent file exist
    if not os.path.exists(f"torrents/{args.torrent_file}"):
        sys.stderr.write(
            f'"{args.torrent_file}" does not exist try a valid torrent file\n'
        )
        sys.exit(1)

    # Formats netid
    peer_id = f"-ECEN426-{args.netid}"

    logging.info(" Config:")
    logging.info(f"\tHost: {args.host}")
    logging.info(f"\tPort: {args.port}")
    logging.info(f"\tFolder: {args.dest}")
    logging.info(f"\tNetID: {args.netid}")
    logging.info(f"\tTorrent File: {args.torrent_file}\n")

    # Opens the json file and loads it into a dictionary
    with open(f"torrents/{args.torrent_file}", "r") as torrent:
        json_data = json.load(torrent)

    # Creates thread killer event
    thread_killer = threading.Event() 

    # Creates tracker thread and response queue
    tracker_queue = queue.Queue(maxsize=1)
    create_tracker_thread(
        peer_id=peer_id,
        ip_address=args.host,
        port_number=args.port,
        torrent_id=json_data["torrent_id"],
        tracker_url=json_data["tracker_url"],
        queue=tracker_queue,
    )

    # Creates server thread to upload chunks to clients
    thread_server = create_server_thread(args.port, json_data["torrent_id"], thread_killer)

    # Creates client thread to download chunks to file

    # Keeps main task alive until a keyboard interrupts is detected
    try:
        while 1:
            time.sleep(1)
    except KeyboardInterrupt:
        # Gracefully closes the peer
        sys.stderr.write("\nClosing peer...\n")
        thread_killer.set()

        # Waits for threads to end gracefully
        thread_server.join()
        logging.info(" MAIN THREAD: server has been closed...")

    
        


if __name__ == "__main__":
    main()
