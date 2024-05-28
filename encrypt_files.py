from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os

enc_key = "RW9TntGwoutrYwZT2qrs9DrNtaaLw36paqqMV9PpD92IPlw1OSMXUBqDMQjx"

def encrypt_file(enc_key, input_file_path):
    # Derive a key from the password using PBKDF2
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        iterations=100000,
        salt=salt,
        length=32,
        backend=default_backend()
    )
    key = kdf.derive(enc_key.encode())

    # Generate a random IV (Initialization Vector)
    iv = os.urandom(16)

    # Create a Cipher object with AES in CBC mode
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())

    with open(input_file_path, 'rb') as infile:
        plaintext = infile.read()

    # Encrypt the plaintext
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()


    #encrypted file path extension
    base_path, old_extension = os.path.splitext(input_file_path)

    # Construct the new file path with the desired extension
    new_file_path = base_path + ".bin"

    # Write the encrypted data along with the salt and IV to the output file
    with open(new_file_path, 'wb') as outfile:
        outfile.write(salt + iv + ciphertext)
    
    #removing the old file
    os.remove(input_file_path)
