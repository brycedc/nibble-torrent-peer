from enum import Enum
import os
import logging


class ChunkStatus(Enum):
    MISSING = 1
    DOWNLOADING = 2
    AVAILABLE = 3


class ChunkManager:
    def __init__(self, torrent_id, file_size, file_name, piece_size, pieces, folder):
        self.torrent_id = torrent_id
        self.file_size = file_size
        self.file_name = file_name
        self.piece_size = piece_size
        self.number_of_pieces = len(pieces)
        self.folder = folder

        # Creates directory if it doesn't exist
        try:
            os.mkdir(folder)
        except OSError as error:
            logging.debug("Directory already exist will ignore error :)")

        # Creates a dictionary entry for each piece
        piece_status_dictionary = {}

        # Loops through each piece and adds it to a list
        index = 0
        for piece in pieces:
            piece_status_dictionary[piece] = ChunkStatus.MISSING

        # Loops through already existing chunks and updates the dictionary
        chunk_files = os.listdir(folder)
        for cfile in chunk_files:
            name, value, _hash = cfile.split("_")
            piece_status_dictionary[_hash] = ChunkStatus.AVAILABLE

        self.piece_status_dictionary = piece_status_dictionary
    

    def is_done(self):
        is_done = True
        for key in self.piece_status_dictionary:
            if(self.piece_status_dictionary[key] != ChunkStatus.AVAILABLE):
                is_done = False
                break
        return is_done
            

    def check_current_chunks(self):

        # Creates a result array
        result = []
        _bytearray = bytearray()
        # Loops through each piece and checks if it is downloaded and creates a binary number
        for key in self.piece_status_dictionary:
            # Checks if the piece is available
            if self.piece_status_dictionary[key] == ChunkStatus.AVAILABLE:
                result.append(True)
            else:
                result.append(False)
            
            # Converts the boolean array into a bytearray
            if result.__len__() == 8:
                _bytearray.append(sum(v << i for i, v in enumerate(result[::-1])))
                result.clear()

        # Pads the array if not empty
        if (remain := result.__len__()) != 0:
            for i in range(8 - remain):
                result.append(False)
            # Appends remaning results to bytearray
            _bytearray.append(sum(v << i for i, v in enumerate(result[::-1])))

        return bytes(_bytearray)
