# Contributing Guidelines

Thank you for your interest in contributing to the Civic Grant Agent Core project! This document provides guidelines and instructions for contributing.

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of background, identity, or experience level.

### Expected Behavior

- Be respectful and considerate
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Trolling or insulting/derogatory comments
- Public or private harassment
- Publishing others' private information
- Other conduct that could be considered inappropriate

## How to Contribute

### Reporting Bugs

Before submitting a bug report:

1. **Check existing issues** to avoid duplicates
2. **Verify the bug** in the latest version
3. **Collect information** about the bug

When submitting a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the issue
- **Expected behavior** vs. **actual behavior**
- **Environment details** (OS, Python version, etc.)
- **Logs or error messages**
- **Screenshots** if applicable

**Template:**

```markdown
## Bug Description
Brief description of the bug

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., Ubuntu 20.04]
- Python Version: [e.g., 3.9.5]
- Package Version: [e.g., 1.0.0]

## Additional Context
Any other relevant information
```

### Suggesting Enhancements

Enhancement suggestions are welcome! Please:

1. **Check existing feature requests** to avoid duplicates
2. **Provide clear use case** for the enhancement
3. **Explain why it would be useful** to users
4. **Consider implementation complexity**

**Template:**

```markdown
## Feature Description
Clear description of the proposed feature

## Use Case
Why is this feature needed? What problem does it solve?

## Proposed Solution
How should this feature work?

## Alternatives Considered
What other approaches have you considered?

## Additional Context
Screenshots, examples, or other relevant information
```

### Submitting Pull Requests

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/my-feature`)
3. **Make your changes** following coding standards
4. **Add or update tests** for your changes
5. **Update documentation** if needed
6. **Run tests and linting** to ensure quality
7. **Commit your changes** with clear messages
8. **Push to your fork**
9. **Submit a pull request** to the main repository

**Pull Request Guidelines:**

- **One feature per PR** - Keep PRs focused
- **Write clear commit messages** - Follow conventional commits
- **Include tests** - All new code should be tested
- **Update documentation** - Keep docs in sync with code
- **Pass all checks** - Tests, linting, type checking must pass
- **Be responsive** - Address review comments promptly

**Pull Request Template:**

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issues
Fixes #(issue number)

## Changes Made
- Change 1
- Change 2
- Change 3

## Testing
How were these changes tested?

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] No new warnings
```

## Development Process

### Setting Up Development Environment

See [Development Guide](Development.md#development-setup) for detailed setup instructions.

### Coding Standards

#### Python Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Maximum line length: 100 characters
- Use type hints for all functions
- Write docstrings for all public functions/classes

#### Code Quality Tools

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type check
mypy src/

# Run all checks
pre-commit run --all-files
```

#### Testing Requirements

- **Unit tests** for all new functions
- **Integration tests** for new features
- **Minimum 80% code coverage**
- **All tests must pass** before merging

```bash
# Run tests
pytest

# Check coverage
pytest --cov=src --cov-report=html
```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**

```
feat(scout): add support for state-specific searches

Implement query generation that includes state abbreviations
for more targeted search results.

Closes #42
```

```
fix(validator): correct eligibility score calculation

The eligibility score was incorrectly weighted. This fix
ensures proper weighting according to the configuration.

Fixes #89
```

### Branch Naming

Use descriptive branch names:

- `feature/add-grant-tracker-agent`
- `bugfix/fix-pdf-parsing-error`
- `docs/improve-getting-started`
- `refactor/simplify-validator-logic`

## Pull Request Review Process

### Review Criteria

Reviewers will check:

1. **Functionality** - Does it work as intended?
2. **Code Quality** - Is the code clean and maintainable?
3. **Tests** - Are there adequate tests?
4. **Documentation** - Is documentation updated?
5. **Performance** - Any performance concerns?
6. **Security** - Any security issues?

### Review Timeline

- Initial review within 2-3 business days
- Follow-up reviews within 1-2 business days
- Merge after approval from at least one maintainer

### Addressing Review Comments

- Be open to feedback
- Ask questions if something is unclear
- Make requested changes promptly
- Mark conversations as resolved when addressed

## Types of Contributions

### Bug Fixes

- **High Priority**: Critical bugs affecting functionality
- **Medium Priority**: Non-critical bugs
- **Low Priority**: Minor issues, typos, etc.

### New Features

Before implementing a major feature:

1. **Open an issue** to discuss the feature
2. **Get maintainer approval** before starting work
3. **Break down** large features into smaller PRs
4. **Provide examples** of usage

### Documentation

Documentation improvements are always welcome:

- Fix typos or unclear explanations
- Add examples or tutorials
- Improve API documentation
- Translate documentation

### Tests

Help improve test coverage:

- Add missing unit tests
- Add integration tests
- Improve test organization
- Add test fixtures

## Areas Needing Contribution

### High Priority

- [ ] Implement core agent functionality
- [ ] Add comprehensive test coverage
- [ ] Create example configurations
- [ ] Write user tutorials

### Medium Priority

- [ ] Add more search strategies
- [ ] Improve eligibility checking logic
- [ ] Enhance draft generation templates
- [ ] Add support for more document formats

### Low Priority

- [ ] Add web interface
- [ ] Implement grant tracking
- [ ] Add notification system
- [ ] Create visualization tools

## Getting Help

If you need help with contributing:

1. **Read the documentation** - Start with the [Development Guide](Development.md)
2. **Search existing issues** - Someone may have had the same question
3. **Ask in discussions** - Use GitHub Discussions for questions
4. **Contact maintainers** - Reach out if you're stuck

## Recognition

Contributors will be:

- Listed in `CONTRIBUTORS.md`
- Mentioned in release notes for their contributions
- Acknowledged in documentation where appropriate

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see `LICENSE` file).

## First-Time Contributors

New to open source? Here are some good first issues:

- Issues labeled `good first issue`
- Documentation improvements
- Adding tests
- Fixing typos

Don't be afraid to ask questions!

## Advanced Contribution Topics

### Adding New Agents

See [Development Guide - Implementing New Agents](Development.md#implementing-new-agents)

### Adding New Tools

See [Development Guide - Implementing New Tools](Development.md#implementing-new-tools)

### Performance Optimization

When optimizing:

- **Profile first** - Use cProfile to identify bottlenecks
- **Measure impact** - Quantify improvements
- **Maintain correctness** - Don't sacrifice correctness for speed
- **Document trade-offs** - Explain optimization choices

### Security Considerations

- **Never commit secrets** - Use environment variables
- **Validate inputs** - Check all user inputs
- **Handle errors safely** - Don't expose sensitive information
- **Follow security best practices**

## Release Process

Maintainers handle releases, but here's the process:

1. Update version numbers
2. Update `CHANGELOG.md`
3. Create release branch
4. Run full test suite
5. Tag release
6. Merge to main
7. Deploy to PyPI (if applicable)
8. Create GitHub release

## Communication Channels

- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: Questions, general discussion
- **Pull Requests**: Code contributions
- **Email**: For security issues (see SECURITY.md)

## Questions?

If you have questions about contributing, please:

1. Check this guide
2. Review the [Development Guide](Development.md)
3. Search existing issues and discussions
4. Open a new discussion

Thank you for contributing to Civic Grant Agent Core! 🚒🎉
