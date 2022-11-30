import hashlib

def check_hash(data, expected_hash):
    actual_hash = hashlib.sha1(data)
    print(actual_hash)