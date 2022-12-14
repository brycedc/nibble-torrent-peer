# Nibbletorrent

## Setup

To start downloading a file, a connection with a tracker is needed.  Once a connection has been established the tracker will send back a list of current peers in the network.  The torrent will then begin requesting chunks of the provided torrent and upload chunks at the same time.  Once all the chunks are downloaded the peer will create the file and continue to seed the network.

## Command Line Interface

To use the program, simply call `python3 peer.py --help` for a list of options the program can handle.  
