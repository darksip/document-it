# Contributing to Document-it

Thank you for considering contributing to Document-it! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Development Environment Setup](#development-environment-setup)
- [Repository Structure](#repository-structure)
- [Development Workflow](#development-workflow)
- [Pull Request Process](#pull-request-process)
- [Changelog Updates](#changelog-updates)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone. Please:

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## How to Contribute

### Reporting Issues

If you find a bug or have a suggestion for improvement:

1. Check if the issue already exists in the [Issues](https://github.com/yourusername/document-it/issues) section
2. If not, create a new issue with a clear description, including:
   - Steps to reproduce (for bugs)
   - Expected behavior
   - Actual behavior
   - Screenshots or code snippets if applicable
   - System information

### Contributing Code

1. **Fork the repository** to your GitHub account
2. **Clone your fork** to your local machine
   ```bash
   git clone https://github.com/your-username/document-it.git
   cd document-it
   ```
3. **Create a new branch** for your changes
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Make your changes** following the [Development Workflow](#development-workflow)
5. **Commit your changes** with clear, descriptive commit messages
   ```bash
   git commit -m "feat: Add new feature for XYZ"
   ```
6. **Push your changes** to your fork
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Submit a pull request** to the main repository

## Development Environment Setup

### Requirements

- Python 3.11 or higher
- UV package manager

### Setup Steps

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/document-it.git
   cd document-it
   ```

2. Install dependencies using UV
   ```bash
   uv sync
   ```

3. Create a `.env` file with required environment variables
   ```bash
   # OpenAI API Key (required for LLM functionality)
   OPENAI_API_KEY=your_openai_api_key_here
   
   # LangGraph Configuration
   LANGGRAPH_TRACING_V2=true
   
   # Logging Level
   LOG_LEVEL=INFO
   ```

### Important: Package Management with UV Only

> **Note:** This project uses the **UV package manager exclusively**. Do not use `pip`, `pipenv`, `poetry`, or any other tool for dependency management.

As specified in our project rules:

- Always use `uv sync` to install dependencies
- Update `pyproject.toml` when adding new dependencies
- Commit changes to the lockfile to ensure reproducibility
- To run any Python command, prefix it with `uv run`, e.g., `uv run python main.py`
- Document any less common libraries in code comments or project docs

## Repository Structure

```
document-it/
├── data/                # Data directory for input/output files
├── docs/                # Project documentation
├── document_it/         # Main package
│   ├── analysis/        # Document analysis components
│   ├── context/         # Context extraction and management
│   ├── parser/          # File parsing functionality
│   ├── processor/       # Document processing logic
│   ├── reporting/       # Report generation
│   └── web/             # Web connectivity components
├── tests/               # Test suite
│   ├── context/         # Tests for context modules
│   └── fixtures/        # Test fixtures
├── .env                 # Environment variables (not committed)
├── .gitignore           # Git ignore file
├── main.py              # Main application entry point
├── pyproject.toml       # Project configuration and dependencies
└── README.md            # Project README
```

## Development Workflow

### Coding Standards

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use type hints for function parameters and return values
- Document classes and functions with docstrings
- Keep functions small and focused on a single responsibility
- The project uses Ruff for linting with a line length of 88 characters

### Adding New Features

1. **Plan your implementation**:
   - Consider how it fits into the existing architecture
   - Review the documentation in the `/docs` directory
   - Consider global context management implications

2. **Write tests first**:
   - Create unit tests for new functionality
   - Ensure tests are placed in the appropriate test module

3. **Implement your feature**:
   - Follow existing patterns and coding style
   - Add appropriate error handling
   - Include clear logging statements

4. **Document your changes**:
   - Update function/class docstrings
   - Add implementation details to the relevant `/docs` files
   - Update the README.md if necessary

### Testing

1. Run tests using UV:
   ```bash
   uv run pytest tests/
   ```

2. For specific test modules:
   ```bash
   uv run pytest tests/test_analysis.py
   ```

3. For verbose output:
   ```bash
   uv run pytest tests/ -v
   ```

### Documentation

- Document all public functions, classes, and methods with docstrings
- Keep implementation notes in the `/docs` directory
- Update documentation when changing functionality

## Pull Request Process

1. **Ensure tests pass**: All tests must pass before a PR can be merged
2. **Update documentation**: Ensure all changes are properly documented
3. **Update the CHANGELOG.md**: Add an entry for your changes (see below)
4. **Submit the PR**: Include a clear description of the changes and any relevant issue numbers
5. **Code review**: Address any feedback from reviewers
6. **Approval**: PRs require approval from at least one maintainer

## Changelog Updates

When submitting a PR, update the `CHANGELOG.md` file with:

1. A summary of your changes under the `[Unreleased]` section
2. A brief commit message that describes the main goal of your changes

Format your changelog entry following the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format:

```markdown
## [Unreleased]

### Added
- New feature that does something

### Changed
- Improvement to existing feature

### Fixed
- Bug fix for something

## Commit Summary
feat: Brief summary of the purpose of this change

Longer description with more details about what the changes accomplish...
```

Thank you for contributing to Document-it!