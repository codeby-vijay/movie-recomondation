# 🎬 CineAI - AI Movie Recommendation System

<p align="center">
  <strong>A Netflix-inspired movie recommendation website powered by Machine Learning</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Flask-3.1-green?logo=flask" alt="Flask">
  <img src="https://img.shields.io/badge/scikit--learn-1.6-orange?logo=scikit-learn" alt="scikit-learn">
  <img src="https://img.shields.io/badge/Bootstrap-5.3-purple?logo=bootstrap" alt="Bootstrap">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
</p>

---

## ✨ Features

### 🤖 Machine Learning
- **Content-Based Filtering** — TF-IDF + Cosine Similarity
- **Collaborative Filtering** — KNNBasic + SVD (Surprise library)
- **Hybrid Recommendations** — Weighted combination of both approaches
- **Model Evaluation** — RMSE, MAE, Precision@K, Recall@K with cross-validation
- **Auto-generated Charts** — Genre distribution, rating histogram, model comparison

### 🎯 User Features
- User registration & login with password hashing
- Star rating system (0.5–5.0)
- Favorites & watchlist management
- Personalized AI recommendations
- Movie search with autocomplete suggestions
- Search history tracking
- Recommendation history

### 🎨 Frontend
- Netflix-inspired dark theme with glassmorphism
- Responsive design (desktop, tablet, mobile)
- Smooth animations & hover effects
- Hero banner with backdrop images
- Horizontal scrolling movie carousels
- Loading skeletons & toast notifications

### 👑 Admin Dashboard
- System statistics overview
- User management (CRUD, admin toggle)
- Movie management (add, edit, delete)
- Dataset upload (CSV)
- ML model retraining
- Visualization charts
- Application log viewer

---

## 🏗️ Architecture

```
Clean Architecture · MVC Pattern · SOLID Principles · Repository Pattern
```

### Folder Structure

```
movie/
├── app/                          # Flask application
│   ├── __init__.py               # App factory
│   ├── controllers/              # Controllers
│   ├── database/                 # Database utilities
│   ├── middleware/                # Request middleware
│   ├── models/                   # SQLAlchemy models
│   │   ├── user.py               # User, SearchHistory
│   │   └── movie.py              # Movie, Rating, Favorite, Watchlist, RecommendationLog
│   ├── repositories/             # Data access layer
│   │   ├── user_repository.py    # User CRUD
│   │   └── movie_repository.py   # Movie, Rating, Favorite, Watchlist repos
│   ├── routes/                   # Blueprint routes
│   │   ├── main_routes.py        # Homepage
│   │   ├── auth_routes.py        # Authentication
│   │   ├── movie_routes.py       # Movie browsing & interactions
│   │   ├── recommendation_routes.py  # Recommendations
│   │   ├── admin_routes.py       # Admin dashboard
│   │   └── api_routes.py         # REST API
│   ├── services/                 # Business logic
│   │   ├── auth_service.py       # Auth logic
│   │   ├── movie_service.py      # Movie logic
│   │   └── recommendation_service.py  # ML orchestration
│   ├── static/
│   │   ├── css/style.css         # Main stylesheet
│   │   ├── js/app.js             # Main JavaScript
│   │   └── images/               # Posters, charts
│   ├── templates/                # Jinja2 HTML templates
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── about.html
│   │   ├── auth/                 # Login, Register, Profile
│   │   ├── movies/               # Browse, Detail, Search, Favorites, Watchlist
│   │   ├── recommendations/      # Recommend, History
│   │   ├── admin/                # Dashboard, Users, Movies, Models, Upload, Stats, Logs
│   │   └── errors/               # 404, 500, 403
│   └── utils/
│       └── helpers.py            # Utility functions
├── ml/                           # Machine Learning pipeline
│   ├── preprocessing/            # Data loading & feature engineering
│   ├── content_based/            # TF-IDF + Cosine Similarity
│   ├── collaborative/            # KNN + SVD
│   ├── hybrid/                   # Weighted combination
│   ├── evaluation/               # Model metrics
│   └── visualization/            # Chart generation
├── scripts/
│   ├── load_data.py              # Data import script
│   └── generate_charts.py        # Chart generation script
├── tests/
│   ├── test_models.py            # Model unit tests
│   ├── test_routes.py            # Route integration tests
│   └── test_ml.py                # ML pipeline tests
├── data/
│   ├── raw/                      # MovieLens CSV files
│   ├── processed/                # Processed features
│   └── models/                   # Trained ML models
├── docs/                         # Documentation
├── logs/                         # Application logs
├── instance/                     # SQLite database
├── config.py                     # Configuration
├── run.py                        # Entry point
├── requirements.txt              # Dependencies
├── .env.example                  # Environment template
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- pip

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/cineai-movie-recommender.git
cd cineai-movie-recommender
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings (optional)
```

### 5. Download MovieLens Dataset

