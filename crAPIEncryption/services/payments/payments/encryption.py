import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

_KEY = b'MySecretKey12345'  # AES-128, matches EncryptionService.java


def encrypt(plain_text: str) -> str:
    cipher = AES.new(_KEY, AES.MODE_ECB)
    encrypted = cipher.encrypt(pad(plain_text.encode('utf-8'), AES.block_size))
    return base64.b64encode(encrypted).decode('utf-8')


def decrypt(encrypted_text: str) -> str:
    cipher = AES.new(_KEY, AES.MODE_ECB)
    decrypted = unpad(cipher.decrypt(base64.b64decode(encrypted_text)), AES.block_size)
    return decrypted.decode('utf-8')
