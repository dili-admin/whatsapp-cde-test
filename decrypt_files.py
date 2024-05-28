from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import json

def decrypt_file(password, input_file_path):
    with open(input_file_path, 'rb') as infile:
        # Read the salt, IV, and ciphertext from the input file
        salt = infile.read(16)
        iv = infile.read(16)
        ciphertext = infile.read()

    # Derive the key from the password using PBKDF2
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        iterations=100000,
        salt=salt,
        length=32,
        backend=default_backend()
    )
    key = kdf.derive(password.encode())

    # Create a Cipher object with AES in CBC mode
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())

    # Decrypt the ciphertext
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    plaintext = json.loads(plaintext.decode("utf-8"))

    #decrypted file path extension
    #base_path, old_extension = os.path.splitext(input_file_path)

    # Construct the new file path with the desired extension
    #new_file_path = base_path + ".txt"

    # Write the decrypted data to the output file
    #with open(new_file_path, 'wb') as outfile:
    #    outfile.write(plaintext)
    return plaintext

input_file = input("Please enter input file path:\n")
password = input("Please enter decryption key:\n")

print(decrypt_file(password, input_file))