Download the [MovieLens Latest Small](https://grouplens.org/datasets/movielens/latest/) dataset and extract the CSV files into `data/raw/`:

```
data/raw/
├── movies.csv
├── ratings.csv
├── links.csv
└── tags.csv
```

### 6. Load Data & Train Models

```bash
python scripts/load_data.py
```

This will:
- Load all CSV data into SQLite
- Create an admin user (`admin` / `admin123`)
- Preprocess features (TF-IDF, genre encoding)
- Train content-based and collaborative models
- Generate visualization charts

### 7. Run the Application

```bash
python run.py
```

Visit: **http://localhost:5000**

---

## 📡 REST API

| Method | Endpoint               | Description              | Auth |
|--------|------------------------|--------------------------|------|
| GET    | `/api/movies`          | List movies (paginated)  | No   |
| GET    | `/api/movies/<id>`     | Movie details            | No   |
| GET    | `/api/movies/search?q=`| Search movies            | No   |
| GET    | `/api/movies/trending` | Trending movies          | No   |
| GET    | `/api/movies/popular`  | Popular movies           | No   |
| GET    | `/api/movies/genres`   | All genres               | No   |
| GET    | `/api/recommend`       | Get recommendations      | Yes  |
| POST   | `/api/rate`            | Rate a movie             | Yes  |
| POST   | `/api/favorite`        | Toggle favorite          | Yes  |
| POST   | `/api/watchlist`       | Toggle watchlist         | Yes  |
| GET    | `/api/statistics`      | System stats (admin)     | Admin|

---

## 🧠 ML Pipeline

### Phase 1: Data Cleaning
- Remove duplicates, handle missing values
- Extract year from movie titles
- Normalize rating ranges

### Phase 2: Feature Engineering
- Genre binary encoding
- Tag aggregation per movie
- TF-IDF vectorization (5000 features, bigrams)
- Rating statistics (mean, count)

### Phase 3: Content-Based Filtering
- TF-IDF matrix from genres + tags
- Cosine similarity matrix
- Per-movie and per-user recommendations

### Phase 4: Collaborative Filtering
- **KNNBasic**: User-based, cosine similarity, k=40
- **SVD**: 100 factors, 20 epochs, regularized
- 3-fold cross-validation
- Metrics: RMSE, MAE, Precision@10, Recall@10

### Phase 5: Hybrid Recommendations
- Weighted combination (40% content + 60% collaborative)
- Score normalization to [0, 1]
- Fallback to available method

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_models.py -v
python -m pytest tests/test_routes.py -v
python -m pytest tests/test_ml.py -v
```

---

## 🔒 Security

- **Password Hashing**: Werkzeug PBKDF2 with SHA-256
- **Environment Variables**: Sensitive config in `.env`
- **Input Sanitization**: XSS prevention on all inputs
- **SQL Injection Prevention**: SQLAlchemy parameterized queries
- **Admin Access Control**: `@admin_required` decorator

---

## 📊 Visualization

Generated charts (saved to `static/images/charts/`):
- Genre Distribution
- Rating Distribution
- Top Rated Movies
- Most Active Users
- Movie Release Timeline
- Model Comparison (RMSE & MAE)
- Recommendation Algorithm Usage

---

## 🚢 Deployment

### Render
1. Connect your GitHub repository
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `gunicorn run:app`
4. Add environment variables from `.env.example`

### Railway
1. Connect repository
2. Add Python buildpack
3. Set start command: `gunicorn run:app --bind 0.0.0.0:$PORT`
4. Configure environment variables

### PythonAnywhere
1. Upload project files
2. Create virtualenv: `mkvirtualenv --python=/usr/bin/python3.12 cineai`
3. Install requirements: `pip install -r requirements.txt`
4. Set WSGI file to import `app` from `run.py`
5. Configure static files path

### Docker (Optional)
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["gunicorn", "run:app", "--bind", "0.0.0.0:5000"]
```

---

## 🛠️ Tech Stack

| Layer           | Technology                           |
|-----------------|--------------------------------------|
| **Backend**     | Python 3.12, Flask 3.1, SQLAlchemy   |
| **Database**    | SQLite                               |
| **Auth**        | Flask-Login, Werkzeug                |
| **ML**          | scikit-learn, Surprise, Pandas, NumPy|
| **Viz**         | Matplotlib                           |
| **Frontend**    | HTML5, CSS3, Bootstrap 5, JavaScript |
| **API**         | RESTful JSON endpoints               |

---

## 📝 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file.

---

## 🙏 Acknowledgements

- [MovieLens](https://grouplens.org/datasets/movielens/) by GroupLens Research
- [TMDb](https://www.themoviedb.org/) for movie metadata
- [Surprise](https://surpriselib.com/) for collaborative filtering
- [scikit-learn](https://scikit-learn.org/) for ML utilities
- [Bootstrap](https://getbootstrap.com/) for UI components

---

<p align="center">
  Built with ❤️ using Flask + Machine Learning
</p>
