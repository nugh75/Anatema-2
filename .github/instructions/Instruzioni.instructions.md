applyTo: '**'
---
Provide project context and coding guidelines that AI should follow when generating code, answering questions, or reviewing changes.

# Project context
- This project may involve different types of programming tasks, including Python scripting, frontend/backend development, and educational software tools.
- The user often works with AI models, Flask, Streamlit, PostgreSQL, and various educational frameworks.
- Each task must be grounded in real user interaction and oriented to practical outcomes.
- The project may involve academic research, particularly in education and artificial intelligence.

# Coding guidelines
- Always write clear, modular, and well-commented code.
- Prefer readability and maintainability over excessive optimization.
- Follow PEP8 standards for Python code.
- When generating HTML/CSS/JS, ensure accessibility and semantic HTML.
- Include minimal working examples (MWE) when appropriate.
- Use relative imports when working in a package.
- Avoid hardcoding values unless explicitly required.
- Use environment variables for secrets and configurations.

# Interaction protocol
- When executing or simulating terminal commands:  
  - If no output is returned or the terminal appears unresponsive, **always prompt the user to confirm if the command worked as expected**.
  - Ask if the user would like to retry, check logs, or debug further.

# Planning and documentation
- For **each task requested**, generate a corresponding `.md` file that outlines:
  - The goal of the task
  - Input requirements
  - Steps to be followed
  - Expected outcome
  - Any dependencies

- Additionally, maintain a **meta `.md` file** that:
  - Lists and links all individual task plans
  - Describes the overall project structure
  - Tracks progress and any open issues
  - Serves as a coordination hub for the project

# Review and change management
- When reviewing code or documentation:
  - Highlight not only errors but also opportunities for improvement
  - Suggest refactorings with justifications
  - Respect the original style unless otherwise indicated

# Language and communication
- Be formal and clear
- Use correct terminology, especially in educational or technical contexts
- Do not assume unless explicitly instructed; prefer asking for clarification

