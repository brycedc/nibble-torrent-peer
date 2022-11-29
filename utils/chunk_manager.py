from enum import Enum


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

        # Creates a dictionary entry for each piece
        piece_status_dictionary = {}

        # Loops through each piece and adds it to a list
        for piece in pieces:
            piece_status_dictionary[piece] = ChunkStatus.MISSING

        self.piece_status_dictionary = piece_status_dictionary

    def check_current_chunks(self):

        # Creates a result array
        result = []
        # Loops through each piece and checks if it is downloaded and creates a binary number
        for key in self.piece_status_dictionary:
            # Checks if the piece is available
            if self.piece_status_dictionary[key] == ChunkStatus.AVAILABLE:
                result.append(True)
            else:
                result.append(False)
        # Formats the boolean list to a binary format
        return format(
            sum(v << i for i, v in enumerate(result[::-1])),
            f"#0{self.piece_status_dictionary.__len__()}b",
        )