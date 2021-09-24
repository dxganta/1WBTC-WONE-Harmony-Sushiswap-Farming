from brownie import *
from config import (
    BADGER_DEV_MULTISIG,
    WANT,
    REWARD_TOKEN,
    PROTECTED_TOKENS,
    FEES
)
from dotmap import DotMap


def main():
    return deploy()


def deploy():
    """
      Deploys, vault, controller and strats and wires them up for you to test
      Also runs a uniswap to get you some funds
      NOTE: Tests use fixtures outside this file
      NOTE: This is just for testing, these settings are not ready for production
      NOTE: If you fork any network beside mainnet, you'll need to do some tweaking
    """
    deployer = accounts[0]

    strategist = deployer
    keeper = deployer
    guardian = deployer

    governance = accounts.at(BADGER_DEV_MULTISIG, force=True)

    controller = Controller.deploy({"from": deployer})
    controller.initialize(
        BADGER_DEV_MULTISIG,
        strategist,
        keeper,
        BADGER_DEV_MULTISIG
    )

    sett = SettV3.deploy({"from": deployer})
    sett.initialize(
        WANT,
        controller,
        BADGER_DEV_MULTISIG,
        keeper,
        guardian,
        False,
        "prefix",
        "PREFIX"
    )

    sett.unpause({"from": governance})
    controller.setVault(WANT, sett)

    # TODO: Add guest list once we find compatible, tested, contract
    # guestList = VipCappedGuestListWrapperUpgradeable.deploy({"from": deployer})
    # guestList.initialize(sett, {"from": deployer})
    # guestList.setGuests([deployer], [True])
    # guestList.setUserDepositCap(100000000)
    # sett.setGuestList(guestList, {"from": governance})

    # Start up Strategy
    strategy = MyStrategy.deploy({"from": deployer})
    strategy.initialize(
        BADGER_DEV_MULTISIG,
        strategist,
        controller,
        keeper,
        guardian,
        PROTECTED_TOKENS,
        FEES
    )

    # Tool that verifies bytecode (run independetly) <- Webapp for anyone to verify

    # Set up tokens
    want = interface.IERC20(WANT)
    rewardToken = interface.IERC20(REWARD_TOKEN)

    # Wire up Controller to Strart
    # In testing will pass, but on live it will fail
    controller.approveStrategy(WANT, strategy, {"from": governance})
    controller.setStrategy(WANT, strategy, {"from": deployer})

    # Sushiswap some tokens here
    router = interface.IUniswapRouterV2(
        "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506")

    WBTC = "0x3095c7557bcb296ccc6e363de01b760ba031f2d9"
    WONE = "0xcF664087a5bB0237a0BAd6742852ec6c8d69A27a"

    wbtc = interface.IERC20(WBTC)
    wone = interface.IERC20(WONE)

    wbtc.approve(router.address, 999999999999999999999999999999,
                 {"from": deployer})
    wone.approve(router.address, 999999999999999999999999999999,
                 {"from": deployer})

    # ONE -> WBTC
    router.swapExactETHForTokens(
        0,
        [WONE, WBTC],
        deployer,
        9999999999999999,
        {"from": deployer, "value": 5 * 10**10 * 10**18}
    )

    # ONE -> WONE
    interface.IWETH(WONE).deposit(
        {"from": deployer, "value": 5 * 10**10 * 10**18})

    # Swap them for WBTC-WONE
    router.addLiquidity(
        wbtc,
        wone,
        wbtc.balanceOf(deployer),
        wone.balanceOf(deployer),
        1,
        1,
        deployer,
        9999999999999999,
        {"from": deployer}
    )

    want.transfer(strategy, want.balanceOf(deployer), {"from": deployer})

    return DotMap(
        deployer=deployer,
        controller=controller,
        vault=sett,
        sett=sett,
        strategy=strategy,
        # guestList=guestList,
        want=want,
        rewardToken=rewardToken
    )
