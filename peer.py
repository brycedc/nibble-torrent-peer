import argparse
import sys



def main():
    # Create parser for Command Line
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument(
        "-p", "--port", type=int, default=8088, help="set the server port number"
    )
    parser.add_argument("-d", "--dest", help="the folder to download to and seed from.")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="display log messages"
    )
    parser.add_argument("netid", help="Your NETID")
    parser.add_argument("torrent_file", help="The torrent file for the file you want to download.")
    args = parser.parse_args()


if __name__ == "__main__":
    main()
