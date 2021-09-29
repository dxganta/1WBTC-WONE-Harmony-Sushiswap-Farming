# 1WBTC-WONE Sushiswap Yield Farming on Harmony Mainnet
<img src="https://user-images.githubusercontent.com/47485188/134777888-d7573e4f-7c46-46c1-a92d-a23d1ceec645.png"></img>
## Deposit
The strategy takes WBTC-WONE LP tokens as deposit and deposits them to Sushiswap's 1WBTC/WONE Liquidity Pool for Yield Generation.

<img src="https://user-images.githubusercontent.com/47485188/134771527-9945e8cb-d32a-4299-94ef-ddf383b63392.png">

## Harvest
Including the fees, we get 1SUSHI AND WONE rewards, which are converted to 1WBTC/WONE LP tokens and deposited back into the strategy.

## Expected Yield
As of Sept 25, 2021
Fees APR => <strong>18.21%</strong><br>
Rewards APR => <strong>20.30%</strong>

## Installation and Setup

1. [Install Brownie](https://eth-brownie.readthedocs.io/en/stable/install.html) & [Ganache-CLI](https://github.com/trufflesuite/ganache-cli), if you haven't already.

2. Install the dependencies in the package

```
## Javascript dependencies
npm i

## Python Dependencies
pip install virtualenv
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Add Harmony to your brownie networks list
```
brownie networks import network-config.yaml
```

4. Increase the default balance of an account (since we are dealing with One here & not Ether)
```
brownie networks modify harmony-main-fork default_balance="1000000 ether"
```

## Basic Use

To deploy the Strategy in a development environment:

1. Open the Brownie console. This automatically launches Ganache on a forked mainnet.

```bash
  brownie console
```

2. Run Scripts for Deployment

```
  brownie run 1_production_deploy.py
```

Deployment will set up a Vault, Controller and deploy your strategy

3. Run the test deployment in the console and interact with it

```python
  brownie console
  deployed = run("mock_deploy")

  ## Takes a minute or so
  Transaction sent: 0xa0009814d5bcd05130ad0a07a894a1add8aa3967658296303ea1f8eceac374a9
  Gas price: 0.0 gwei   Gas limit: 12000000   Nonce: 9
  UniswapV2Router02.swapExactETHForTokens confirmed - Block: 12614073   Gas used: 88626 (0.74%)

  ## Now you can interact with the contracts via the console
  >>> deployed
  {
      'controller': 0x602C71e4DAC47a042Ee7f46E0aee17F94A3bA0B6,
      'deployer': 0x66aB6D9362d4F35596279692F0251Db635165871,
      'rewardToken': 0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9,
      'sett': 0x6951b5Bd815043E3F842c1b026b0Fa888Cc2DD85,
      'strategy': 0x9E4c14403d7d9A8A782044E86a93CAE09D7B2ac9,
      'vault': 0x6951b5Bd815043E3F842c1b026b0Fa888Cc2DD85,
      'want': 0x6B175474E89094C44Da98b954EedeAC495271d0F
  }
  >>>

  ## Deploy also sushiswaps want to the deployer (accounts[0]), so you have funds to play with!
  >>> deployed.want.balanceOf(a[0])
  240545908911436022026

```

## Tests
Due to some problem with the RPC provider (most probably), running all the tests together causes some weird errors. Therefore, it is 
needed to run each test file independently one by one.
```
brownie test tests/test_profitable.py 
```
```
brownie test tests/examples/test_basic.py
```
```
brownie test tests/examples/test_are_you_trying.py
```
```
brownie test tests/examples/test_harvest_flow.py
```
```
brownie test tests/examples/test_strategy_permissions.py
```
