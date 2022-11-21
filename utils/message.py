from enum import Enum


class MessageType(Enum):
    HELLO_REQUEST = 1
    HELLO_RESPONSE = 2
    PIECE_REQUEST = 3
    PIECE_RESPONSE = 4
    ERROR = 5


class Message:
    def __init__(self, type_, version=1, data=None):
        self.version = version
        self.type = type_
        self.data = data

    @classmethod
    def from_socket(cls, socket):
        header = socket.recv(4)

        if not header:
            return None

        version = header[0]
        type_ = header[1:2]
        length = int.from_bytes(header[2:], "big")
        total_data = b""

        while len(total_data) != length:
            data = socket.recv(length - len(total_data))

            if not data:
                return None

            total_data += data

        return cls(MessageType(type_), data=total_data)

    @classmethod
    async def from_reader(cls, reader):
        header = await reader.read(4)

        if not header:
            return None

        type_ = header[0]
        length = int.from_bytes(header[1:], "big")

        data = await reader.readexactly(length)
        return cls(MessageType(type_), data)

    def to_bytes(self):
        data = self.data or b""
        return self.version.to_bytes(1, "big") + self.type.value.to_bytes(1, "big") + len(data).to_bytes(2, "big") + data

    def __str__(self) -> str:
        return f"<Message(msg_type={self.type}, length={len(self.data)}, data={self.data})>"
