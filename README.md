# hyperliquid-python-sdk

<div align="center">

[![Dependencies Status](https://img.shields.io/badge/dependencies-up%20to%20date-brightgreen.svg)](https://github.com/hyperliquid-dex/hyperliquid-python-sdk/pulls?utf8=%E2%9C%93&q=is%3Apr%20author%3Aapp%2Fdependabot)

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Security: bandit](https://img.shields.io/badge/security-bandit-green.svg)](https://github.com/PyCQA/bandit)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/hyperliquid-dex/hyperliquid-python-sdk/blob/master/.pre-commit-config.yaml)
[![Semantic Versions](https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--versions-e10079.svg)](https://github.com/hyperliquid-dex/hyperliquid-python-sdk/releases)
[![License](https://img.shields.io/pypi/l/hyperliquid-python-sdk)](https://github.com/hyperliquid-dex/hyperliquid-python-sdk/blob/master/LICENSE.md)

SDK for Hyperliquid API trading with Python.

</div>

---

> 📦 **AI Trading Bot 已独立**: `ai_trading/` 目录已移至独立仓库 [hyperliquid-ai-trader](../hyperliquid-ai-trader/)。如果您需要使用 AI 交易机器人,请查看新仓库。本仓库专注于 Hyperliquid Python SDK 的核心功能。

---

## Installation

### Install uv

First, install uv using one of the following methods:

#### macOS/Linux (using curl)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Windows (using PowerShell)
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### Using pip
```bash
pip install uv
```

#### Using Homebrew (macOS/Linux)
```bash
brew install uv
```

After installation, restart your terminal or run `source ~/.bashrc` (or `source ~/.zshrc` on macOS) to make uv available in your PATH.

### Using uv (Recommended)

```bash
# Create a virtual environment with Python 3.10
uv venv --python 3.10

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
uv pip install hyperliquid-python-sdk
```
## Configuration 

- Set the public key as the `account_address` in examples/config.json.
- Set your private key as the `secret_key` in examples/config.json.
- See the example of loading the config in examples/example_utils.py

### [Optional] Generate a new API key for an API Wallet
Generate and authorize a new API private key on https://app.hyperliquid.xyz/API, and set the API wallet's private key as the `secret_key` in examples/config.json. Note that you must still set the public key of the main wallet *not* the API wallet as the `account_address` in examples/config.json

## 🤖 AI Trading Bot System

A complete AI-powered trading system using **DeepSeek AI** with advanced technical analysis and RSI divergence detection.

### Quick Start
```bash
# Install dependencies
uv pip install numpy pandas openai schedule python-dotenv

# Set up API key in .env file
cd ai_trading
cp .env.example .env
nano .env  # Add your DEEPSEEK_API_KEY

# Run system test
python test_system.py

# Start the bot (test mode - runs once)
python ai_trader_bot.py --test

# Start the bot (normal mode - runs every 3 minutes)
./start_deepseek.sh
```

### Features
- ✅ Automatic market data collection and technical indicators (EMA, MACD, RSI, ATR)
- ✅ AI-driven trading decisions using DeepSeek Reasoner
- ✅ Advanced RSI divergence detection for reversal signals
- ✅ Automatic risk management with stop-loss and take-profit
- ✅ Multi-coin support (BTC, ETH, SOL, BNB, XRP, DOGE, etc.)
- ✅ JSON mode for guaranteed valid AI responses
- ✅ Testnet support for safe practice

### Documentation
- **[ai_trading/README.md](ai_trading/README.md)** - Complete usage guide and system architecture ⭐
- **[HOSTINGER_DEPLOYMENT.md](HOSTINGER_DEPLOYMENT.md)** - Deploy to Hostinger VPS (24/7) 🚀
- **[CLAUDE.md](CLAUDE.md)** - Development instructions for Claude Code

### Deploy to Cloud (24/7 Trading)
Run your bot on Hostinger VPS with one command:
```bash
wget https://raw.githubusercontent.com/alexanderhanboli/hyperliquid-python-sdk/testnet/deploy/quick_deploy.sh
bash quick_deploy.sh
```
See [HOSTINGER_DEPLOYMENT.md](HOSTINGER_DEPLOYMENT.md) for details.

---

## Usage Examples
```python
from hyperliquid.info import Info
from hyperliquid.utils import constants

info = Info(constants.TESTNET_API_URL, skip_ws=True)
user_state = info.user_state("0xcd5051944f780a621ee62e39e493c489668acf4d")
print(user_state)
```
See [examples](examples) for more complete examples. You can also checkout the repo and run any of the examples after configuring your private key e.g. 
```bash
cp examples/config.json.example examples/config.json
vim examples/config.json
python examples/basic_order.py
```

## Getting started with contributing to this repo

1. Install `uv`: https://docs.astral.sh/uv/. 
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Install Python 3.10 for development. For development we require python 3.10 exactly. Some dependencies have issues on 3.11, while older versions don't have correct typing support.
   ```bash
   brew install python@3.10 && uv python install 3.10
   ```

3. Install dependencies:

```bash
uv sync
```

### Makefile usage

CLI commands for faster development. See `make help` for more details.

```bash
check-safety          Run safety checks on dependencies
cleanup               Cleanup project
install               Install dependencies
install-types         Find and install additional types for mypy
lint                  Alias for the pre-commit target
lockfile-update       Update lock file
lockfile-update-full  Fully regenerate lock file
pre-commit            Run linters + formatters via pre-commit, run "make pre-commit hook=black" to run only black
test                  Run tests with pytest
update-dev-deps       Update development dependencies to latest versions
```

## Releases

You can see the list of available releases on the [GitHub Releases](https://github.com/hyperliquid-dex/hyperliquid-python-sdk/releases) page.

We follow the [Semantic Versions](https://semver.org/) specification and use [`Release Drafter`](https://github.com/marketplace/actions/release-drafter). As pull requests are merged, a draft release is kept up-to-date listing the changes, ready to publish when you’re ready. With the categories option, you can categorize pull requests in release notes using labels.

### List of labels and corresponding titles

|               **Label**               |  **Title in Releases**  |
| :-----------------------------------: | :---------------------: |
|       `enhancement`, `feature`        |        Features         |
| `bug`, `refactoring`, `bugfix`, `fix` |  Fixes & Refactoring    |
|       `build`, `ci`, `testing`        |  Build System & CI/CD   |
|              `breaking`               |    Breaking Changes     |
|            `documentation`            |     Documentation       |
|            `dependencies`             |  Dependencies updates   |

### Building and releasing

Building a new version of the application contains steps:

- Bump the version of your package in `pyproject.toml`. You can pass the new version explicitly, or update it manually following the [Semantic Versions](https://semver.org/) standard.
- Make a commit to `GitHub`
- Create a `GitHub release`
- `uv build && uv publish`

## License

This project is licensed under the terms of the `MIT` license. See [LICENSE](LICENSE.md) for more details.

```bibtex
@misc{hyperliquid-python-sdk,
  author = {Hyperliquid},
  title = {SDK for Hyperliquid API trading with Python.},
  year = {2024},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/hyperliquid-dex/hyperliquid-python-sdk}}
}
```

## Credits

This project was generated with [`python-package-template`](https://github.com/TezRomacH/python-package-template).
