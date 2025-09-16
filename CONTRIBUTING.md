# Contributing to LinkedIn MCP Server

Thank you for your interest in contributing to the LinkedIn MCP Server! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```

## Development Setup

### Environment Configuration

1. Copy `.env.example` to `.env`
2. Fill in your LinkedIn API credentials
3. Configure other environment variables as needed

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_linkedin_mcp.py
```

### Code Quality

We use several tools to maintain code quality:

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

### Pre-commit Hooks

Install pre-commit hooks to automatically run checks:

```bash
pre-commit install
```

## Contribution Guidelines

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes
- Keep functions focused and under 50 lines when possible

### Commit Messages

Use clear, descriptive commit messages:

```
feat: add job application tracking functionality
fix: resolve authentication token refresh issue
docs: update API usage examples
test: add unit tests for profile management
```

### Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with appropriate tests
3. Ensure all tests pass and code quality checks succeed
4. Update documentation if necessary
5. Submit a pull request with a clear description

### Adding New Features

When adding new LinkedIn API integrations:

1. Add the tool definition to `TOOLS` list
2. Implement the handler in `call_tool()` function
3. Add comprehensive tests
4. Update the README with usage examples
5. Consider rate limiting and error handling

### Testing Guidelines

- Write unit tests for all new functionality
- Use mocks for external API calls
- Test both success and failure scenarios
- Maintain test coverage above 80%

## Areas for Contribution

We welcome contributions in these areas:

### High Priority
- LinkedIn API integration implementation
- OAuth 2.0 authentication flow
- Rate limiting and retry logic
- Error handling and logging

### Medium Priority
- Job application tracking database
- Resume parsing and optimization
- Company research automation
- Network analysis tools

### Low Priority
- Performance optimizations
- Additional API endpoints
- UI for configuration management
- Advanced analytics features

## API Integration Guidelines

When implementing LinkedIn API calls:

1. Use async/await for all API calls
2. Implement proper error handling
3. Respect rate limits
4. Cache responses when appropriate
5. Log API requests for debugging

### Example Implementation

```python
async def search_jobs(keywords: str, location: str = None) -> List[Dict]:
    """Search for jobs using LinkedIn API"""
    try:
        # Implement LinkedIn API call
        response = await linkedin_client.search_jobs(
            keywords=keywords,
            location=location
        )
        return response.get('jobs', [])
    except RateLimitExceeded:
        # Handle rate limiting
        await asyncio.sleep(60)
        return await search_jobs(keywords, location)
    except Exception as e:
        logger.error(f"Job search failed: {e}")
        raise
```

## Documentation

When updating documentation:

- Update README.md for user-facing changes
- Add docstrings for new functions
- Include usage examples
- Update configuration options

## Security Considerations

- Never commit API credentials
- Use environment variables for sensitive data
- Implement proper input validation
- Follow OAuth 2.0 best practices

## Questions and Support

If you have questions:

1. Check the existing issues and documentation
2. Create a new issue with detailed information
3. Join our community discussions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to LinkedIn MCP Server!