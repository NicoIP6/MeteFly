import requests
import time
import getpass
import os 

# Get the identifier registered as an environment variable (you must replace TOKEN and ID by you variable in str)

bot_token = os.getenv('TOKEN')
user_id = os.getenv('ID')

# built a function who send Telegram message (see the Telegram doc to create your personal chatbot)
# It will be used to send potential problem while downloading files from the server

def alert_sender(message):
    url_telegram = f"https://api.telegram.org/bot{bot_token}/sendMessage" # Connect to the Telegram API with the personal token
    payload = {
        "chat_id": user_id,
        "text": message
    }
    response = requests.post(url_telegram, data=payload)
    if response.status_code == 200:
        print("Message sent successfully.")
    else:
        print(f"Error while sending : {response.text}")



DELAY = 30
username = input("Enter your username : ")
password = getpass.getpass("Enter a valid password : ")
# Warning: some IDE won't support getpass in their native shells and would print your password in clear (like PyCharm)

try:
    file_nasa = "/home/nico/Documents/MeteFly/subset_M2T1NXSLV_5.12.4_20241120_085335_.txt"
    # This File must contain all the links for files downloading
    # (for the Merra files it's one link one file and one file a day)
    # Read de Merra documentation, some steps must be done to access to the server without problem
    with open(file_nasa, "r") as f:
        urls = [line.strip() for line in f if line.strip()] # Split the file to have a list with each link
    for url in urls:
        result = requests.get(url, auth=(username, password), stream=True)
        filename = url.split("/")[-1] # the end of the url that contain the date and the type of model
        try: # Try to download and save the file
            print(f"Status : {result.raise_for_status} - Start downloading")
            with open(filename, "wb") as f:
                f.write(result.content)
            print(f"{filename} downloaded")
        except requests.exceptions.RequestException as e: # Send a Telegram Message with the request code if in error
            alert_sender(f"Error {str(e)}: {result.status_code} - {result.reason} - {filename}")
        time.sleep(DELAY) # This delay is used to avoid server overload (in second)
except Exception as e:
    alert_sender(f"Job in error : {str(e)}")
