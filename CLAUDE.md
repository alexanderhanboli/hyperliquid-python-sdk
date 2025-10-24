# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **Hyperliquid Python SDK** - a comprehensive Python library for trading on Hyperliquid DEX. The project includes:

1. **Core SDK** (`hyperliquid/`) - API client for Hyperliquid trading
2. **AI Trading System** (`ai_trading/`) - DeepSeek-powered automated trading bot with RSI divergence detection

**Current branch**: testnet (main branch is master for PRs)

## Development Setup

### Prerequisites
- Python 3.9+ (development requires Python 3.10)
- Poetry for dependency management

### Installation & Dependencies

```bash
# Download and install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python -

# Install dependencies
make install

# Install additional type stubs for mypy
make install-types
```

### Configuration
- Copy `examples/config.json.example` to `examples/config.json`
- Add your wallet's public key as `account_address`
- Add your private key as `secret_key` (or use API wallet private key - see README.md)

## Common Development Commands

```bash
# Run linters and formatters
make lint
# Or run just black: make pre-commit hook=black

# Run tests
make test

# Type checking with mypy
poetry run mypy --config-file pyproject.toml ./

# Safety checks on dependencies
make check-safety

# Update dependencies
make lockfile-update
make update-dev-deps

# Clean project
make cleanup
```

### Run Specific Tests

```bash
# Run a single test file
poetry run pytest tests/signing_test.py -v

# Run tests matching a pattern
poetry run pytest -k "test_order" -v

# Run with coverage report
poetry run pytest --cov=hyperliquid tests/
```

## Code Quality & Pre-commit Hooks

The project uses pre-commit hooks configured in `.pre-commit-config.yaml` for:

- **Code formatting**: black (120 char line length), isort
- **Linting**: flake8, pylint, pyupgrade
- **Security**: bandit (excludes tests/)
- **Type checking**: mypy (strict config)
- **Config validation**: YAML, TOML, JSON schema checks

Tools are managed via Poetry and run through `make lint` (equivalent to `make pre-commit`).

## Codebase Architecture

### Core SDK Structure (`hyperliquid/`)

**Main modules**:
- `exchange.py:Exchange` - Main class for executing trades (orders, cancellations, liquidation orders, spot transfers)
- `info.py:Info` - Market data queries (user state, positions, trades, open orders, l2 data, funding rates, etc.)
- `api.py:API` - Low-level HTTP request wrapper
- `signing.py` - Order signing, transaction signing, and cryptographic utilities
- `utils/constants.py` - API URLs (MAINNET_API_URL, TESTNET_API_URL) and chain IDs
- `utils/types.py` - Type definitions (uses Python 3.10+ typing)
- `websocket_manager.py` - WebSocket connection management

**Key relationships**:
- `Exchange` uses `Info` internally to fetch current prices for order validation
- Order creation flow: `OrderRequest` → `order_request_to_order_wire()` → sign order → `exchange.order()` → POST to API
- Data types are strongly typed with detailed TypedDict definitions in `utils/types.py`

### AI Trading System (`ai_trading/`)

**Architecture**:
```
Market Data (Hyperliquid)
    ↓
market_data.py (data fetching + technical indicators + RSI divergence detection)
    ↓
prompt_builder.py (formats data into AI-friendly prompt)
    ↓
DeepSeek API (or Claude via Anthropic - currently DeepSeek)
    ↓
order_executor.py (parses AI decision JSON and executes trades)
    ↓
History Storage (automatic, keeps last 50 trades)
```

**Core components**:
- `ai_trader_bot.py` - Main entry point. Handles CLI args, loads config from `.env` via python-dotenv, runs trading loop
- `market_data.py:MarketDataFetcher` - Fetches OHLCV data, calculates EMA(20), MACD, RSI(7/14), ATR; detects RSI divergences (bullish/bearish) with strength scoring
- `prompt_builder.py:PromptBuilder` - Builds structured prompts with market data, technical indicators, account state, and RSI divergence signals
- `order_executor.py:OrderExecutor` - Executes trade decisions: opens positions with leverage, sets stop-loss/take-profit, handles closing
- `view_history.py` - CLI tool to view trade history, AI reasoning, and token usage stats

