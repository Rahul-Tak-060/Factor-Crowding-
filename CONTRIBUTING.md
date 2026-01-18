# Contributing to Factor Crowding Analysis

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Code of Conduct

* Be respectful and inclusive
* Focus on constructive feedback
* Help maintain a welcoming environment

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
* Clear description of the problem
* Steps to reproduce
* Expected vs actual behavior
* Python version and environment details

### Suggesting Enhancements

For feature requests:
* Describe the enhancement clearly
* Explain the use case
* Provide examples if applicable

### Pull Requests

1. **Fork the repository** and create a feature branch
2. **Make your changes** with clear, atomic commits
3. **Add tests** for new functionality
4. **Update documentation** as needed
5. **Run quality checks:**
   ```bash
   make format lint type-check test
   ```
6. **Submit a PR** with a clear description

## Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/factor-crowding-crash-risk.git
cd factor-crowding-crash-risk

# Install in development mode
uv pip install -e ".[dev]"

# Set up pre-commit hooks
make setup
```

## Code Style

* Follow **PEP 8** conventions
* Use **Black** for formatting (100 char line length)
* Use **type hints** for all functions
* Write **docstrings** for public APIs (Google style)
* Keep functions focused and testable

## Testing

* Write tests for all new features
* Maintain test coverage above 80%
* Use meaningful test names
* Include edge cases

```bash
# Run tests
pytest

# With coverage
pytest --cov --cov-report=html
```

## Commit Messages

Use clear, descriptive commit messages:

```
Add quantile regression for tail risk analysis

- Implement QuantReg model for 5th percentile returns
- Add tests for quantile regression fitting
- Update documentation with usage examples
```

## Documentation

* Update README for user-facing changes
* Add docstrings for all public functions
* Update design.md for methodology changes
* Include examples where helpful

## Questions?

Feel free to open an issue for any questions about contributing!
