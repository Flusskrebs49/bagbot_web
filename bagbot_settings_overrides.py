ELEGRAM_TOKEN = "xxxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TELEGRAM_CHAT_ID = "11111111111"
STAKE_ON_VALIDATOR = "5CszMVts9ueMUSKdAwLFSLT7u4oyxN7fUBpo8Z3ETw1ggMUV"
WALLET_PW = 'xxxxxxxx' #Replace with your wallet's password that you entered into btcli
WALLET_NAME = 'xxxxxxxx' #The name of the wallet created in btcli
WATCHED_WALLETS = {
    "Wallet_Invest": "5Cxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",   # adresse SS58 publique
}
# Note: LOWER THAN 0.01 MAY CAUSE THE BUYS TO FAIL WHILE STILL TAKING THE GAS FEE
MAX_TAO_PER_BUY = 0.1 #May increase as desired, I wouldnt reduce it.
MAX_TAO_PER_SELL = 0.3 #May increase as desired, I wouldnt reduce it
MAX_SLIPPAGE_PERCENT_PER_BUY = 2 #If over this slippage %, buy trades won't execute.

# Power curve settings for buy/sell zones (1.0 = linear, >1.0 = more aggressive early, <1.0 = more conservative early)
# Must be positive. Suggested range: 0.1 to 10
BUY_ZONE_POWER = 1.0  # Power curve exponent for buy price progression
SELL_ZONE_POWER = 1.0  # Power curve exponent for sell price progression

# buy_lower is the lowest price that the bot will allocate your max_alpha amount to.  Will only purchase this low if you hold near the max_alpha amount.
# buy_upper is the highest price that the bot will allocate your max_alpha amount to.  Will only purchase this high if you hold no alpha in the subnet yet.
# sell_lower is the lowest price that the bot will sell your alpha.  Will only sell this low if you hold near the max_alpha amount.
# sell_upper is the highest price that the bot will sell your alpha.  Will only sell this high if you hold near almost no alpha in the subnet.
# max_alpha is the maximum amount of alpha to buy in the subnet, the bot will not purchase more.
#
# OPTIONAL PER-SUBNET OVERRIDES (if not specified, uses global defaults above):
# stake_on_validator - Override which validator hotkey to stake on for this subnet (default: STAKE_ON_VALIDATOR)
# max_tao_per_buy - Override max TAO per buy for this subnet (default: MAX_TAO_PER_BUY)
# max_tao_per_sell - Override max TAO per sell for this subnet (default: MAX_TAO_PER_SELL)
# max_slippage_percent_per_buy - Override max slippage % for this subnet (default: MAX_SLIPPAGE_PERCENT_PER_BUY)
# buy_zone_power - Override buy zone power curve for this subnet (default: BUY_ZONE_POWER)
# sell_zone_power - Override sell zone power curve for this subnet (default: SELL_ZONE_POWER)
SUBNET_SETTINGS = {
    107: {
        'buy_lower': 0.00255,
        'buy_upper': 0.00485,
        'sell_lower': 0.02345,
        'sell_upper': 0.02845,
        'max_alpha': 27,
    },
    100: {
        'buy_lower': 0.00955,
        'buy_upper': 0.01175,
        'sell_lower': 0.02055,
        'sell_upper': 0.02655,
        'max_alpha': 27,
    },
}
     # Example overrides (optional):
     # 'max_tao_per_buy': 0.05,  # Use 0.05 TAO per buy instead of global default
     # 'max_tao_per_sell': 0.03,  # Use 0.03 TAO per sell instead of global default
     # 'max_slippage_percent_per_buy': 0.3,  # Allow 0.3% slippage instead of global default
     # 'stake_on_validator': '5SomeOtherValidatorHotkeyHere',  # Stake on different validator
     # 'buy_zone_power': 2.0,  # More aggressive buying early (stays near buy_upper longer)
     # 'sell_zone_power': 0.5,  # More conservative selling early (drops to sell_lower faster)


#Could have a pending withdraw already - if you hit max and it gives you an amount do that, then itll let you queue up another withdraw
