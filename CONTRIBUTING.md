# Contributing to Template Rooms Package

We welcome contributions to the Template Rooms Package! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally or use the template:
   ```bash
   git clone https://github.com/synvex-ai/template-rooms-pkg.git
   cd template-rooms-pkg
   ```
3. **Install the package in development mode**:
   ```bash
   pip install -e .
   ```

## Development Setup

### Code Quality Tools

This project uses automated code quality tools:

- **Ruff**: Fast Python linter and formatter
- **Pre-commit**: Runs quality checks before each commit

Install development dependencies:
```bash
pip install ruff pre-commit
```

Setup pre-commit hooks:
```bash
pre-commit install
```

### Code Style

- We use **Ruff** for linting and formatting
- Run `ruff check .` to check for issues
- Run `ruff format .` to format code
- Pre-commit hooks will automatically run these checks

## Making Changes

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following these guidelines:
   - Follow existing code patterns and conventions
   - Add appropriate docstrings and comments
   - Ensure code passes all quality checks

3. **Test your changes**:
   - Ensure the addon still loads and functions correctly
   - Test any new functionality you've added

4. **Commit your changes** using conventional commit format:
   ```bash
   git commit -m "feat: add new feature description"
   git commit -m "fix: resolve bug description"
   ```

## Commit Message Format

We use [Conventional Commits](https://www.conventionalcommits.org/) for automated versioning:

- `feat:` - New features (minor version bump)
- `fix:` - Bug fixes (patch version bump)
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

For breaking changes, add `BREAKING CHANGE:` in the commit body.

## Pull Request Process

1. **Push your branch** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request** on GitHub with:
   - Clear title describing the change
   - Detailed description of what was changed and why
   - Reference any related issues

3. **Ensure all checks pass**:
   - Code quality checks (Ruff)
   - Any automated tests

4. **Address review feedback** if needed

## Code Review Guidelines

- Be respectful and constructive in feedback
- Focus on code quality, maintainability, and adherence to project standards
- Ask questions if something is unclear
- Suggest improvements where appropriate

## Reporting Issues

When reporting issues:

1. **Check existing issues** first to avoid duplicates
2. **Use the issue template** if available
3. **Provide clear steps to reproduce** the problem
4. **Include relevant information**:
   - Python version
   - Package version
   - Error messages and stack traces
   - Minimal code example if applicable

## Feature Requests

For feature requests:

1. **Check existing issues** for similar requests
2. **Clearly describe the feature** and its use case
3. **Explain why it would be valuable** to the project
4. **Consider backward compatibility** implications

## Documentation

- Update documentation for any new features or changes
- Ensure README.md reflects current functionality
- Add docstrings to new functions and classes
- Update configuration examples if needed

## Release Process

Releases are automated using semantic release:

1. Changes are merged to `main` branch
2. Semantic release analyzes commit messages
3. Version is automatically bumped
4. Changelog is generated
5. GitHub release is created

## Getting Help

- **Issues**: Use GitHub issues for bug reports and feature requests
- **Discussions**: Use GitHub discussions for general questions
- **Email**: Contact SYNVEX at contact@synvex.com for other inquiries

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing to Template Rooms Package!