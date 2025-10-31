# Contributing to LexTimeCheck

Thank you for your interest in contributing to LexTimeCheck! This document provides guidelines for contributing to the project.

## Ways to Contribute

- 🐛 Report bugs and issues
- 💡 Suggest new features or improvements
- 📝 Improve documentation
- 🔧 Submit bug fixes
- ✨ Add new features
- 📊 Contribute new legal corpora
- 🧪 Add test cases

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/lextimecheck.git
   cd lextimecheck
   ```
3. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Install in development mode**:
   ```bash
   pip install -e ".[dev]"
   ```

## Development Guidelines

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes
- Keep functions focused and modular

Format your code with:
```bash
black lextimecheck/
ruff check lextimecheck/
```

### Testing

Add tests for new features:
```bash
pytest tests/
```

### Documentation

- Update README.md for user-facing changes
- Add docstrings to new functions
- Update type annotations

## Adding a New Corpus

1. Create directory structure:
   ```
   data/your_corpus/
   ├── metadata.json
   ├── version1.txt
   └── version2.txt
   ```

2. metadata.json format:
   ```json
   {
     "version1": {
       "effective_date": "YYYY-MM-DD",
       "enactment_date": "YYYY-MM-DD",
       "authority_level": "statute|regulation|guidance",
       "source_url": "https://..."
     }
   }
   ```

3. Test your corpus:
   ```bash
   python cli.py extract --corpus your_corpus
   ```

4. Submit a pull request with:
   - Corpus data files
   - Brief description in PR
   - Example output (optional)

## Submitting Changes

1. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Brief description of changes"
   ```

2. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create a Pull Request** on GitHub

### Pull Request Guidelines

- Write a clear title and description
- Reference any related issues
- Include examples of output (if applicable)
- Ensure tests pass
- Update documentation as needed

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Help others learn

## Questions?

- Open an issue for questions
- Use GitHub Discussions for broader topics
- Check existing issues before creating new ones

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