**Configuration**:
- Uses `python-dotenv` to load `DEEPSEEK_API_KEY` from `.env` file
- Command-line args: `--coins BTC ETH`, `--top-coins N`, `--interval 3`, `--testnet`, `--model deepseek-reasoner`
- Defaults: testnet, deepseek-reasoner model, major coins, 3-minute interval

**Key features**:
- RSI divergence detection (P0/P1/P2 strength levels) - strongest reversal signal
- Multi-period confirmation (RSI(7) + RSI(14) same signal = strong)
- Automatic account balance fetching (reads real balance, not hardcoded)
- Automatic history rotation (keeps last 50 trades in `ai_trading/history/`)
- Supports both margin trading (leverage) and simple buy/sell

## Testing Strategy

- Unit tests in `tests/` use pytest with VCR cassettes for HTTP recording (`--record-mode=once`)
- Test coverage reporting to HTML: `htmlcov/index.html`
- Test config in `pyproject.toml` includes doctest for inline examples
- Key test files: `info_test.py`, `signing_test.py`

## Type System

- **Strictly typed**: mypy with `check_untyped_defs=true`, `disallow_incomplete_defs=true`
- **Python 3.10 syntax**: Uses newer typing features (TypedDict, UnionType)
- **Type exceptions**: `utils/types.py` has `# type: ignore` for types-requests compatibility
- Pre-commit hook runs mypy on all files

## Git Workflow & Release Management

- Follow **Semantic Versioning** (major.minor.patch)
- Release labels map to sections: `enhancement`/`feature` → Features, `bug`/`fix` → Fixes & Refactoring, `breaking` → Breaking Changes
- Bump version: `poetry version <major|minor|patch>`
- Release flow: commit → create GitHub release → `poetry publish --build`

## Common Task Patterns

### Adding New Order Types

1. Add to `signing.py:OrderType` enum
2. Implement in `exchange.py:Exchange` (create request, sign, post)
3. Update `utils/types.py` with related TypedDict definitions
4. Add test case in `tests/signing_test.py`

### Querying Market Data

```python
from hyperliquid.info import Info
from hyperliquid.utils.constants import TESTNET_API_URL

info = Info(TESTNET_API_URL, skip_ws=True)
l2_data = info.l2_snapshot("BTC")  # OrderBook
trades = info.recent_trades("BTC")
funding_rates = info.funding_history("BTC", 100)
```

### Placing Orders

1. Create order request with all parameters
2. Use `order_request_to_order_wire()` to convert
3. Sign with private key via `sign_l1_action()` or wallet integration
4. Post to Exchange API via `exchange.order()`

### Testing AI Trading

```bash
# Test system setup (checks imports, API connectivity)
python ai_trading/test_system.py

# Run bot once
python ai_trading/ai_trader_bot.py --test

# View last trade
python ai_trading/view_history.py list 1

# Check token usage
python ai_trading/view_history.py tokens
```

## Deployment

For 24/7 trading on Hostinger VPS:
- Use `deploy/quick_deploy.sh` for one-command setup
- See `HOSTINGER_DEPLOYMENT.md` for detailed guide
- Bot runs via systemd service (auto-restart, logging)

## Important Notes

- **Security**: Private keys should never be committed. Use environment variables or `.env` files with python-dotenv
- **Testnet first**: Always test on testnet before mainnet trading
- **Leverage is risky**: Default leverage is 5x-40x; start conservative
- **API limits**: No formal rate limits documented, but avoid hammering endpoints
- **Order sizes**: Minimum order value is $10 USD
- **Funding rates**: Check `info.funding_history()` for cost of holding positions

## Documentation References

- **README.md** - Project overview, installation, usage examples
- **AI_TRADING_GUIDE.md** - Complete AI trading system documentation (Claude Sonnet based)
- **QUICK_START.md** - Quick start for basic trading
- **ORDER_TYPES_GUIDE.md** - Detailed order type documentation
- **ai_trading/README.md** - DeepSeek-based trading bot documentation with RSI divergence
- **SECURITY.md** - Security best practices
- **LEARNING_RESOURCES.md** - Learning materials for Hyperliquid API

## Current Development Status

- **Active branch**: testnet
- **Modified files**: `ai_trading/order_executor.py` (DeepSeek integration, order quantity precision)
- **Recent changes**: DeepSeek Context Caching support, history file cleanup, AI trading improvements
