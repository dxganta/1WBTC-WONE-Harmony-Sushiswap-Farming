from brownie import (
    accounts,
    interface,
    Controller,
    SettV3,
    MyStrategy,
)
from config import (
    BADGER_DEV_MULTISIG,
    WANT,
    REWARD_TOKEN,
    PROTECTED_TOKENS,
    FEES,
)
from dotmap import DotMap
import pytest


@pytest.fixture
def deployed():
    """
    Deploys, vault, controller and strats and wires them up for you to test
    """
    deployer = accounts[0]

    strategist = deployer
    keeper = deployer
    guardian = deployer

    governance = accounts.at(BADGER_DEV_MULTISIG, force=True)

    controller = Controller.deploy({"from": deployer})
    controller.initialize(BADGER_DEV_MULTISIG, strategist,
                          keeper, BADGER_DEV_MULTISIG)

    sett = SettV3.deploy({"from": deployer})
    sett.initialize(
        WANT,
        controller,
        BADGER_DEV_MULTISIG,
        keeper,
        guardian,
        False,
        "prefix",
        "PREFIX",
    )

    sett.unpause({"from": governance})
    controller.setVault(WANT, sett)

    # TODO: Add guest list once we find compatible, tested, contract
    # guestList = VipCappedGuestListWrapperUpgradeable.deploy({"from": deployer})
    # guestList.initialize(sett, {"from": deployer})
    # guestList.setGuests([deployer], [True])
    # guestList.setUserDepositCap(100000000)
    # sett.setGuestList(guestList, {"from": governance})

    #  Start up Strategy
    strategy = MyStrategy.deploy({"from": deployer})
    strategy.initialize(
        BADGER_DEV_MULTISIG,
        strategist,
        controller,
        keeper,
        guardian,
        PROTECTED_TOKENS,
        FEES,
    )

    # Tool that verifies bytecode (run independently) <- Webapp for anyone to verify

    # Set up tokens
    want = interface.IERC20(WANT)
    rewardToken = interface.IERC20(REWARD_TOKEN)

    #  Wire up Controller to Strart
    #  In testing will pass, but on live it will fail
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

    return DotMap(
        deployer=deployer,
        controller=controller,
        vault=sett,
        sett=sett,
        strategy=strategy,
        # guestList=guestList,
        want=want,
        rewardToken=rewardToken,
    )


## Contracts ##


@pytest.fixture
def vault(deployed):
    return deployed.vault


@pytest.fixture
def sett(deployed):
    return deployed.sett


@pytest.fixture
def controller(deployed):
    return deployed.controller


@pytest.fixture
def strategy(deployed):
    return deployed.strategy


## Tokens ##


@pytest.fixture
def want(deployed):
    return deployed.want


@pytest.fixture
def tokens():
    return [WANT, REWARD_TOKEN]


## Accounts ##


@pytest.fixture
def deployer(deployed):
    return deployed.deployer


@pytest.fixture
def strategist(strategy):
    return accounts.at(strategy.strategist(), force=True)


@pytest.fixture
def settKeeper(vault):
    return accounts.at(vault.keeper(), force=True)


@pytest.fixture
def strategyKeeper(strategy):
    return accounts.at(strategy.keeper(), force=True)
