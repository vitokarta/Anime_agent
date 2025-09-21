# Anime Recommendation AI Agent

An intelligent anime recommendation system powered by tag-based filtering and rating-based sorting, with SQLite database storage for efficient data management.

## 🚀 Features

- 🏷️ **Smart Tag Filtering**: Precise anime search based on genre and category tags
- ⭐ **Rating-Based Sorting**: Automatic ranking by user ratings in descending order
- 🔢 **Flexible Results Control**: Configurable top-N recommendation limits
- 📊 **Rating Threshold**: Minimum rating filtering for quality assurance
- 💾 **Persistent Storage**: SQLite database for reliable local data storage
- 🤖 **AI-Powered Recommendations**: Intelligent content matching and suggestions
- 🌐 **RESTful API**: Clean API endpoints for integration
- 🖥️ **Web Interface**: Modern frontend for user interaction

## 🛠️ Tech Stack

- **Backend**: Python, Flask, SQLite
- **Frontend**: React.js
- **AI/ML**: LangChain, OpenAI API
- **Package Management**: UV (Ultra-fast Python package manager)
- **Database**: SQLite with custom anime schema

## 📋 Prerequisites

- Python 3.9+
- Node.js 16+ (for frontend)
- Windows 10/11 (current setup optimized for Windows)

## ⚡ Quick Start (Windows with UV)

We use [UV](https://github.com/astral-sh/uv) - an extremely fast Python package and environment manager. Follow steps 1-4 to start development immediately.

### 1. Install UV (Single executable, no system Python required)
```powershell
irm https://astral.sh/uv/install.ps1 | iex
# If uv is not recognized in current window:
$env:PATH += ";$HOME\.local\bin"; uv --version
```

### 2. Create and Activate Virtual Environment
```powershell
# Create .venv directory (skip if exists)
uv venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1
# Alternative activation method:
.venv\Scripts\activate
```

### 3. Install Project Dependencies
```powershell
uv pip install -r requirements.txt
```

### 4. Run the Application
```powershell
# Start the Flask API server
python api.py

# In a new terminal, start the frontend (if available)
cd frontend
npm install
npm start
```

### 5. Adding New Dependencies
```powershell
uv pip install <package-name>
uv pip freeze > requirements.txt
```

> **Note**: Steps 1-4 are sufficient for development. Advanced dependency locking with `requirements.in` and `uv pip compile` can be implemented later for production deployments.

## 📁 Project Structure

```
anime_agent/
├── api.py                 # Flask API server
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── anime_database.db     # SQLite database
├── anime_data/           # Raw anime data and images
│   ├── data/            # CSV data files by season/year
│   └── images/          # Anime cover images
├── docs/                # Documentation
├── frontend/            # React.js web interface
├── mcp_*/              # Model Context Protocol integrations
├── models/             # AI model configurations
├── utils/              # Utility functions and database queries
│   ├── database/       # Database utilities
│   └── *.py           # Various utility modules
└── memory/             # LangChain memory implementations
```

## 🔧 Configuration

Key configuration files:
- `config.py`: Main application settings
- `requirements.txt`: Python package dependencies
- `frontend/package.json`: Frontend dependencies

## 📖 API Documentation

### Anime Endpoints

- `GET /api/anime` - Get all anime with optional filtering
- `GET /api/anime/{id}` - Get specific anime details
- `POST /api/anime/like/{id}` - Update like/dislike status
- `GET /api/anime/recommendations` - Get AI-powered recommendations

### Search and Filter

- `POST /api/search` - Advanced search with multiple criteria
- `GET /api/tags` - Get available tags and genres
- `GET /api/ratings` - Get rating statistics

## 🧪 Testing

```powershell
# Run test suite
python -m pytest tests/

# Run specific test file
python test.py
```

## 🤝 Development Workflow

### Branch Strategy

- **Main Branch**: `main` (production-ready, deployable)
- **Feature Branches**: Short-lived branches for specific features/fixes
- **Integration**: Pull Request workflow for code review

### Git Workflow

#### Initial Setup
```bash
git clone <repository-url>
cd anime_agent
git checkout -b feature/<feature-name>
```

#### Daily Development
```bash
# Sync with main branch
git checkout main
git pull origin main
git checkout feature/<feature-name>
git rebase main  # or: git merge main
```

#### Making Changes
```bash
git add .
git commit -m "feat: add new recommendation algorithm"
git push -u origin feature/<feature-name>
```

#### Integration Options

**Option A: Merge Commit (preserves branch history)**
```bash
git checkout main
git pull origin main
git merge --no-ff feature/<feature-name>
git push origin main
```

**Option B: Linear History (rebase + fast-forward)**
```bash
git checkout feature/<feature-name>
git rebase origin/main
git checkout main
git merge --ff-only feature/<feature-name>
git push origin main
```

#### Cleanup
```bash
git checkout main
git pull origin main
git branch -d feature/<feature-name>
git push origin --delete feature/<feature-name>
```

### Git Commands Reference

| Action | Command |
|--------|---------|
| Create feature branch | `git checkout -b feature/<description>` |
| Sync main | `git pull origin main` |
| Update feature branch | `git rebase main` or `git merge main` |
| Push changes | `git push` (first time: `git push -u`) |
| Resolve conflicts | `git add; git rebase --continue` |
| Delete local branch | `git branch -d <branch>` |
| Delete remote branch | `git push origin --delete <branch>` |
| Merge with history | `git merge --no-ff <branch>` |
| Linear merge | `git rebase main → git merge --ff-only <branch>` |

## 🚀 Deployment

### Production Setup

1. **Environment Variables**: Configure production settings
2. **Database**: Set up production SQLite or migrate to PostgreSQL
3. **Static Files**: Build and serve frontend assets
4. **Process Management**: Use systemd, supervisor, or Docker

### Docker Support (Optional)

```dockerfile
# Dockerfile example
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "api.py"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the code style
4. Add tests for new functionality
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Anime data sourced from various public APIs
- UI components inspired by modern design systems
- AI recommendations powered by advanced language models

## 📞 Support

For support and questions:
- Open an issue on GitHub
- Check the [documentation](docs/)
- Review existing discussions and solutions

---

**Development Principles**: 
- No direct development on main branch
- Small, focused commits
- One feature per branch
- Maintain replayable history (rebase or merge before PR)
