# Contributing to RealityCheck

Thank you for your interest in contributing to RealityCheck! This document provides guidelines for contributing to this data-driven global analysis platform.

## 🎯 Ways to Contribute

### 📊 Data & Analysis
- **New KPI Sources**: Suggest reliable data sources for additional global indicators
- **Data Quality**: Report data inconsistencies or propose data validation improvements
- **Analysis Enhancement**: Improve AI-generated insights or suggest new analysis dimensions

### 🛠️ Technical Contributions
- **Frontend Improvements**: Enhance visualizations, user interface, or user experience
- **Performance Optimization**: Improve loading times, data processing, or caching
- **Security Enhancements**: Identify and fix security vulnerabilities
- **Mobile Experience**: Optimize for mobile devices and accessibility

### 🌐 Content & Documentation
- **Documentation**: Improve README, user guides, or technical documentation
- **Translations**: Help translate the interface to other languages
- **Educational Content**: Create tutorials or explanation materials

## 🚀 Getting Started

### Development Setup
1. **Clone the repository**
   ```bash
   git clone https://github.com/ckvfox/realitycheck.git
   cd realitycheck
   ```

2. **Install Python dependencies** (for data fetching)
   ```bash
   pip install requests pandas tqdm python-dotenv openai
   ```

3. **Start local development server**
   ```bash
   python -m http.server 8000
   ```

4. **Open in browser**: `http://localhost:8000`

### Project Structure
- `/scripts/` - Data fetching and processing scripts
- `/data/` - KPI datasets and metadata
- `/data/meta/` - Immutable metadata (countries, KPI definitions)
- Frontend: Pure HTML/CSS/JS (no build system)

## 📋 Contribution Process

### For Code Changes
1. **Fork** the repository
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes** following our coding conventions
4. **Test thoroughly** - ensure all pages load and function correctly
5. **Commit with descriptive messages** using conventional commits
6. **Push** to your fork and create a **Pull Request**

### For Data Contributions
1. **Verify data source** - ensure it's reliable and regularly updated
2. **Check data format** - must be compatible with our JSON schema
3. **Add metadata** - include proper attribution and licensing info
4. **Test data integration** - ensure it displays correctly in all views

## 🔍 Code Guidelines

### JavaScript
- Use modern ES6+ features where appropriate
- Follow existing code style and naming conventions
- Add comments for complex logic
- Ensure cross-browser compatibility

### Python (Data Scripts)
- Follow PEP 8 style guidelines
- Use type hints where helpful
- Add docstrings to functions
- Handle errors gracefully

### Data Standards
- All KPI files must follow the standard JSON schema: `[{"country": "Name", "year": 2023, "value": 123.45}, ...]`
- Country names must match the canonical names in `data/meta/countries.json`
- Include proper data source attribution

## 🐛 Reporting Issues

### Bug Reports
Please include:
- **Steps to reproduce** the issue
- **Expected behavior** vs actual behavior
- **Browser and version** information
- **Screenshots** if relevant

### Feature Requests
Please include:
- **Clear description** of the proposed feature
- **Use case** - why would this be valuable?
- **Mockups or examples** if applicable

## 📊 Data Sources & Ethics

### Data Quality Standards
- Use only reliable, publicly available data sources
- Prefer official government and international organization data
- Ensure data is regularly updated and maintained
- Respect data licensing and attribution requirements

### Ethical Guidelines
- Maintain objectivity in data presentation
- Avoid biased interpretations or misleading visualizations
- Respect privacy and sensitive information guidelines
- Acknowledge data limitations and uncertainties

## 🏷️ Commit Message Format

Use conventional commits for clear history:
```
feat: add new KPI for renewable energy adoption
fix: resolve country name mapping issue
docs: update installation instructions
style: improve mobile responsive design
perf: optimize data loading performance
```

## 🎉 Recognition

Contributors will be acknowledged in:
- Repository contributors list
- Release notes for significant contributions
- About page credits (for major feature contributions)

## 📞 Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Create an Issue with the bug report template
- **Security Issues**: Email privately to the maintainer

## 📄 License

By contributing to RealityCheck, you agree that your contributions will be licensed under the same license as the project.

---

**Thank you for helping make global data more accessible and understandable! 🌍📊**