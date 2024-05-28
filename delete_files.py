import os
from datetime import datetime, timedelta
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import re
from encrypt_files import encrypt_file

password = "RW9TntGwoutrYwZT2qrs9DrNtaaLw36paqqMV9PpD92IPlw1OSMXUBqDMQjx"
directory_path = "BureauReports"

def extract_decision(byte_text):
    # Convert bytes to string
    #print(byte_text)
    text = byte_text.decode('utf-8') 


    # Define a regular expression pattern to find the "decision" field and its value
    pattern = r'decision"\s*:\s*"([^"]*)"'

    # Search for the pattern in the text
    match = re.search(pattern, text)

    # Check if a match is found
    if match:
        decision = match.group(1)
        print(f"The decision is: {decision}")
        return decision
    else:
        print("Decision not found in the text.")
        return None

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

    return plaintext

def delete_old_files(directory_path):
    # Get the current date and time
    current_date = datetime.now()

    # Iterate through the files in the directory
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        print(f"Checking Expiry time for the file: {filename}")

        #check file extension
        base_path, file_extension = os.path.splitext(file_path)

        if file_extension == '.bin':
            decrypted_text = decrypt_file(password, file_path)
        else:
            with open(file_path, 'rb') as infile:
                decrypted_text = infile.read()
        
        decision = extract_decision(decrypted_text)
        # Specify the number of days to keep
        if decision in ['Approve','Approved']:
            days_to_keep = 10
        elif decision in ['Review','Decline','Declined']:
            days_to_keep = 31
        else:
            days_to_keep = 31


        print(f'decison is {decision} so keeping files for {days_to_keep}')
        # Calculate the date threshold for deletion
        threshold_date = current_date - timedelta(days=days_to_keep)

        # Extract the date part from the filename
        date_str = filename[:19]

        # Convert the date part to a datetime object
        file_date = datetime.strptime(date_str, "%d_%m_%Y_%H_%M_%S")

        # Delete files older than the threshold date
        if file_date < threshold_date:
            os.remove(file_path)
            print(f"Deleted file: {filename}")


# Call the function to delete old files
delete_old_files(directory_path)




