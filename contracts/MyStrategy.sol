// SPDX-License-Identifier: MIT

pragma solidity ^0.6.11;
pragma experimental ABIEncoderV2;

import "../deps/@openzeppelin/contracts-upgradeable/token/ERC20/IERC20Upgradeable.sol";
import "../deps/@openzeppelin/contracts-upgradeable/math/SafeMathUpgradeable.sol";
import "../deps/@openzeppelin/contracts-upgradeable/math/MathUpgradeable.sol";
import "../deps/@openzeppelin/contracts-upgradeable/utils/AddressUpgradeable.sol";
import "../deps/@openzeppelin/contracts-upgradeable/token/ERC20/SafeERC20Upgradeable.sol";

import "../interfaces/badger/IController.sol";
import "../interfaces/sushiswap/IMiniChefV2.sol";
import "../interfaces/uniswap/IUniswapRouterV2.sol";

import {BaseStrategy} from "../deps/BaseStrategy.sol";

contract MyStrategy is BaseStrategy {
    using SafeERC20Upgradeable for IERC20Upgradeable;
    using AddressUpgradeable for address;
    using SafeMathUpgradeable for uint256;

    // address public want // Inherited from BaseStrategy, the token the strategy wants, swaps into and tries to grow
    address public reward; // Token we farm and swap to want / lpComponent

    address public constant SUSHISWAPV2ROUTER = 0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506;
    address public constant MINICHEFV2 = 0x67dA5f2FfaDDfF067AB9d5F025F8810634d84287;
    uint256 public constant POOL_PID = 5;
    address public constant wbtc = 0x3095c7557bCb296ccc6e363DE01b760bA031F2d9;
    address public constant wone = 0xcF664087a5bB0237a0BAd6742852ec6c8d69A27a;
    uint256 public constant MAX_PPM = 10**6; // PARTS PER MILLION 
    uint32 public slippage_tolerance = 5000;  // in PPM, 5000 = 0.5%

    // Used to signal to the Badger Tree that rewards where sent to it
    event TreeDistribution(
        address indexed token,
        uint256 amount,
        uint256 indexed blockNumber,
        uint256 timestamp
    );

    function initialize(
        address _governance,
        address _strategist,
        address _controller,
        address _keeper,
        address _guardian,
        address[2] memory _wantConfig,
        uint256[3] memory _feeConfig
    ) public initializer {
        __BaseStrategy_init(
            _governance,
            _strategist,
            _controller,
            _keeper,
            _guardian
        );
        /// @dev Add config here
        want = _wantConfig[0];
        reward = _wantConfig[1];

        performanceFeeGovernance = _feeConfig[0];
        performanceFeeStrategist = _feeConfig[1];
        withdrawalFee = _feeConfig[2];

        /// @dev do one off approvals here
        IERC20Upgradeable(want).safeApprove(MINICHEFV2, type(uint256).max);
        IERC20Upgradeable(reward).safeApprove(SUSHISWAPV2ROUTER,type(uint256).max);
        IERC20Upgradeable(wone).safeApprove(SUSHISWAPV2ROUTER,type(uint256).max);
        IERC20Upgradeable(wbtc).safeApprove(SUSHISWAPV2ROUTER,type(uint256).max);
    }

    /// ===== View Functions =====

    // @dev Specify the name of the strategy
    function getName() external pure override returns (string memory) {
        return "1WBTC-ONE Sushiswap Farming Strategy";
    }

    // @dev Specify the version of the Strategy, for upgrades
    function version() external pure returns (string memory) {
        return "1.0";
    }

    /// @dev Balance of want currently held in strategy positions
    function balanceOfPool() public view override returns (uint256) {
        (uint256 _pool, ) = IMiniChefV2(MINICHEFV2).userInfo(POOL_PID, address(this));
        return _pool;
    }

    /// @dev Returns true if this strategy requires tending
    function isTendable() public view override returns (bool) {
        return true;
    }

    // @dev These are the tokens that cannot be moved except by the vault
    function getProtectedTokens()
        public
        view
        override
        returns (address[] memory)
    {
        address[] memory protectedTokens = new address[](3);
        protectedTokens[0] = want;
        protectedTokens[1] = reward;
        protectedTokens[2] = wone;
        return protectedTokens;
    }

    /// ===== Internal Core Implementations =====

    /// @dev security check to avoid moving tokens that would cause a rugpull, edit based on strat
    function _onlyNotProtectedTokens(address _asset) internal override {
        address[] memory protectedTokens = getProtectedTokens();

        for (uint256 x = 0; x < protectedTokens.length; x++) {
            require(
                address(protectedTokens[x]) != _asset,
                "Asset is protected"
            );
        }
    }

    /// @dev invest the amount of want
    /// @notice When this function is called, the controller has already sent want to this
    /// @notice Just get the current balance and then invest accordingly
    function _deposit(uint256 _amount) internal override {
        IMiniChefV2(MINICHEFV2).deposit(POOL_PID, _amount, address(this));
    }

    function testDeposit(uint256 _amount) external {
        _deposit(_amount);
    }

    /// @dev utility function to withdraw everything for migration
    function _withdrawAll() internal override {
        // Withdraw all LP tokens from MCV2 and harvest rewards
        IMiniChefV2(MINICHEFV2).withdrawAndHarvest(POOL_PID, balanceOfPool(), address(this));
    }

    /// @dev withdraw the specified amount of want, liquidate from lpComponent to want, paying off any necessary debt for the conversion
    function _withdrawSome(uint256 _amount)
        internal
        override
        returns (uint256)
    {
        uint256 _pool = balanceOfPool();
        if (_amount > _pool) {
            _amount = _pool;
        }
        IMiniChefV2(MINICHEFV2).withdraw(POOL_PID, _amount, address(this));
        return _amount;
    }

    /// @dev Harvest from strategy mechanics, realizing increase in underlying position
    function harvest() external whenNotPaused returns (uint256 harvested) {
        _onlyAuthorizedActors();

        uint256 _before = IERC20Upgradeable(want).balanceOf(address(this));

        // if there are no rewards then return 0
        if (IMiniChefV2(MINICHEFV2).pendingSushi(POOL_PID, address(this)) == 0) {
            return 0;
        }

        IMiniChefV2(MINICHEFV2).harvest(POOL_PID, address(this));

        // convert SUSHI => WONE
        address[] memory _path = new address[](2);
        _path[0] = reward;
        _path[1] = wone;

        IUniswapRouterV2(SUSHISWAPV2ROUTER).swapExactTokensForTokens(
            IERC20Upgradeable(reward).balanceOf(address(this)),
         0, 
         _path, 
         address(this), 
         now
         );

         // convert 50% WONE to WBTC
         _path = new address[](2);
         _path[0] = wone;
         _path[1] = wbtc;
        IUniswapRouterV2(SUSHISWAPV2ROUTER).swapExactTokensForTokens(
            IERC20Upgradeable(wone).balanceOf(address(this)).mul(500000).div(MAX_PPM),
            0, 
            _path,
            address(this),
            now
        );

        // convert to WBTC/WONE LP Tokens
        uint256 _wbtcAmt = IERC20Upgradeable(wbtc).balanceOf(address(this));
        uint256 _woneAmt = IERC20Upgradeable(wone).balanceOf(address(this));
        IUniswapRouterV2(SUSHISWAPV2ROUTER).addLiquidity(
            wbtc,
            wone,
            _wbtcAmt,
            _woneAmt,
            _wbtcAmt.mul(MAX_PPM - slippage_tolerance).div(MAX_PPM),
            _woneAmt.mul(MAX_PPM - slippage_tolerance).div(MAX_PPM),
            address(this),
            now
        );

        uint256 earned =
            IERC20Upgradeable(want).balanceOf(address(this)).sub(_before);

        /// @notice Keep this in so you get paid!
        (uint256 governancePerformanceFee, uint256 strategistPerformanceFee) =
            _processRewardsFees(earned, want);

        /// @dev Harvest event that every strategy MUST have, see BaseStrategy
        emit Harvest(earned, block.number);

        /// @dev Harvest must return the amount of want increased
        return earned;
    }

    // Alternative Harvest with Price received from harvester, used to avoid exessive front-running
    function harvest(uint256 price)
        external
        whenNotPaused
        returns (uint256 harvested)
    {}

    /// @dev Rebalance, Compound or Pay off debt here
    function tend() external whenNotPaused {
        _onlyAuthorizedActors();
        uint256 bal = balanceOfWant();
        if (bal > 0) {
            _deposit(bal);
        }
    }

    /// @dev set the slippage tolerance
      function setSlippageTolerance(uint32 _val) external {
        _onlyAuthorizedActors();
        require(_val <= MAX_PPM);
        slippage_tolerance = _val;
    }

    /// ===== Internal Helper Functions =====

    /// @dev used to manage the governance and strategist fee on earned rewards, make sure to use it to get paid!
    function _processRewardsFees(uint256 _amount, address _token)
        internal
        returns (uint256 governanceRewardsFee, uint256 strategistRewardsFee)
    {
        governanceRewardsFee = _processFee(
            _token,
            _amount,
            performanceFeeGovernance,
            IController(controller).rewards()
        );

        strategistRewardsFee = _processFee(
            _token,
            _amount,
            performanceFeeStrategist,
            strategist
        );
    }
}


// check if rewards are greater than zero

// harvest sushi & one rewards
// check if one rewards are in WONE or ONE 
// convert SUSHI to WONE
// Convert 50% of WONE to 1WBTC
// convert 1WBTC & WONE to 1WBTC/WONE LP Tokens