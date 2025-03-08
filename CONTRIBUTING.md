# Contributing to Document-it

Thank you for your interest in contributing to Document-it! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Package Management](#package-management)
- [Project Structure](#project-structure)

## Code of Conduct

By participating in this project, you agree to uphold the following principles:

- Be respectful and inclusive towards all contributors
- Provide constructive feedback
- Focus on the best interests of the project
- Be open to collaboration and different viewpoints

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** to your local machine
   ```
   git clone https://github.com/yourusername/document-it.git
   cd document-it
   ```
3. **Add the original repository as upstream**
   ```
   git remote add upstream https://github.com/originalowner/document-it.git
   ```
4. **Create a new branch** for your feature or bugfix
   ```
   git checkout -b feature/your-feature-name
   ```

## Development Environment

### Prerequisites

- Python 3.11 or higher
- UV package manager

### Setting Up

1. **Install dependencies**
   ```
   uv sync
   ```

2. **Set up environment variables**
   Create a `.env` file in the project root with:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   LANGGRAPH_TRACING_V2=true
   LOG_LEVEL=INFO
   ```

3. **Verify installation**
   ```
   uv run python main.py --help
   ```

## Development Workflow

1. **Sync with upstream** before starting work
   ```
   git fetch upstream
   git rebase upstream/main
   ```

2. **Implement your changes** following the code standards

3. **Run tests** to ensure your changes don't break existing functionality
   ```
   uv run pytest
   ```

4. **Update documentation** if your changes modify behavior or API

5. **Commit your changes** with clear, descriptive commit messages
   ```
   git add .
   git commit -m "feat: implement parallelization for document processing"
   ```

6. **Push to your fork**
   ```
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request** against the main repository

## Code Standards

### Python Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guide
- Use 4 spaces for indentation (not tabs)
- Maximum line length of 88 characters
- Use type hints for function parameters and return values
- Document classes and functions with docstrings (Google style)

### Naming Conventions

- `snake_case` for variables, functions, and methods
- `PascalCase` for classes
- `UPPER_CASE` for constants

### Architecture Guidelines

- Follow the component architecture outlined in the project documentation
- Keep components loosely coupled
- Implement appropriate error handling
- Write code that is testable and maintainable

## Testing

All new code should include appropriate tests:

- **Unit tests** for individual functions and classes
- **Integration tests** for component interactions
- **End-to-end tests** for critical workflows

To run tests:
```
uv run pytest
```

To run tests with coverage:
```
uv run pytest --cov=document_it
```

## Documentation

Documentation is a crucial part of this project:

- **Code Documentation**: Use docstrings and clear variable names
- **Functional Documentation**: Update or create markdown files in the `docs/` directory
- **README Updates**: Update README.md if your changes add or modify features

## Pull Request Process

1. **Create a descriptive PR** that explains what your changes do and why
2. **Link any related issues** using GitHub's issue linking syntax
3. **Ensure all tests pass** and code meets quality standards
4. **Request reviews** from maintainers
5. **Address review feedback** promptly
6. **Update the CHANGELOG.md** with details of your changes
7. **Wait for approval** from at least one maintainer before merging

## Package Management (UV Only)

This project uses UV exclusively for package management. Key points:

- **No pip, pipenv, or poetry**: Use UV for all Python dependency management
- **Add dependencies to pyproject.toml**: When adding new dependencies
- **Run `uv sync`**: After updating dependencies to resolve and install them
- **Document dependency purpose**: Add comments for less common libraries

## Project Structure

```
document_it/
├── analysis/          # Document analysis components
├── context/           # Context extraction and management
├── parser/            # File and document parsing
├── processor/         # Document processing pipeline
├── reporting/         # Report generation
└── web/               # Web connector components

tests/                 # Test suite
└── fixtures/          # Test fixtures

docs/                  # Documentation
data/                  # Data directories for input/output
```

## Feature Planning

Before implementing major features:

1. **Create an issue** describing the feature and its benefits
2. **Discuss implementation approaches** with the community
3. **Create a design document** in the docs/ directory
4. **Get approval** from maintainers before starting implementation

## Questions or Need Help?

If you have questions or need help, please:

1. Check the existing documentation
2. Search for similar issues on GitHub
3. Open a new issue with a clear description of your question

Thank you for contributing to Document-it!