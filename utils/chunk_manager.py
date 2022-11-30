from enum import Enum
import os


class ChunkStatus(Enum):
    MISSING = 1
    DOWNLOADING = 2
    AVAILABLE = 3


class ChunkManager:
    def __init__(self, torrent_id, file_size, file_name, piece_size, pieces):
        self.torrent_id = torrent_id
        self.file_size = file_size
        self.file_name = file_name
        self.piece_size = piece_size
        self.number_of_pieces = len(pieces)

        # Creates a dictionary entry for each piece
        piece_status_dictionary = {}
        chunk_dicitionary = {}

        # Loops through each piece and adds it to a list
        index = 0
        for piece in pieces:
            piece_status_dictionary[piece] = ChunkStatus.MISSING

        # Loops through already existing chunks and updates the dictionary
        chunk_files = os.listdir(f"chunks/{file_name}")
        for cfile in chunk_files:
            chunk, value = cfile.split("_")
            piece_status_dictionary[value] = ChunkStatus.AVAILABLE

        self.piece_status_dictionary = piece_status_dictionary
        self.chunk_dicitionary = chunk_dicitionary

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
        if remain := result.__len__() != 0:
            for i in range(8 - remain):
                result.append(False)
            # Appends remaning results to bytearray
            _bytearray.append(sum(v << i for i, v in enumerate(result[::-1])))

        return _bytearray
