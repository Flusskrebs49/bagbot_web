# Bagbot_web
A bot for trading alpha in the Bittensor Subnets.

> **⚠️ Warning: Use at your own risk!** There are no guarantees! Try with small amounts first!!

> [!CAUTION]
**HIGHLY RECOMMENDED TO JOIN THE [BITTENSOR ALPHA GROUP](https://taotemplar.com/bag) FOR HELP WITH USE AND STRATEGY**

Adding some improvements on Flusskrebs49/bagbot repo :
- web interface in Flask for remove/add subnets, modifying buy/sell prices
- web interface with logging page (only on local network), brute force, session timeout
- writing the bagbot configuration file on the fly (no need to restart the bot)

## Setup Instructions

Follow these steps to set up and run Bagbot:

#### 1. Clone the repository, navigate to bagbot repository and set up a python virtual environment
*Linux (Windows)*
```
sudo apt update && sudo apt install -y python3.10 python3-pip \
&& git clone https://github.com/taotemplar/bagbot.git \
&& cd bagbot \
&& python3.10 -m venv .bagbotvirtualenv \
&& source .bagbotvirtualenv/bin/activate
```
*MacOS*
```
brew install python@3.10 \
&& git clone https://github.com/taotemplar/bagbot.git \
&& cd bagbot \
&& python3.10 -m venv .bagbotvirtualenv \
&& source .bagbotvirtualenv/bin/activate
```

#### 4. Install Requirements & Flask
   ```bash
   python3 -m pip install -r requirements.txt
   pip install Flask
   ```

#### 5. Move *.html files 
   create \bagbot\templates
   move index.html and login.html to \templates

#### 6. Create a New Wallet
   ```bash
   btcli w create --wallet.name bagbot
   ```

#### 6. Fund the Wallet 
   Send a small amount to the wallet address. To find the address, run the following command and look for the `ss58_address` (e.g., `5Dso...xAi3`):
   ```bash
   btcli w list
   ```

#### 7. Configure Buy/Sell Settings
   Copy the top part of the `bagbot_settings.py` file to a new file named `bagbot_settings_overrides.py`.  
   **Note:** Do **not** copy the bottom 4 lines.

#### 8. Edit the Settings File
   In `bagbot_settings_overrides.py`:
   - Update the `WALLET_PW` variable with your wallet's password.
   - Modify other settings as desired. The file includes notes explaining each variable.
   - Add IP of your influx server, database name, user and password
   - Specify the Master wallet to monitor

## Running the Bot

To start the bot, activate the virtual environment and run the script:
```bash
source ~/.bagbotvirtualenv/bin/activate
python3 bagbot.py
python3 bagbot_web.py
```
You can access to the login page at : http://ip_bagbot:5000
