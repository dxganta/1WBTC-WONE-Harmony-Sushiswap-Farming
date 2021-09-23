# Ideally, they have one file with the settings for the strat and deployment
# This file would allow them to configure so they can test, deploy and interact with the strategy

BADGER_DEV_MULTISIG = "0xb65cef03b9b89f99517643226d76e286ee999e77"

WANT = "0xc3670b927eF42eed252e483e2446352C238D9905"  # 1WBTC/WONE
LP_COMPONENT = ""  #
REWARD_TOKEN = "0xbec775cb42abfa4288de81f387a9b1a3c4bc552a"  # 1SUSHI Token
# REWARD_TOKEN_2 = ""  # ONE

PROTECTED_TOKENS = [WANT, LP_COMPONENT, REWARD_TOKEN]
#  Fees in Basis Points
DEFAULT_GOV_PERFORMANCE_FEE = 1000
DEFAULT_PERFORMANCE_FEE = 1000
DEFAULT_WITHDRAWAL_FEE = 50

FEES = [DEFAULT_GOV_PERFORMANCE_FEE,
        DEFAULT_PERFORMANCE_FEE, DEFAULT_WITHDRAWAL_FEE]

REGISTRY = "0xFda7eB6f8b7a9e9fCFd348042ae675d1d652454f"  # Multichain BadgerRegistry
