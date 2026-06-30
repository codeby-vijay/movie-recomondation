# CineAI - API Documentation

## Base URL
```
http://localhost:5000/api
```

## Authentication
Most endpoints require authentication via Flask-Login sessions. Login via the web UI at `/auth/login` to establish a session, then use the session cookie for API requests.

## Endpoints

### Movies

#### GET `/api/movies`
Get paginated list of movies.

**Parameters:**
| Param    | Type   | Default | Description          |
|----------|--------|---------|----------------------|
| page     | int    | 1       | Page number          |
| per_page | int    | 20      | Items per page       |
| genre    | string | ""      | Filter by genre      |

**Response:**
```json
{
  "success": true,
  "movies": [...],
  "page": 1,
  "pages": 50,
  "total": 1000,
  "has_next": true,
  "has_prev": false
}
```

---

#### GET `/api/movies/<id>`
Get movie details by ID.

**Response:**
```json
{
  "success": true,
  "movie": {
    "id": 1,
    "title": "Toy Story (1995)",
    "genres": "Animation|Children|Comedy",
    "year": 1995,
    "poster_url": "...",
    "average_rating": 4.2,
    "rating_count": 215
  }
}
```

---

#### GET `/api/movies/search?q=<query>`
Search movies by title.

**Parameters:**
| Param | Type   | Description    |
|-------|--------|----------------|
| q     | string | Search query   |
| page  | int    | Page number    |

---

#### GET `/api/movies/trending`
Get trending movies (highest popularity).

#### GET `/api/movies/popular`
Get most popular movies (most rated).

#### GET `/api/movies/genres`
Get all available genres.

---

### Recommendations

#### GET `/api/recommend` (Auth Required)
Get personalized movie recommendations.

**Parameters:**
| Param     | Type   | Default | Description                           |
|-----------|--------|---------|---------------------------------------|
| algorithm | string | hybrid  | Algorithm: hybrid, content, svd, knn  |
| n         | int    | 10      | Number of recommendations (max 50)    |

**Response:**
```json
{
  "success": true,
  "algorithm": "hybrid",
  "recommendations": [
    {
      "movie_id": 318,
      "title": "Shawshank Redemption, The (1994)",
      "genres": "Crime|Drama",
      "score": 0.9423,
      "algorithm": "hybrid"
    }
  ]
}
```

---

### User Actions

#### POST `/api/rate` (Auth Required)
Rate a movie.

**Body:**
```json
{
  "movie_id": 1,
  "rating": 4.5
}
```

#### POST `/api/favorite` (Auth Required)
Toggle favorite status.

**Body:**
```json
{
  "movie_id": 1
}
```

#### POST `/api/watchlist` (Auth Required)
Toggle watchlist status.

**Body:**
```json
{
  "movie_id": 1
}
```

---

### Admin

#### GET `/api/statistics` (Admin Required)
Get system statistics.

---

## HTTP Status Codes

| Code | Description              |
|------|--------------------------|
| 200  | Success                  |
| 400  | Bad request / validation |
| 401  | Unauthorized             |
| 403  | Forbidden (not admin)    |
| 404  | Resource not found       |
| 500  | Internal server error    |

## Error Response Format
```json
{
  "success": false,
  "message": "Error description",
  "status": 404
}
```
