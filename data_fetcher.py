#data_fetcher.py
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from typing import Dict, List, Tuple, Optional
import sqlite3
import logging
from dotenv import load_dotenv
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#APP project
class NFLDataFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_calls = 0
        self.base_url = 'https://v1.american-football.api-sports.io'
        self.headers = {
            'x-rapidapi-host': 'v1.american-football.api-sports.io',
            'x-rapidapi-key': api_key
        }

        # Add database connection
        self.db_path = 'nfl_data.db'
        self.init_db_connection()

        # Initialize team mapping
        self._initialize_team_mapping()

        # Print available team names for debugging
        #print("Available team identifiers:")
        #for key in self.team_mapping.keys():
        #    print(f"- {key}")

    def _initialize_team_mapping(self) -> Dict:
        """Initialize team mapping from API"""
        url = f"{self.base_url}/teams"
        params = {
            'league': '1',
            'season': '2024'
        }

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            teams = response.json()['response']

            # Clear existing mappings
            self.cursor.execute('DELETE FROM team_mapping')

            mapping = {}
            for team in teams:
                team_name = team['name']
                team_id = team['id']

                # Store in database
                self.cursor.execute('''
                    INSERT OR REPLACE INTO team_mapping
                    (team_name, api_id, last_updated)
                    VALUES (?, ?, datetime('now'))
                ''', (team_name, team_id))

                # Add to in-memory mapping
                mapping[team_name.lower()] = {
                    'name': team_name,
                    'id': team_id
                }

            self.conn.commit()
            return mapping

        except Exception as e:
            logger.error(f"Error initializing team mapping: {e}")
            return {}

    def init_db_connection(self):
        """Initialize database connection and tables"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()

            # Create team_mapping table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS team_mapping (
                    team_name TEXT PRIMARY KEY,
                    api_id INTEGER,
                    last_updated TIMESTAMP
                )
            ''')

            # Create team_stats table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS team_stats (
                    game_id INTEGER,
                    team_id INTEGER,
                    stat_name TEXT,
                    stat_value REAL,
                    PRIMARY KEY (game_id, team_id, stat_name)
                )
            ''')

            # Create qb_stats table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS qb_stats (
                    game_id INTEGER,
                    team_id INTEGER,
                    player_id INTEGER,
                    player_name TEXT,
                    stat_name TEXT,
                    stat_value REAL,
                    PRIMARY KEY (game_id, team_id, player_id, stat_name)
                )
            ''')

            self.conn.commit()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")

    def _make_api_call(self, url: str, params: Dict) -> Dict:
        """Centralized API call method with counter"""
        try:
            self.api_calls += 1
            logger.info(f"Making API call #{self.api_calls} to: {url}")
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API call failed: {e}")
            return {}

    def _clean_ratio_stat(self, stat_string: str) -> Tuple[int, int]:
        """Convert stats like '4-13' or '19/24' to tuple of integers"""
        if not stat_string:
            return (0, 0)

        # Handle both dash and forward slash separators
        if '-' in stat_string:
            nums = stat_string.split('-')
        elif '/' in stat_string:
            nums = stat_string.split('/')
        else:
            return (0, 0)

        try:
            return (int(nums[0]), int(nums[1]))
        except (ValueError, IndexError):
            return (0, 0)

    def _convert_time_to_decimal(self, time_str: str) -> float:
        """Convert time string like '29:20' to decimal (29.33)"""
        try:
            minutes, seconds = time_str.split(':')
            return float(minutes) + float(seconds)/60
        except (ValueError, AttributeError):
            return 0.0

    def _clean_team_stats(self, stats: Dict) -> Dict:
        """Clean and process team statistics"""
        if not stats:
            return {}

        # Extract and clean statistics
        third_down = self._clean_ratio_stat(stats['first_downs']['third_down_efficiency'])
        fourth_down = self._clean_ratio_stat(stats['first_downs']['fourth_down_efficiency'])
        comp_att = self._clean_ratio_stat(stats['passing']['comp_att'])
        penalties = self._clean_ratio_stat(stats['penalties']['total'])
        redzone = self._clean_ratio_stat(stats['red_zone']['made_att'])
        sacks = self._clean_ratio_stat(stats['passing']['sacks_yards_lost'])

        cleaned_stats = {
            'first_downs_total': stats['first_downs']['total'],
            'first_downs_passing': stats['first_downs']['passing'],
            'first_downs_rushing': stats['first_downs']['rushing'],
            'first_downs_penalties': stats['first_downs']['from_penalties'],
            'third_down_attempts': third_down[1],
            'third_down_conversions': third_down[0],
            'third_down_pct': round(third_down[0] / third_down[1] * 100 if third_down[1] else 0, 2),
            'fourth_down_attempts': fourth_down[1],
            'fourth_down_conversions': fourth_down[0],
            'fourth_down_pct': round(fourth_down[0] / fourth_down[1] * 100 if fourth_down[1] else 0, 2),
            'total_plays': stats['plays']['total'],
            'total_yards': stats['yards']['total'],
            'yards_per_play': float(stats['yards']['yards_per_play']),
            'passing_yards': stats['passing']['total'],
            'passing_attempts': comp_att[1],
            'passing_completions': comp_att[0],
            'completion_pct': round(comp_att[0] / comp_att[1] * 100 if comp_att[1] else 0, 2),
            'yards_per_pass': float(stats['passing']['yards_per_pass']),
            'sacks': sacks[0],
            'sacks_yards_lost': sacks[1],
            'rushing_yards': stats['rushings']['total'],
            'rushing_attempts': stats['rushings']['attempts'],
            'yards_per_rush': float(stats['rushings']['yards_per_rush']),
            'redzone_attempts': redzone[1],
            'redzone_scores': redzone[0],
            'redzone_pct': round(redzone[0] / redzone[1] * 100 if redzone[1] else 0, 2),
            'penalties': penalties[0],
            'penalty_yards': penalties[1],
            'turnovers': stats['turnovers']['total'],
            'possession_time': self._convert_time_to_decimal(stats['posession']['total']),
            'points_against': stats['points_against']['total']
        }

        print(f"Raw stats received: {json.dumps(stats, indent=2)}")
        print(f"Cleaned stats: {json.dumps(cleaned_stats, indent=2)}")

        return cleaned_stats

    def verify_team_mapping(self):
        """Verify team mapping exists and reinitialize if needed"""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM team_mapping")
            count = self.cursor.fetchone()[0]
            if count == 0:
                print("Team mapping empty, initializing...")
                self._initialize_team_mapping()
        except Exception as e:
            print(f"Error verifying team mapping: {e}")
            self._initialize_team_mapping()

    #def get_team_info(self, team_identifier: str) -> Dict:
        #"""Get team info from code or name"""
       # team_identifier = team_identifier.lower()

        # Print debugging info
        #print(f"\nLooking for team: {team_identifier}")
        #print("Available matches:", [k for k in self.team_mapping.keys() if team_identifier in k])

        #return self.team_mapping.get(team_identifier)

    def get_team_info(self, team_name: str) -> Dict:
        """Get team info from database"""
        try:
            self.cursor.execute('''
                SELECT team_name, api_id
                FROM team_mapping
                WHERE team_name = ?
            ''', (team_name,))

            result = self.cursor.fetchone()
            if result:
                return {
                    'name': result[0],
                    'id': result[1]
                }

            # If team not found, try to get it from API and cache it
            return self._initialize_team_mapping().get(team_name.lower())
        except Exception as e:
            logger.error(f"Error getting team info: {e}")
            return None

    def get_recent_games(self, team_id: int, limit: int = 3) -> List[int]:
        """Get the most recent games for a team"""
        url = f"{self.base_url}/games"
        params = {
            'league': '1',
            'season': '2024',
            'team': team_id
        }

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            games = response.json()['response']

            # Filter completed games and sort by date
            completed_games = [
                game for game in games
                if game['game']['status']['short'] == 'FT'
            ]
            completed_games.sort(
                key=lambda x: datetime.strptime(x['game']['date']['date'], '%Y-%m-%d'),
                reverse=True
            )

            return [game['game']['id'] for game in completed_games[:limit]]

        except Exception as e:
            print(f"Error fetching games: {e}")
            return []

    def get_game_stats(self, game_id: int) -> Dict:
        """Get statistics for a specific game"""
        url = f"{self.base_url}/games/statistics/teams"
        params = {'id': str(game_id)}

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()['response']
        except Exception as e:
            print(f"Error fetching game stats: {e}")
            return {}

    def get_team_recent_stats(self, team_identifier: str, num_games: int = 3) -> pd.DataFrame:
        """Get recent stats from cache or API"""
        team_info = self.get_team_info(team_identifier)
        if not team_info:
            raise ValueError(f"Team not found: {team_identifier}")

        try:
            # Check cache first
            self.cursor.execute('''
                SELECT DISTINCT game_id, stat_name, stat_value
                FROM team_stats
                WHERE team_id = ?
                ORDER BY game_id DESC
                LIMIT ?
            ''', (team_info['id'], num_games * 32))  # 32 stats per game
            cached_stats = self.cursor.fetchall()

            # If cache has enough data, use it
            if cached_stats:
                stats_list = []
                current_game_id = None
                game_stats = {}

                for game_id, stat_name, stat_value in cached_stats:
                    if current_game_id != game_id:
                        if current_game_id is not None:
                            stats_list.append(game_stats)
                        current_game_id = game_id
                        game_stats = {'game_id': game_id}
                    game_stats[stat_name] = stat_value

                if game_stats:  # Add the last game
                    stats_list.append(game_stats)

                if len(stats_list) >= num_games:
                    return pd.DataFrame(stats_list)

            # If cache miss or insufficient data, fetch from API
            return self._fetch_and_cache_team_stats(team_info['id'], num_games)

        except Exception as e:
            print(f"Cache access error: {e}")
            # If there's any error with the cache, fallback to API
            return self._fetch_and_cache_team_stats(team_info['id'], num_games)

    def get_future_game_id(self, team1: str, team2: str) -> Optional[int]:
        """Find the next game ID between two teams"""
        # Get next 7 days of games
        for i in range(7):
            date = (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
            url = f"{self.base_url}/games"
            params = {
                'league': '1',
                'season': '2024',
                'date': date
            }

            try:
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                games = response.json()['response']

                for game in games:
                    home_team = game['teams']['home']['name'].lower()
                    away_team = game['teams']['away']['name'].lower()

                    if (team1.lower() in [home_team, away_team] and
                        team2.lower() in [home_team, away_team]):
                        return game['game']['id']
            except Exception as e:
                print(f"Error fetching games for date {date}: {e}")

        return None

    def get_odds(self, game_id: int) -> Dict:
        """Get odds for a specific game"""
        url = f"{self.base_url}/odds"
        params = {
            'game': str(game_id),
            'bookmaker': '18'  # Dafabet
        }

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            odds_data = response.json()['response'][0]
            return odds_data
        except Exception as e:
            print(f"Error fetching odds: {e}")
            return {}

    def _clean_qb_stats(self, stats: List[Dict]) -> Dict:
        """Clean and process quarterback statistics"""
        if not stats:
            return {}

        cleaned_stats = {}
        for stat in stats:
            name = stat['name']
            value = stat['value']

            if name == 'comp att':
                comp, att = self._clean_ratio_stat(value)
                cleaned_stats['completions'] = comp
                cleaned_stats['attempts'] = att
                cleaned_stats['completion_pct'] = round((comp / att * 100) if att else 0, 2)
            elif name == 'sacks':
                sacks, yards = self._clean_ratio_stat(value)
                cleaned_stats['sacks'] = sacks
                cleaned_stats['sack_yards'] = yards
            else:
                # Convert string values to appropriate types
                try:
                    if name in ['yards', 'passing touch downs', 'interceptions', 'two pt']:
                        cleaned_stats[name.replace(' ', '_')] = int(value)
                    elif name == 'average':
                        cleaned_stats['yards_per_attempt'] = float(value)
                    elif name == 'rating':
                        cleaned_stats['passer_rating'] = float(value)
                except (ValueError, TypeError):
                    cleaned_stats[name.replace(' ', '_')] = value

        return cleaned_stats

    def get_qb_stats(self, game_id: int) -> Dict:
        """Get quarterback statistics for a specific game"""
        url = f"{self.base_url}/games/statistics/players"
        params = {
            'id': str(game_id),
            'group': 'Passing'
        }

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()['response']

            qb_stats = {}
            for team_data in data:
                team_name = team_data['team']['name']
                if team_data['groups'] and team_data['groups'][0]['players']:
                    qb = team_data['groups'][0]['players'][0]  # Get primary QB
                    qb_stats[team_name] = {
                        'player_name': qb['player']['name'],
                        'player_id': qb['player']['id'],
                        **self._clean_qb_stats(qb['statistics'])
                    }

            return qb_stats
        except Exception as e:
            print(f"Error fetching QB stats: {e}")
            return {}

    # data_fetcher
    def analyze_matchup(self, team1: str, team2: str) -> Dict:
        # Get team stats
        team1_stats = self.get_team_recent_stats(team1)
        team2_stats = self.get_team_recent_stats(team2)

        # Get QB stats
        team1_qb_stats = self.get_team_recent_qb_stats(team1)
        team2_qb_stats = self.get_team_recent_qb_stats(team2)

        # Debug prints
        print("\nTeam Stats Columns:")
        print(f"Team 1: {team1_stats.columns.tolist()}")
        print(f"Team 2: {team2_stats.columns.tolist()}")
        print("\nQB Stats Columns:")
        print(f"Team 1 QB: {team1_qb_stats.columns.tolist()}")
        print(f"Team 2 QB: {team2_qb_stats.columns.tolist()}")

        if team1_stats.empty or team2_stats.empty:
            return {"error": "Could not fetch stats for one or both teams"}

        # Calculate averages
        team1_avg = team1_stats.mean()
        team2_avg = team2_stats.mean()

        # Specify numeric columns for QB stats
        numeric_columns = [
            'completions', 'attempts', 'completion_pct',
            'yards', 'yards_per_attempt', 'passing_touch_downs',
            'interceptions', 'sacks', 'sack_yards', 'passer_rating'
        ]

        # Calculate QB averages only for numeric columns
        team1_qb_avg = team1_qb_stats[numeric_columns].mean() if not team1_qb_stats.empty else pd.Series()
        team2_qb_avg = team2_qb_stats[numeric_columns].mean() if not team2_qb_stats.empty else pd.Series()

        # Get the most recent QB name for each team
        team1_qb_name = team1_qb_stats['player_name'].iloc[-1] if not team1_qb_stats.empty else "Unknown"
        team2_qb_name = team2_qb_stats['player_name'].iloc[-1] if not team2_qb_stats.empty else "Unknown"

        analysis = {
            'team_stats': {
                team1.upper(): dict(team1_avg),
                team2.upper(): dict(team2_avg)
            },
            'qb_stats': {
                team1.upper(): {
                    'name': team1_qb_name,
                    **dict(team1_qb_avg)
                } if not team1_qb_stats.empty else {},
                team2.upper(): {
                    'name': team2_qb_name,
                    **dict(team2_qb_avg)
                } if not team2_qb_stats.empty else {}
            },
            'advantages': {
                team1.upper(): [],
                team2.upper(): []
            }
        }

        # Offensive metrics
        offensive_metrics = {
            'yards_per_play': ('Yards per Play', 0.5),
            'third_down_pct': ('Third Down %', 5),
            'redzone_pct': ('Red Zone %', 10),
            'possession_time': ('Time of Possession', 2),
            'yards_per_pass': ('Yards per Pass', 0.5),
            'yards_per_rush': ('Yards per Rush', 0.3)
        }

        # Defensive metrics
        defensive_metrics = {
            'sacks': ('Sacks', 1),
            'turnovers': ('Turnovers Forced', 0.5),
            'interceptions': ('Interceptions', 0.5),
            'fumbles_recovered': ('Fumbles Recovered', 0.5),
            'points_against': ('Points Allowed', 3)
        }

        # QB metrics
        qb_metrics = {
            'completion_pct': ('Completion %', 5),
            'yards_per_attempt': ('Yards per Attempt', 0.5),
            'passer_rating': ('Passer Rating', 10)
        }

        # Analyze offensive metrics
        for metric, (display_name, threshold) in offensive_metrics.items():
            if metric in team1_avg and metric in team2_avg:
                value1 = team1_avg[metric]
                value2 = team2_avg[metric]
                diff = value1 - value2

                if abs(diff) > threshold:
                    if diff > 0:
                        analysis['advantages'][team1.upper()].append(
                            f"Better {display_name}: {value1:.1f} vs {value2:.1f}"
                        )
                    else:
                        analysis['advantages'][team2.upper()].append(
                            f"Better {display_name}: {value2:.1f} vs {value1:.1f}"
                        )

        # Analyze defensive metrics
        for metric, (display_name, threshold) in defensive_metrics.items():
            if metric in team1_avg and metric in team2_avg:
                value1 = team1_avg[metric]
                value2 = team2_avg[metric]
                # For points against and turnovers allowed, lower is better
                if metric in ['points_against']:
                    diff = value2 - value1
                else:
                    diff = value1 - value2

                if abs(diff) > threshold:
                    if diff > 0:
                        analysis['advantages'][team1.upper()].append(
                            f"Better Defense - {display_name}: {value1:.1f} vs {value2:.1f}"
                        )
                    else:
                        analysis['advantages'][team2.upper()].append(
                            f"Better Defense - {display_name}: {value2:.1f} vs {value1:.1f}"
                        )

        # Analyze QB metrics
        if not team1_qb_stats.empty and not team2_qb_stats.empty:
            for metric, (display_name, threshold) in qb_metrics.items():
                if metric in team1_qb_avg and metric in team2_qb_avg:
                    value1 = team1_qb_avg[metric]
                    value2 = team2_qb_avg[metric]
                    diff = value1 - value2

                    if abs(diff) > threshold:
                        if diff > 0:
                            analysis['advantages'][team1.upper()].append(
                                f"QB Better {display_name}: {value1:.1f} vs {value2:.1f}"
                            )
                        else:
                            analysis['advantages'][team2.upper()].append(
                                f"QB Better {display_name}: {value2:.1f} vs {value1:.1f}"
                            )

        return analysis

    def _get_cached_team_mapping(self) -> Dict:
        """Get team mapping from cache or API"""
        self.cursor.execute('''
            SELECT team_identifier, team_id, team_name, last_updated
            FROM team_mapping
        ''')
        cached_data = self.cursor.fetchall()

        # If cache is empty or old (>24 hours), fetch from API
        if not cached_data or (datetime.now() - cached_data[0][3]).days >= 1:
            mapping = self._initialize_team_mapping()
            self._cache_team_mapping(mapping)
            return mapping

        # Convert cached data to dictionary
        mapping = {}
        for identifier, team_id, name, _ in cached_data:
            mapping[identifier] = {
                'id': team_id,
                'name': name
            }
        return mapping

    def _cache_team_mapping(self, mapping: Dict):
        """Cache team mapping to database"""
        now = datetime.now()
        self.cursor.executemany('''
            INSERT OR REPLACE INTO team_mapping
            (team_identifier, team_id, team_name, last_updated)
            VALUES (?, ?, ?, ?)
        ''', [(k, v['id'], v['name'], now) for k, v in mapping.items()])
        self.conn.commit()

    def _fetch_and_cache_team_stats(self, team_id: int, num_games: int) -> pd.DataFrame:
        """Fetch team stats from API and cache them"""
        recent_game_ids = self.get_recent_games(team_id, num_games)
        stats_list = []

        try:
            for game_id in recent_game_ids:
                # Check if this game is already in cache
                self.cursor.execute('''
                    SELECT COUNT(*) FROM team_stats
                    WHERE game_id = ? AND team_id = ?
                ''', (game_id, team_id))

                if self.cursor.fetchone()[0] > 0:
                    # Game exists in cache, fetch it
                    self.cursor.execute('''
                        SELECT stat_name, stat_value
                        FROM team_stats
                        WHERE game_id = ? AND team_id = ?
                    ''', (game_id, team_id))

                    game_stats = {'game_id': game_id}
                    for stat_name, stat_value in self.cursor.fetchall():
                        game_stats[stat_name] = stat_value
                    stats_list.append(game_stats)
                    continue

                # If not in cache, fetch from API
                game_stats = self.get_game_stats(game_id)
                if not game_stats:
                    continue

                team_stats = next(
                    (stats for stats in game_stats
                    if stats['team']['id'] == team_id),
                    None
                )

                if team_stats:
                    cleaned_stats = self._clean_team_stats(team_stats['statistics'])
                    cleaned_stats['game_id'] = game_id
                    stats_list.append(cleaned_stats)

                    # Cache each stat
                    for stat_name, stat_value in cleaned_stats.items():
                        self.cursor.execute('''
                            INSERT OR REPLACE INTO team_stats
                            (game_id, team_id, stat_name, stat_value)
                            VALUES (?, ?, ?, ?)
                        ''', (game_id, team_id, stat_name, float(stat_value)))

            self.conn.commit()
            return pd.DataFrame(stats_list)

        except Exception as e:
            print(f"Error fetching/caching stats: {e}")
            self.conn.rollback()
            return pd.DataFrame()

    def get_team_recent_qb_stats(self, team_identifier: str, num_games: int = 3) -> pd.DataFrame:
        """Get QB stats from cache or API"""
        team_info = self.get_team_info(team_identifier)
        if not team_info:
            raise ValueError(f"Team not found: {team_identifier}")

        try:
            # Check cache first
            self.cursor.execute('''
                SELECT DISTINCT game_id, player_id, player_name, stat_name, stat_value
                FROM qb_stats
                WHERE team_id = ?
                ORDER BY game_id DESC
                LIMIT ?
            ''', (team_info['id'], num_games))
            cached_stats = self.cursor.fetchall()

            # If cache is empty, fetch from API
            if not cached_stats:
                return self._fetch_and_cache_qb_stats(team_info, num_games)

            # Convert cached data to DataFrame
            stats_list = []
            current_game_id = None
            game_stats = {}

            for game_id, player_id, player_name, stat_name, stat_value in cached_stats:
                if current_game_id != game_id:
                    if current_game_id is not None:
                        stats_list.append(game_stats)
                    current_game_id = game_id
                    game_stats = {
                        'game_id': game_id,
                        'player_id': player_id,
                        'player_name': player_name
                    }
                game_stats[stat_name] = stat_value

            if game_stats:
                stats_list.append(game_stats)

            return pd.DataFrame(stats_list)

        except Exception as e:
            print(f"Cache access error: {e}")
            # If there's any error with the cache, fallback to API
            return self._fetch_and_cache_qb_stats(team_info, num_games)

    def _fetch_and_cache_qb_stats(self, team_info: Dict, num_games: int) -> pd.DataFrame:
        """Fetch QB stats from API and cache them"""
        recent_game_ids = self.get_recent_games(team_info['id'], num_games)
        qb_stats_list = []

        try:
            # Clear existing cached data for this team
            self.cursor.execute('''
                DELETE FROM qb_stats
                WHERE team_id = ?
            ''', (team_info['id'],))

            for game_id in recent_game_ids:
                game_qb_stats = self.get_qb_stats(game_id)
                if game_qb_stats.get(team_info['name']):
                    stats = game_qb_stats[team_info['name']]
                    stats['game_id'] = game_id
                    qb_stats_list.append(stats)

                    # Cache each stat
                    for stat_name, stat_value in stats.items():
                        if stat_name not in ['player_name', 'player_id', 'game_id']:
                            self.cursor.execute('''
                                INSERT OR REPLACE INTO qb_stats
                                (game_id, team_id, player_id, player_name, stat_name, stat_value)
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (
                                game_id,
                                team_info['id'],
                                stats['player_id'],
                                stats['player_name'],
                                stat_name,
                                stat_value
                            ))

            self.conn.commit()
            return pd.DataFrame(qb_stats_list)

        except Exception as e:
            print(f"Error fetching/caching QB stats: {e}")
            self.conn.rollback()
            return pd.DataFrame()