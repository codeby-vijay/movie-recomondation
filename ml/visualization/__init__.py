"""
Visualization Module
======================
Generates charts and plots for data analysis and model performance.
Saves all charts to static/images/charts/.
"""

import os
import logging

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Chart style configuration
plt.rcParams.update({
    'figure.facecolor': '#1a1a2e',
    'axes.facecolor': '#16213e',
    'axes.edgecolor': '#e94560',
    'axes.labelcolor': '#eee',
    'text.color': '#eee',
    'xtick.color': '#aaa',
    'ytick.color': '#aaa',
    'grid.color': '#333',
    'font.family': 'sans-serif',
    'font.size': 11,
})


class ChartGenerator:
    """Generates visualization charts for the recommendation system.

    Attributes:
        output_dir: Directory to save chart images.
    """

    def __init__(self, output_dir: str = 'app/static/images/charts') -> None:
        """Initialize chart generator.

        Args:
            output_dir: Output directory for chart images.
        """
        self.output_dir: str = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_all(self, movies_df: pd.DataFrame,
                     ratings_df: pd.DataFrame,
                     eval_results: dict | None = None) -> list[str]:
        """Generate all charts.

        Args:
            movies_df: Movies DataFrame.
            ratings_df: Ratings DataFrame.
            eval_results: Optional evaluation results.

        Returns:
            List of generated chart file paths.
        """
        charts = []
        try:
            charts.append(self.genre_distribution(movies_df))
            charts.append(self.rating_distribution(ratings_df))
            charts.append(self.top_rated_movies(movies_df, ratings_df))
            charts.append(self.most_active_users(ratings_df))
            charts.append(self.movie_timeline(movies_df))

            if eval_results:
                charts.append(self.model_comparison(eval_results))

            logger.info(f"Generated {len(charts)} charts")
        except Exception as e:
            logger.error(f"Chart generation error: {str(e)}")

        return [c for c in charts if c]

    def genre_distribution(self, movies_df: pd.DataFrame) -> str:
        """Generate genre distribution bar chart.

        Args:
            movies_df: Movies DataFrame with 'genres' column.

        Returns:
            Path to saved chart image.
        """
        fig, ax = plt.subplots(figsize=(12, 6))

        # Count genres
        genre_counts: dict[str, int] = {}
        for genres_str in movies_df['genres'].fillna(''):
            if genres_str and genres_str != '(no genres listed)':
                for genre in genres_str.split('|'):
                    genre = genre.strip()
                    genre_counts[genre] = genre_counts.get(genre, 0) + 1

        if not genre_counts:
            plt.close(fig)
            return ''

        sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1],
                               reverse=True)
        genres, counts = zip(*sorted_genres)

        colors = plt.cm.plasma(np.linspace(0.2, 0.8, len(genres)))
        bars = ax.barh(range(len(genres)), counts, color=colors)
        ax.set_yticks(range(len(genres)))
        ax.set_yticklabels(genres, fontsize=9)
        ax.set_xlabel('Number of Movies')
        ax.set_title('Genre Distribution', fontsize=14, fontweight='bold',
                     color='#e94560')
        ax.invert_yaxis()

        for bar, count in zip(bars, counts):
            ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height() / 2,
                    str(count), va='center', fontsize=8, color='#eee')

        plt.tight_layout()
        filepath = os.path.join(self.output_dir, 'genre_distribution.png')
        fig.savefig(filepath, dpi=150, bbox_inches='tight',
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        logger.info(f"Generated genre distribution chart: {filepath}")
        return filepath

    def rating_distribution(self, ratings_df: pd.DataFrame) -> str:
        """Generate rating distribution histogram.

        Args:
            ratings_df: Ratings DataFrame with 'rating' column.

        Returns:
            Path to saved chart image.
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        if len(ratings_df) == 0:
            plt.close(fig)
            return ''

        rating_counts = ratings_df['rating'].value_counts().sort_index()
        colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(rating_counts)))

        ax.bar(rating_counts.index.astype(str), rating_counts.values,
               color=colors, edgecolor='#e94560', linewidth=0.5, width=0.6)
        ax.set_xlabel('Rating')
        ax.set_ylabel('Count')
        ax.set_title('Rating Distribution', fontsize=14, fontweight='bold',
                     color='#e94560')
        ax.yaxis.set_major_formatter(
            ticker.FuncFormatter(lambda x, p: format(int(x), ','))
        )

        plt.tight_layout()
        filepath = os.path.join(self.output_dir, 'rating_distribution.png')
        fig.savefig(filepath, dpi=150, bbox_inches='tight',
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        logger.info(f"Generated rating distribution chart: {filepath}")
        return filepath

    def top_rated_movies(self, movies_df: pd.DataFrame,
                         ratings_df: pd.DataFrame,
                         top_n: int = 15) -> str:
        """Generate top rated movies chart.

        Args:
            movies_df: Movies DataFrame.
            ratings_df: Ratings DataFrame.
            top_n: Number of top movies to show.

        Returns:
            Path to saved chart image.
        """
        fig, ax = plt.subplots(figsize=(12, 7))

        if len(ratings_df) == 0:
            plt.close(fig)
            return ''

        movie_stats = ratings_df.groupby('movieId').agg(
            avg_rating=('rating', 'mean'),
            count=('rating', 'count')
        ).reset_index()

        # Filter movies with at least 10 ratings
        movie_stats = movie_stats[movie_stats['count'] >= 10]
        movie_stats = movie_stats.nlargest(top_n, 'avg_rating')

        # Merge with movie titles
        merged = movie_stats.merge(
            movies_df[['movieId', 'title']], on='movieId', how='left'
        )
        merged['short_title'] = merged['title'].apply(
            lambda x: x[:35] + '...' if len(str(x)) > 35 else x
        )

        colors = plt.cm.magma(np.linspace(0.3, 0.8, len(merged)))
        bars = ax.barh(range(len(merged)), merged['avg_rating'], color=colors)
        ax.set_yticks(range(len(merged)))
        ax.set_yticklabels(merged['short_title'], fontsize=8)
        ax.set_xlabel('Average Rating')
        ax.set_title('Top Rated Movies (min 10 ratings)', fontsize=14,
                     fontweight='bold', color='#e94560')
        ax.set_xlim(0, 5.5)
        ax.invert_yaxis()

        for bar, rating in zip(bars, merged['avg_rating']):
            ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
                    f'{rating:.2f}', va='center', fontsize=8, color='#eee')

        plt.tight_layout()
        filepath = os.path.join(self.output_dir, 'top_rated_movies.png')
        fig.savefig(filepath, dpi=150, bbox_inches='tight',
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        logger.info(f"Generated top rated movies chart: {filepath}")
        return filepath

    def most_active_users(self, ratings_df: pd.DataFrame,
                          top_n: int = 15) -> str:
        """Generate most active users chart.

        Args:
            ratings_df: Ratings DataFrame.
            top_n: Number of users to show.

        Returns:
            Path to saved chart image.
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        if len(ratings_df) == 0:
            plt.close(fig)
            return ''

        user_counts = ratings_df['userId'].value_counts().head(top_n)
        colors = plt.cm.cool(np.linspace(0.2, 0.8, len(user_counts)))

        ax.bar(range(len(user_counts)), user_counts.values, color=colors,
               edgecolor='#e94560', linewidth=0.5)
        ax.set_xticks(range(len(user_counts)))
        ax.set_xticklabels([f'User {uid}' for uid in user_counts.index],
                           rotation=45, ha='right', fontsize=8)
        ax.set_ylabel('Number of Ratings')
        ax.set_title('Most Active Users', fontsize=14, fontweight='bold',
                     color='#e94560')

        plt.tight_layout()
        filepath = os.path.join(self.output_dir, 'most_active_users.png')
        fig.savefig(filepath, dpi=150, bbox_inches='tight',
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        logger.info(f"Generated most active users chart: {filepath}")
        return filepath

    def movie_timeline(self, movies_df: pd.DataFrame) -> str:
        """Generate movie release year timeline.

        Args:
            movies_df: Movies DataFrame with 'year' column.

        Returns:
            Path to saved chart image.
        """
        fig, ax = plt.subplots(figsize=(12, 5))

        year_col = 'year' if 'year' in movies_df.columns else None
        if year_col is None:
            plt.close(fig)
            return ''

        year_counts = movies_df[movies_df[year_col] > 1900][year_col].value_counts().sort_index()

        ax.fill_between(year_counts.index, year_counts.values,
                        alpha=0.3, color='#e94560')
        ax.plot(year_counts.index, year_counts.values,
                color='#e94560', linewidth=2)
        ax.set_xlabel('Year')
        ax.set_ylabel('Number of Movies')
        ax.set_title('Movies Released Per Year', fontsize=14,
                     fontweight='bold', color='#e94560')

        plt.tight_layout()
        filepath = os.path.join(self.output_dir, 'movie_timeline.png')
        fig.savefig(filepath, dpi=150, bbox_inches='tight',
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        logger.info(f"Generated movie timeline chart: {filepath}")
        return filepath

    def model_comparison(self, eval_results: dict) -> str:
        """Generate model comparison chart.

        Args:
            eval_results: Dictionary with model evaluation results.

        Returns:
            Path to saved chart image.
        """
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        models = []
        rmse_values = []
        mae_values = []

        for model_name, metrics in eval_results.items():
            if isinstance(metrics, dict) and 'rmse' in metrics:
                models.append(model_name.upper())
                rmse_values.append(metrics['rmse'])
                mae_values.append(metrics['mae'])

        if not models:
            plt.close(fig)
            return ''

        colors = ['#e94560', '#0f3460', '#533483']

        # RMSE comparison
        bars1 = axes[0].bar(models, rmse_values,
                            color=colors[:len(models)], edgecolor='white',
                            linewidth=0.5)
        axes[0].set_title('RMSE Comparison', fontweight='bold', color='#e94560')
        axes[0].set_ylabel('RMSE (lower is better)')
        for bar, val in zip(bars1, rmse_values):
            axes[0].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                         f'{val:.4f}', ha='center', fontsize=9, color='#eee')

        # MAE comparison
        bars2 = axes[1].bar(models, mae_values,
                            color=colors[:len(models)], edgecolor='white',
                            linewidth=0.5)
        axes[1].set_title('MAE Comparison', fontweight='bold', color='#e94560')
        axes[1].set_ylabel('MAE (lower is better)')
        for bar, val in zip(bars2, mae_values):
            axes[1].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                         f'{val:.4f}', ha='center', fontsize=9, color='#eee')

        plt.tight_layout()
        filepath = os.path.join(self.output_dir, 'model_comparison.png')
        fig.savefig(filepath, dpi=150, bbox_inches='tight',
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        logger.info(f"Generated model comparison chart: {filepath}")
        return filepath

    def recommendation_frequency(self, rec_logs: list[dict]) -> str:
        """Generate recommendation frequency chart.

        Args:
            rec_logs: List of recommendation log dictionaries.

        Returns:
            Path to saved chart image.
        """
        fig, ax = plt.subplots(figsize=(10, 5))

        if not rec_logs:
            plt.close(fig)
            return ''

        df = pd.DataFrame(rec_logs)
        if 'algorithm' in df.columns:
            algo_counts = df['algorithm'].value_counts()
            colors = plt.cm.Set2(np.linspace(0, 1, len(algo_counts)))
            ax.pie(algo_counts.values, labels=algo_counts.index,
                   colors=colors, autopct='%1.1f%%', startangle=90,
                   textprops={'color': '#eee'})
            ax.set_title('Recommendation Algorithm Usage', fontsize=14,
                         fontweight='bold', color='#e94560')

        plt.tight_layout()
        filepath = os.path.join(self.output_dir, 'recommendation_frequency.png')
        fig.savefig(filepath, dpi=150, bbox_inches='tight',
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        logger.info(f"Generated recommendation frequency chart: {filepath}")
        return filepath
