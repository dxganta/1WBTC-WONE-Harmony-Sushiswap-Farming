from brownie import *
from config import (
    BADGER_DEV_MULTISIG,
    WANT,
    REWARD_TOKEN,
    PROTECTED_TOKENS,
    FEES
)
from helpers.constants import MaxUint256
from helpers.SnapshotManager import SnapshotManager


def main():
    return test()


def test():
    deployed = run("mock_deploy")

    deployer = deployed.deployer
    vault = deployed.vault
    controller = deployed.controller
    strategy = deployed.strategy
    want = deployed.want
    randomUser = accounts[6]

    d = deployed.deployer.address
    s = deployed.strategy.address

    print("Balance Of Want ", strategy.balanceOfWant())
    print("Depositing...")
    strategy.testDeposit(strategy.balanceOfWant())
    print("Balance of Pool ", strategy.balanceOfPool())

    chain.sleep(86400)
    chain.mine()

    wone = interface.IERC20(deployed.strategy.wone())
    sushi = interface.IERC20(deployed.strategy.reward())

    minichef = interface.IMiniChefV2(deployed.strategy.MINICHEFV2())

    minichef.harvest(5, s, {"from": s})

    print("Balance of WONE", wone.balanceOf(s))
    print("Balance of Sushi ", sushi.balanceOf(s))

    router = interface.IUniswapRouterV2(
        "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506")

    # 50% ONE -> WBTC
    router.swapExactTokensForTokens(
        (wone.balanceOf(s) * 5) // 10,
        0,
        [deployed.strategy.wone(), deployed.strategy.wbtc()],
        s,
        chain.time(),
        {"from": s}
    )

    wbtc = interface.IERC20(deployed.strategy.wbtc())

    print("Balance of WONE ", wone.balanceOf(s))
    print("Balance of WBTC ", wbtc.balanceOf(s))

    router.addLiquidity(
        wbtc.address,
        wone.address,
        wbtc.balanceOf(s),
        wone.balanceOf(s),
        1,
        1,
        s,
        chain.time(),
        {"from": s}
    )
