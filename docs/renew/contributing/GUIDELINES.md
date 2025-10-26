# Contribution Guidelines

Thank you for considering contributing to Agent-Forge! We welcome all contributions, from bug fixes to new features.

To ensure a smooth and collaborative process, please follow these guidelines.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How to Contribute

1.  **Find an Issue**: Look for open issues in the [issue tracker](https://github.com/your-username/agent-forge/issues). If you have a new idea, please open an issue first to discuss it.

2.  **Claim the Issue**: Before you start working, please assign the issue to yourself and add a comment that you are starting work. This prevents duplicate efforts.

3.  **Fork the Repository**: Create a fork of the repository to your own GitHub account.

4.  **Create a Branch**: Create a new branch for your feature or bug fix. Use a descriptive name, like `feat/add-new-agent` or `fix/polling-service-bug`.

    ```bash
    git checkout -b feat/your-feature-name
    ```

5.  **Make Your Changes**: Write your code, following the project's coding style and conventions.

6.  **Add Debug Logging**: Ensure that you add comprehensive debug logging to your code, following the emoji-prefix convention described in the main `README.md`.

7.  **Update `CHANGELOG.md`**: Add an entry to `CHANGELOG.md` under the `[Unreleased]` section, describing your changes.

8.  **Commit Your Changes**: Use the [Conventional Commits](https://www.conventionalcommits.org/) format for your commit messages.

    ```bash
    git commit -m "feat(parser): add support for YAML configs"
    ```

9.  **Push to Your Fork**: Push your changes to your forked repository.

    ```bash
    git push origin feat/your-feature-name
    ```

10. **Open a Pull Request**: Open a pull request from your branch to the `main` branch of the original repository. Provide a clear description of your changes and link the issue you are resolving.

## Coding Style

*   Follow PEP 8 for Python code.
*   Use clear and descriptive variable and function names.
*   Keep functions small and focused on a single task.
*   Add docstrings to all modules, classes, and functions.

## Git Workflow

*   **File-Specific Commits**: Make small, atomic commits that are specific to a single file or a related set of changes. Avoid generic commit messages like "Update files".
*   **Update Changelog First**: Always update `CHANGELOG.md` *before* you create your commit.

Thank you for your contribution!
