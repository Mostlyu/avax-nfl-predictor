#predictor.py
import pandas as pd
from data_fetcher import NFLDataFetcher
import requests
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('predictor')

class NFLPredictor(NFLDataFetcher):
    def __init__(self, api_key: str):
        # Call parent class initialization first
        super().__init__(api_key)

        # Set up bookmakers and key numbers
        self.BOOKMAKERS = range(2, 19)
        self.KEY_NUMBERS = {
            'spread': {
                'primary': [3, 7],
                'secondary': [4, 6, 10, 14],
                'margin': 0.5
            },
            'totals': {
                'primary': [41, 44, 47, 51],
                'secondary': [37, 40, 43, 46, 50],
                'margin': 0.5
            }
        }

        # Initialize database tables
        self._init_odds_tables()
        self._init_prediction_tables()

    def _init_prediction_tables(self):
        """Initialize prediction-related tables"""
        try:
            if not hasattr(self, 'cursor'):
                self.init_db_connection()

            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS game_predictions_cache (
                    game_id INTEGER PRIMARY KEY,
                    prediction_data TEXT,
                    game_data TEXT,
                    last_updated TIMESTAMP,
                    expiry TIMESTAMP
                )
            ''')
            self.conn.commit()
            logger.info("Created game_predictions_cache table")
        except Exception as e:
            logger.error(f"Error creating prediction tables: {e}")

    def _init_odds_tables(self):
        """Initialize odds-related tables"""
        try:
            if not hasattr(self, 'cursor'):
                self.init_db_connection()

            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_odds (
                    game_id INTEGER,
                    bookmaker_id INTEGER,
                    bet_type TEXT,
                    bet_value TEXT,
                    odds REAL,
                    last_updated TIMESTAMP,
                    PRIMARY KEY (game_id, bookmaker_id, bet_type, bet_value)
                )
            ''')

            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS consensus_lines (
                    game_id INTEGER,
                    line_type TEXT,
                    consensus_value TEXT,
                    avg_odds REAL,
                    book_count INTEGER,
                    last_updated TIMESTAMP,
                    PRIMARY KEY (game_id, line_type)
                )
            ''')
            self.conn.commit()
        except Exception as e:
            print(f"Error initializing odds tables: {e}")

    def analyze_matchup(self, team1: str, team2: str) -> Dict:
        """Analyze matchup between two teams including QB performance and defensive metrics"""
        try:
            # Get team stats
            team1_stats = self.get_team_recent_stats(team1)
            team2_stats = self.get_team_recent_stats(team2)

            if team1_stats.empty or team2_stats.empty:
                return {"error": "Could not fetch stats for one or both teams"}

            # Calculate averages
            team1_avg = team1_stats.mean()
            team2_avg = team2_stats.mean()

            # Make sure we include all needed metrics
            analysis = {
                'team_stats': {
                    team1.upper(): dict(team1_avg),
                    team2.upper(): dict(team2_avg)
                },
                'advantages': {
                    team1.upper(): [],
                    team2.upper(): []
                },
                'home_team': team1.upper(),
                'away_team': team2.upper()
            }

            print("\nAvailable Stats:")
            print(f"{team1} stats columns:", team1_stats.columns.tolist())
            print(f"{team2} stats columns:", team2_stats.columns.tolist())
            print(f"\n{team1} stats:\n", team1_stats.mean())
            print(f"\n{team2} stats:\n", team2_stats.mean())

            # Get QB stats
            team1_qb_stats = self.get_team_recent_qb_stats(team1)
            team2_qb_stats = self.get_team_recent_qb_stats(team2)

            if team1_stats.empty or team2_stats.empty:
                return {"error": "Could not fetch stats for one or both teams"}

            # Calculate averages
            team1_avg = team1_stats.mean()
            team2_avg = team2_stats.mean()

            analysis = {
                'team_stats': {
                    team1.upper(): dict(team1_avg),
                    team2.upper(): dict(team2_avg)
                },
                'advantages': {
                    team1.upper(): [],
                    team2.upper(): []
                }
            }

            # Define all metrics we want to compare
            metrics_to_check = {
                'yards_per_play': ('Yards per Play', 0.5),
                'third_down_pct': ('Third Down %', 5),
                'redzone_pct': ('Red Zone %', 10),
                'possession_time': ('Time of Possession', 2),
                'yards_per_pass': ('Yards per Pass', 0.5),
                'yards_per_rush': ('Yards per Rush', 0.3),
                'points_against': ('Defense - Points Allowed', 3, True),
                'sacks': ('Defense - Sacks', 1),
                'turnovers': ('Defense - Turnovers Forced', 0.5)
            }

            # Check each metric
            for metric, (display_name, threshold, *args) in metrics_to_check.items():
                if metric in team1_avg.index and metric in team2_avg.index:
                    try:
                        value1 = float(team1_avg[metric])
                        value2 = float(team2_avg[metric])
                        lower_is_better = len(args) > 0 and args[0]

                        diff = value2 - value1 if lower_is_better else value1 - value2

                        if abs(diff) > threshold:
                            if diff > 0:
                                analysis['advantages'][team1.upper()].append(
                                    f"Better {display_name}: {value1:.1f} vs {value2:.1f}"
                                )
                            else:
                                analysis['advantages'][team2.upper()].append(
                                    f"Better {display_name}: {value2:.1f} vs {value1:.1f}"
                                )
                    except (ValueError, TypeError) as e:
                        print(f"Error processing {metric}: {e}")
                        continue

            # QB Analysis
            if not team1_qb_stats.empty and not team2_qb_stats.empty:
                qb_metrics = {
                    'completion_pct': ('QB Completion %', 5),
                    'yards_per_attempt': ('QB Yards per Attempt', 0.5),
                    'passer_rating': ('QB Passer Rating', 10)
                }

                for metric, (display_name, threshold) in qb_metrics.items():
                    try:
                        if metric in team1_qb_stats.columns and metric in team2_qb_stats.columns:
                            value1 = float(team1_qb_stats[metric].mean())
                            value2 = float(team2_qb_stats[metric].mean())
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
                    except Exception as e:
                        print(f"Error processing QB stat {metric}: {e}")
                        continue

            print("\nFinal Analysis:")
            print(json.dumps(analysis, indent=2))

            if 'home_team' not in analysis:
                analysis['home_team'] = team1.upper()
                analysis['away_team'] = team2.upper()

            return analysis

        except Exception as e:
            print(f"Error in analyze_matchup: {str(e)}")
            return {"error": f"Analysis error: {str(e)}"}

    def get_future_game(self, team1: str = "", team2: str = "") -> Dict:
        """Find upcoming games. If team1 and team2 are provided, finds specific matchup."""
        for i in range(14):  # Look ahead 14 days
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

                # If no specific teams provided, return all games for the date
                if not team1 and not team2:
                    return games

                # Otherwise, find specific matchup
                for game in games:
                    home_team = game['teams']['home']['name'].lower()
                    away_team = game['teams']['away']['name'].lower()

                    team1_lower = team1.lower()
                    team2_lower = team2.lower()

                    if ((team1_lower in home_team and team2_lower in away_team) or
                        (team2_lower in home_team and team1_lower in away_team)):
                        return game

            except Exception as e:
                print(f"Error fetching games for date {date}: {e}")
                continue

        return None

    # In NFLPredictor class
    def get_game_odds(self, game_id: int) -> Dict:
        """Get betting odds from cache or API"""
        try:
            # Check cache first
            self.cursor.execute('''
                SELECT bet_type, bet_value, odds
                FROM market_odds
                WHERE game_id = ? AND bookmaker_id = 18
            ''', (game_id,))
            cached_odds = self.cursor.fetchall()

            if cached_odds:
                processed_odds = {
                    'spread': {},
                    'total': {},
                    'moneyline': {}
                }
                for bet_type, bet_value, odds in cached_odds:
                    processed_odds[bet_type][bet_value] = odds
                return processed_odds

            # If not in cache, fetch from API
            url = f"{self.base_url}/odds"
            params = {
                'game': str(game_id),
                'bookmaker': '18'  # Dafabet
            }

            try:
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()['response']

                if not data or not data[0].get('bookmakers'):
                    logger.info("No odds data available")
                    return {'spread': {}, 'total': {}, 'moneyline': {}}

                odds_data = data[0]
                processed_odds = {
                    'spread': {},
                    'total': {},
                    'moneyline': {}
                }

                for bet in odds_data['bookmakers'][0]['bets']:
                    try:
                        if bet['name'] == 'Asian Handicap':
                            for value in bet['values']:
                                try:
                                    points = float(value['value'].split()[1])
                                    if abs(points) <= 14:  # Filter unreasonable spreads
                                        side = value['value'].split()[0]  # Home or Away
                                        # Add explicit + sign for underdogs, - for favorites
                                        sign = '+' if points >= 0 else '-'
                                        spread_value = f"{side} {sign}{abs(points)}"
                                        processed_odds['spread'][spread_value] = float(value['odd'])
                                except (ValueError, IndexError):
                                    continue

                        elif bet['name'] == 'Over/Under':
                            for value in bet['values']:
                                try:
                                    points = float(value['value'].split()[1])
                                    if 35 <= points <= 55:  # Filter reasonable totals only
                                        processed_odds['total'][value['value']] = float(value['odd'])
                                except (ValueError, IndexError):
                                    continue

                    except Exception as e:
                        logger.error(f"Error processing bet type {bet['name']}: {e}")
                        continue

                # Cache the processed odds
                if any(processed_odds.values()):
                    for bet_type, bets in processed_odds.items():
                        for bet_value, odd in bets.items():
                            self.cursor.execute('''
                                INSERT OR REPLACE INTO market_odds
                                (game_id, bookmaker_id, bet_type, bet_value, odds, last_updated)
                                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                            ''', (game_id, 18, bet_type, bet_value, odd))
                    self.conn.commit()

                return processed_odds

            except Exception as e:
                logger.error(f"Error fetching odds: {e}")
                return {'spread': {}, 'total': {}, 'moneyline': {}}

        except Exception as e:
            logger.error(f"Error accessing odds cache: {e}")
            return {'spread': {}, 'total': {}, 'moneyline': {}}

    def _cache_odds(self, game_id: int, bookmaker_id: int, processed_odds: Dict):
        """Helper method to cache processed odds"""
        try:
            for bet_type, bets in processed_odds.items():
                for bet_value, odd in bets.items():
                    self.cursor.execute('''
                        INSERT OR REPLACE INTO market_odds
                        (game_id, bookmaker_id, bet_type, bet_value, odds, last_updated)
                        VALUES (?, ?, ?, ?, ?, datetime('now'))
                    ''', (game_id, bookmaker_id, bet_type, bet_value, odd))
            self.conn.commit()
        except Exception as e:
            print(f"Error caching odds: {e}")

    # In NFLPredictor class
    def get_market_data(self, game_id: int) -> Dict:
        """Get market data from cache or API"""
        market_data = {
            'spread': {},
            'total': {},
            'consensus': {
                'spread': None,
                'total': None
            },
            'line_movement': {
                'spread': [],
                'total': []
            },
            'key_number_alerts': []
        }

        try:
            # Check consensus cache first
            self.cursor.execute('''
                SELECT line_type, consensus_value, avg_odds, book_count
                FROM consensus_lines
                WHERE game_id = ?
            ''', (game_id,))
            cached_consensus = self.cursor.fetchall()

            if cached_consensus:
                for line_type, value, avg_odds, count in cached_consensus:
                    if value:  # If we have a consensus value
                        market_data['consensus'][line_type] = value
                        market_data['consensus'][f'{line_type}_odds'] = {
                            'avg_odd': avg_odds,
                            'count': count
                        }
            else:
                # If not in cache, fetch from all bookmakers and cache
                for bookmaker in self.BOOKMAKERS:
                    try:
                        odds = self.get_odds_for_bookmaker(game_id, bookmaker)
                        if odds:
                            self._process_bookmaker_odds(odds, market_data)
                    except Exception as e:
                        continue

                # Calculate and cache consensus
                consensus = self._calculate_consensus(market_data)
                market_data['consensus'] = consensus

                # Cache consensus lines
                for line_type in ['spread', 'total']:
                    if consensus.get(line_type):
                        self.cursor.execute('''
                            INSERT OR REPLACE INTO consensus_lines
                            (game_id, line_type, consensus_value, avg_odds, book_count)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (
                            game_id,
                            line_type,
                            consensus[line_type],
                            consensus[f'{line_type}_odds']['avg_odd'],
                            consensus[f'{line_type}_odds']['count']
                        ))
                self.conn.commit()

            # Add key number analysis
            market_data['key_number_alerts'] = self._analyze_key_numbers(market_data['consensus'])
            return market_data

        except Exception as e:
            print(f"Error processing market data: {e}")
            return market_data

    def _fetch_and_cache_market_data(self, game_id: int) -> Dict:
        """Fetch market data from all bookmakers and cache it"""
        market_data = {
            'spread': {},
            'total': {},
            'consensus': {
                'spread': None,
                'total': None
            }
        }
        now = datetime.now()

        for bookmaker in self.BOOKMAKERS:
            try:
                odds = self.get_odds_for_bookmaker(game_id, bookmaker)
                if odds:
                    self._process_and_cache_odds(game_id, bookmaker, odds, now)
                    self._process_bookmaker_odds(odds, market_data)
            except Exception as e:
                continue

        # Calculate and cache consensus
        consensus = self._calculate_consensus(market_data)

        # Cache consensus lines
        for line_type in ['spread', 'total']:
            if consensus.get(line_type):
                self.cursor.execute('''
                    INSERT OR REPLACE INTO consensus_lines
                    (game_id, line_type, consensus_value, avg_odds, book_count, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    game_id, line_type, consensus[line_type],
                    consensus[f'{line_type}_odds']['avg_odd'],
                    consensus[f'{line_type}_odds']['count'],
                    now
                ))

        self.conn.commit()
        market_data['consensus'] = consensus
        market_data['key_number_alerts'] = self._analyze_key_numbers(consensus)
        return market_data

    def _process_and_cache_odds(self, game_id: int, bookmaker_id: int, odds_data: Dict, timestamp):
        """Process and cache odds from a bookmaker"""
        for bet in odds_data['bookmakers'][0]['bets']:
            bet_type = 'spread' if bet['name'] == 'Asian Handicap' else \
                      'total' if bet['name'] == 'Over/Under' else 'moneyline'

            for value in bet['values']:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO market_odds
                    (game_id, bookmaker_id, bet_type, bet_value, odds, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    game_id, bookmaker_id, bet_type,
                    value['value'], float(value['odd']), timestamp
                ))

    def get_odds_for_bookmaker(self, game_id: int, bookmaker: int) -> Dict:
        """Get odds from a specific bookmaker"""
        url = f"{self.base_url}/odds"
        params = {
            'game': str(game_id),
            'bookmaker': str(bookmaker)
        }

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()['response'][0]
        except Exception as e:
            return None

    def _process_bookmaker_odds(self, odds_data: Dict, market_data: Dict):
        """Process odds from each bookmaker"""
        bookmaker_name = odds_data['bookmakers'][0]['name']

        for bet in odds_data['bookmakers'][0]['bets']:
            if bet['name'] == 'Asian Handicap':
                # Process spread odds
                for value in bet['values']:
                    spread = value['value']
                    odd = float(value['odd'])
                    if spread not in market_data['spread']:
                        market_data['spread'][spread] = []
                    market_data['spread'][spread].append({
                        'bookmaker': bookmaker_name,
                        'odd': odd
                    })

            elif bet['name'] == 'Over/Under':
                # Process total odds
                for value in bet['values']:
                    total = value['value']
                    odd = float(value['odd'])
                    if total not in market_data['total']:
                        market_data['total'][total] = []
                    market_data['total'][total].append({
                        'bookmaker': bookmaker_name,
                        'odd': odd
                    })

    def _calculate_consensus(self, market_data: Dict) -> Dict:
        """Calculate market consensus lines"""
        consensus = {
            'spread': None,
            'total': None,
            'spread_odds': [],
            'total_odds': []
        }

        # Calculate spread consensus
        if market_data['spread']:
            spreads = {}
            for spread, books in market_data['spread'].items():
                avg_odd = sum(b['odd'] for b in books) / len(books)
                spreads[spread] = {
                    'count': len(books),
                    'avg_odd': avg_odd
                }

            # Find most common spread
            max_count = max(v['count'] for v in spreads.values())
            consensus_spreads = [k for k, v in spreads.items() if v['count'] == max_count]
            if consensus_spreads:
                consensus['spread'] = consensus_spreads[0]
                consensus['spread_odds'] = spreads[consensus_spreads[0]]

        # Calculate total consensus similarly
        if market_data['total']:
            totals = {}
            for total, books in market_data['total'].items():
                avg_odd = sum(b['odd'] for b in books) / len(books)
                totals[total] = {
                    'count': len(books),
                    'avg_odd': avg_odd
                }

            max_count = max(v['count'] for v in totals.values())
            consensus_totals = [k for k, v in totals.items() if v['count'] == max_count]
            if consensus_totals:
                consensus['total'] = consensus_totals[0]
                consensus['total_odds'] = totals[consensus_totals[0]]

        return consensus

    def _analyze_key_numbers(self, consensus: Dict) -> List[str]:
        """Analyze if lines are near key numbers"""
        alerts = []

        if consensus['spread']:
            spread_value = abs(float(consensus['spread'].split()[1]))

            # Check primary key numbers
            for key in self.KEY_NUMBERS['spread']['primary']:
                if abs(spread_value - key) <= self.KEY_NUMBERS['spread']['margin']:
                    alerts.append(f"Spread {spread_value} is near key number {key}")

            # Check secondary key numbers
            for key in self.KEY_NUMBERS['spread']['secondary']:
                if abs(spread_value - key) <= self.KEY_NUMBERS['spread']['margin']:
                    alerts.append(f"Spread {spread_value} is near secondary key number {key}")

        if consensus['total']:
            total_value = float(consensus['total'].split()[1])

            # Check total key numbers
            for key in self.KEY_NUMBERS['totals']['primary']:
                if abs(total_value - key) <= self.KEY_NUMBERS['totals']['margin']:
                    alerts.append(f"Total {total_value} is near key number {key}")

        return alerts

    def calculate_confidence_scores(self, advantages: Dict) -> Dict:
        """Calculate confidence scores based on advantages"""
        total_advantages = sum(len(adv) for adv in advantages.values())
        confidence_scores = {}

        if total_advantages > 0:
            for team, team_advantages in advantages.items():
                # Weight different advantages
                weighted_score = 0
                for advantage in team_advantages:
                    if 'QB' in advantage:
                        weighted_score += 1.5  # QB advantages count more
                    elif 'Defense' in advantage:
                        weighted_score += 1.2  # Defensive advantages count more
                    else:
                        weighted_score += 1.0  # Standard weight for other advantages

                # Calculate percentage but cap at 85%
                score = (weighted_score / (total_advantages + (0.5 * total_advantages))) * 100
                confidence_scores[team] = min(85, round(score))
        else:
            # If no advantages, split 50-50
            for team in advantages.keys():
                confidence_scores[team] = 50

        return confidence_scores

    # In NFLPredictor class
    def predict_game(self, team1: str, team2: str):
        """Complete game prediction with market analysis"""
        try:
            print(f"\nPredicting game between {team1} and {team2}")

            # Get game info
            game_info = self.get_future_game(team1, team2)
            if not game_info:
                print("No future game found between these teams")
                return None

            game_id = game_info['game']['id']

            # Check cache first
            cached_prediction = self.get_cached_prediction(game_id)
            if cached_prediction:
                print("Using cached prediction")
                return cached_prediction

            print(f"Game info: {game_info}")

            # Get team identifiers
            home_team_name = game_info['teams']['home']['name']
            away_team_name = game_info['teams']['away']['name']

            print(f"\nAnalyzing matchup between {home_team_name} vs {away_team_name}")

            # Get statistical analysis
            analysis = self.analyze_matchup(team1, team2)
            if 'error' in analysis:
                print(f"Analysis error: {analysis['error']}")
                return None

            print(f"Analysis completed successfully")

            # Map team names in analysis
            analysis['home_team'] = home_team_name
            analysis['away_team'] = away_team_name

            # Calculate confidence scores
            confidence_scores = self.calculate_confidence_scores(analysis['advantages'])
            print(f"Confidence scores: {confidence_scores}")

            # Get odds
            odds = self.get_game_odds(game_info['game']['id'])
            print(f"Odds data: {odds}")

            # Get recommendations
            recommendations = self.find_best_odds(analysis, odds)
            print(f"Betting recommendations: {recommendations}")

            prediction = {
                "matchup": f"{home_team_name} (Home) vs {away_team_name} (Away)",
                "date": game_info['game']['date']['date'],
                "statistical_analysis": analysis,
                "confidence_scores": confidence_scores,
                "odds": odds,
                "betting_recommendations": recommendations
            }

            # Cache only the prediction data and game_id
            self.cache_prediction_data(game_id, prediction)

            return prediction

        except Exception as e:
            print(f"Error in predict_game: {str(e)}")
            return None

    def calculate_sos_impact(self, team_id: int, is_road_game: bool) -> float:
        """Calculate strength of schedule impact"""
        try:
            recent_games = self.get_recent_games(team_id, 3)  # Last 3 opponents
            all_games = self.get_recent_games(team_id, 10)    # Season-long view

            # Calculate opponent stats
            recent_opp_wins = 0
            recent_opp_points = 0
            season_opp_wins = 0
            season_opp_points = 0

            for game_id in recent_games:
                game_stats = self.get_game_stats(game_id)
                opponent = next(stats for stats in game_stats if stats['team']['id'] != team_id)
                recent_opp_wins += opponent['team'].get('win_pct', 0.5)  # Default to 0.5 if not found
                recent_opp_points += opponent['team'].get('points_per_game', 20)  # Default to 20

            recent_sos = (recent_opp_wins / len(recent_games) * 0.30 +
                         recent_opp_points / (len(recent_games) * 30) * 0.15)  # Normalize points to 0-1 scale

            # Similar calculation for season-long SOS
            for game_id in all_games:
                game_stats = self.get_game_stats(game_id)
                opponent = next(stats for stats in game_stats if stats['team']['id'] != team_id)
                season_opp_wins += opponent['team'].get('win_pct', 0.5)
                season_opp_points += opponent['team'].get('points_per_game', 20)

            season_sos = (season_opp_wins / len(all_games) * 0.15 +
                         season_opp_points / (len(all_games) * 30) * 0.15)

            total_sos = recent_sos + season_sos

            # Calculate impact
            sos_impact = 0
            if total_sos > 0.6:
                sos_impact = 3  # Strong schedule bonus
            elif total_sos < 0.4:
                sos_impact = -3  # Weak schedule penalty

            # Additional road game penalty against strong schedule
            if is_road_game and total_sos > 0.6:
                sos_impact -= 1

            return sos_impact

        except Exception as e:
            print(f"Error calculating SOS impact: {e}")
            return 0

    def calculate_rest_impact(self, team_id: int, game_date: str) -> float:
        """Calculate rest days impact"""
        try:
            recent_games = self.get_recent_games(team_id, 1)  # Get last game
            if not recent_games:
                return 0

            last_game = recent_games[0]
            last_game_date = self.get_game_date(last_game)  # You'll need to implement this

            # Calculate days between games
            days_rest = (datetime.strptime(game_date, '%Y-%m-%d') -
                        datetime.strptime(last_game_date, '%Y-%m-%d')).days

            rest_impact = 0

            # Apply rest factors
            if days_rest >= 7:
                rest_impact += 2  # Week+ rest bonus
            elif days_rest < 6:
                rest_impact -= 3  # Short week penalty

            # Bye week check (14+ days between games)
            if days_rest >= 14:
                rest_impact += 2  # Bye week bonus

            return rest_impact

        except Exception as e:
            print(f"Error calculating rest impact: {e}")
            return 0

    def get_game_date(self, game_id: int) -> str:
        """Get the date of a specific game"""
        try:
            url = f"{self.base_url}/games"
            params = {
                'id': str(game_id),
                'league': '1',
                'season': '2024'
            }

            response = requests.get(url, headers=self.headers, params=params)
            data = response.json()
            if data and 'response' in data and data['response']:
                return data['response'][0]['game']['date']['date']
            return datetime.now().strftime('%Y-%m-%d')  # Fallback to current date
        except Exception as e:
            logger.error(f"Error fetching game date: {e}")
            return datetime.now().strftime('%Y-%m-%d')  # Fallback to current date

    def find_best_odds(self, analysis: Dict, odds: Dict) -> List[Dict]:
        """Determine best betting opportunities based on analysis"""
        recommendations = []

        team_scores = analysis.get('confidence_scores', {})
        home_team = analysis.get('home_team', '').upper()
        away_team = analysis.get('away_team', '').upper()

        if not team_scores or not (home_team and away_team):
            logger.warning("Missing team scores or team names")
            return []

        try:
            # Get team with highest confidence score
            if not team_scores:
                logger.warning("No confidence scores available")
                return []

            favorite_team = max(team_scores.items(), key=lambda x: x[1])[0]
            favorite_confidence = team_scores[favorite_team]
            is_favorite_home = (favorite_team == home_team)

            # Calculate adjusted confidence with SOS and rest impact
            adjusted_confidence = favorite_confidence
            try:
                favorite_id = self.get_team_info(favorite_team.lower())['id']
                game_date = analysis.get('game_date', '')

                if favorite_id and game_date:
                    sos_impact = self.calculate_sos_impact(favorite_id, not is_favorite_home)
                    rest_impact = self.calculate_rest_impact(favorite_id, game_date)
                    adjusted_confidence = min(favorite_confidence + 5,
                                        max(favorite_confidence - 5,
                                            favorite_confidence + sos_impact + rest_impact))
            except Exception as e:
                adjusted_confidence = favorite_confidence

            # Generate spread recommendation
            if odds and 'spread' in odds and odds['spread']:
                # Compare team strengths
                if favorite_team:
                    favorite_confidence = team_scores[favorite_team]
                    underdog_team = away_team if favorite_team == home_team else home_team
                    is_favorite_home = (favorite_team == home_team)

                    # Pick side based on team strength
                    if favorite_confidence > 55:
                        look_for_side = 'Home' if is_favorite_home else 'Away'
                        team_name = favorite_team
                    else:
                        look_for_side = 'Home' if not is_favorite_home else 'Away'
                        team_name = underdog_team

                    # Find best line
                    best_spread = None
                    best_odd = None

                    for spread, odd in odds['spread'].items():
                        if look_for_side in spread:
                            if not best_odd or odd > best_odd:
                                best_spread = spread
                                best_odd = odd

                    if best_spread:
                        advantages = analysis['advantages'].get(team_name, [])
                        explanation = (f"{team_name} show{'s' if not team_name.endswith('S') else ''} significant advantages in " +
                                    ", ".join(adv.split(':')[0].lower() for adv in advantages[:2])) if advantages else f"Value found backing {team_name} at current line"

                        rec_confidence = min(75, favorite_confidence) if team_name == favorite_team else min(65, team_scores[team_name] + 5)

                        recommendations.append({
                            'type': 'Spread',
                            'bet': best_spread,
                            'odds': best_odd,
                            'confidence': rec_confidence,
                            'explanation': explanation
                        })

            # Calculate totals (including half-time)
            if 'team_stats' in analysis:
                offensive_metrics = {
                    'yards_per_play': lambda x: float(x) / 10,
                    'third_down_pct': lambda x: float(x) / 100,
                    'redzone_pct': lambda x: float(x) / 100,
                    'yards_per_pass': lambda x: float(x) / 15
                }

                defensive_metrics = {
                    'points_against': lambda x: (100 - float(x)) / 100,
                    'turnovers': lambda x: float(x) / 4,
                    'sacks': lambda x: float(x) / 5
                }

                # Calculate efficiency ratings
                total_rating, metrics_count = 0, 0
                defense_rating, defense_count = 0, 0

                for team_stats in analysis['team_stats'].values():
                    for metric, normalizer in offensive_metrics.items():
                        if metric in team_stats:
                            try:
                                total_rating += normalizer(team_stats[metric])
                                metrics_count += 1
                            except (ValueError, TypeError, ZeroDivisionError):
                                continue

                    for metric, normalizer in defensive_metrics.items():
                        if metric in team_stats:
                            try:
                                defense_rating += normalizer(team_stats[metric])
                                defense_count += 1
                            except (ValueError, TypeError, ZeroDivisionError):
                                continue

                avg_offensive_rating = total_rating / metrics_count if metrics_count > 0 else 0.5
                avg_defensive_rating = defense_rating / defense_count if defense_count > 0 else 0.5

                # Find best total (full game, 1st half, or 2nd half)
                best_total_play = None
                best_confidence = 45  # Minimum confidence threshold

                # Check all total markets
                total_markets = [
                    ('total', 35, 55),  # Full game
                    ('first_half_total', 17, 28),  # First half
                    ('second_half_total', 17, 28)  # Second half
                ]

                for market, min_points, max_points in total_markets:
                    if market in odds:
                        for total, odd in odds[market].items():
                            try:
                                if 'Over' not in total and 'Under' not in total:
                                    continue

                                points = float(total.split()[1])
                                is_over = 'Over' in total

                                if points < min_points or points > max_points:
                                    continue

                                # Calculate confidence
                                if is_over and avg_offensive_rating > avg_defensive_rating:
                                    confidence = int((avg_offensive_rating * 70) + (avg_defensive_rating * 30))
                                    period = "first half" if market == "first_half_total" else "second half" if market == "second_half_total" else "full game"
                                    explanation = f"Strong offensive efficiency metrics suggest high-scoring {period}" if confidence > 60 else f"Teams showing enough offensive efficiency to justify the {period} over"
                                elif not is_over and avg_defensive_rating > avg_offensive_rating:
                                    confidence = int((avg_defensive_rating * 70) + ((1 - avg_offensive_rating) * 30))
                                    period = "first half" if market == "first_half_total" else "second half" if market == "second_half_total" else "full game"
                                    explanation = f"Strong defensive metrics suggest low-scoring {period}" if confidence > 60 else f"Teams showing defensive strength, suggesting the {period} under"
                                else:
                                    continue

                                confidence = min(75, max(45, confidence))

                                if confidence > best_confidence:
                                    best_total_play = {
                                        'type': f'Total ({market.replace("_", " ").title()})',
                                        'bet': total,
                                        'odds': odd,
                                        'confidence': confidence,
                                        'explanation': explanation
                                    }
                                    best_confidence = confidence

                            except Exception as e:
                                logger.error(f"Error processing total {total}: {e}")
                                continue

                if best_total_play:
                    recommendations.append(best_total_play)

        except Exception as e:
            print(f"Error generating recommendations: {e}")

        return recommendations

    def find_best_value_bets(self, game_id: int, analysis: Dict) -> List[Dict]:

        """Find best value bets considering market data"""
        market_data = self.get_market_data(game_id)
        recommendations = []

        # Add market context to existing analysis
        if market_data['consensus']['spread']:
            consensus_spread = market_data['consensus']['spread']
            consensus_odds = market_data['consensus']['spread_odds']

            # Add spread analysis considering consensus and key numbers
            recommendations.append({
                'type': 'Spread (Market Consensus)',
                'bet': consensus_spread,
                'odds': consensus_odds['avg_odd'],
                'confidence': 60,  # Base confidence
                'explanation': f"Market consensus spread with average odds of {consensus_odds['avg_odd']:.2f}"
            })

        if market_data['consensus']['total']:
            consensus_total = market_data['consensus']['total']
            consensus_odds = market_data['consensus']['total_odds']

            # Add totals analysis considering consensus
            recommendations.append({
                'type': 'Total (Market Consensus)',
                'bet': consensus_total,
                'odds': consensus_odds['avg_odd'],
                'confidence': 55,  # Base confidence
                'explanation': f"Market consensus total with average odds of {consensus_odds['avg_odd']:.2f}"
            })

        # Add key number alerts
        for alert in market_data['key_number_alerts']:
            # Adjust recommendations based on key numbers
            recommendations.append({
                'type': 'Key Number Alert',
                'bet': 'Consider line movement',
                'explanation': alert
            })

        return recommendations

    def analyze_cached_stats(self, team1: str, team2: str, team1_stats: dict, team2_stats: dict) -> Dict:
        """Analyze matchup using cached statistics"""
        analysis = {
            'team_stats': {
                team1.upper(): team1_stats,
                team2.upper(): team2_stats
            },
            'advantages': {
                team1.upper(): [],
                team2.upper(): []
            }
        }

        # Define metrics to compare
        metrics = {
            'yards_per_play': ('Yards per Play', 0.5),
            'third_down_pct': ('Third Down %', 5),
            'redzone_pct': ('Red Zone %', 10),
            'possession_time': ('Time of Possession', 2),
            'yards_per_pass': ('Yards per Pass', 0.5),
            'yards_per_rush': ('Yards per Rush', 0.3),
        }

        # Defensive metrics
        defensive_metrics = {
            'sacks': ('Defense - Sacks', 1),
            'turnovers': ('Defense - Turnovers Forced', 0.5),
            'points_against': ('Defense - Points Allowed', 3, True)
        }

        # Compare metrics
        for metric, (display_name, threshold) in metrics.items():
            if metric in team1_stats and metric in team2_stats:
                value1 = float(team1_stats[metric])
                value2 = float(team2_stats[metric])
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

        # Compare defensive metrics
        for metric, (display_name, threshold, *args) in defensive_metrics.items():
            if metric in team1_stats and metric in team2_stats:
                value1 = float(team1_stats[metric])
                value2 = float(team2_stats[metric])
                lower_is_better = len(args) > 0 and args[0]

                diff = value2 - value1 if lower_is_better else value1 - value2

                if abs(diff) > threshold:
                    if diff > 0:
                        analysis['advantages'][team1.upper()].append(
                            f"Better {display_name}: {value1:.1f} vs {value2:.1f}"
                        )
                    else:
                        analysis['advantages'][team2.upper()].append(
                            f"Better {display_name}: {value2:.1f} vs {value1:.1f}"
                        )

        return analysis

    def get_cached_prediction(self, game_id: int) -> Optional[Dict]:
        """Get cached prediction if not expired"""
        try:
            self.cursor.execute('''
                SELECT prediction_data
                FROM game_predictions_cache
                WHERE game_id = ? AND expiry > datetime('now')
            ''', (game_id,))

            result = self.cursor.fetchone()
            if result and result[0]:
                try:
                    return json.loads(result[0])
                except json.JSONDecodeError:
                    logger.error("Invalid JSON in cache")
                    return None
            return None
        except Exception as e:
            logger.error(f"Error reading prediction cache: {e}")
            return None

    def get_cached_game_data(self, game_id: int) -> Optional[Dict]:
        """Get cached game data"""
        try:
            self.cursor.execute('''
                SELECT game_data, last_updated
                FROM game_predictions_cache
                WHERE game_id = ?
            ''', (game_id,))
            result = self.cursor.fetchone()

            if result:
                game_data, last_updated = result
                last_updated = datetime.strptime(last_updated, '%Y-%m-%d %H:%M:%S')

                if datetime.now() - last_updated < timedelta(hours=24):
                    logger.info(f"Using cached game data for game {game_id}")
                    return json.loads(game_data)

            return None
        except Exception as e:
            logger.error(f"Error reading game cache: {e}")
            return None

    def cache_prediction_data(self, game_id: int, prediction_data: Dict):
        """Cache prediction data"""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO game_predictions_cache
                (game_id, prediction_data, last_updated, expiry)
                VALUES (?, ?, datetime('now'), datetime('now', '+6 hours'))
            ''', (
                game_id,
                json.dumps(prediction_data)
            ))
            self.conn.commit()
            logger.info(f"Successfully cached prediction for game {game_id}")
        except Exception as e:
            logger.error(f"Error caching prediction data: {e}")

    def cache_game_data(self, game_id: int, game_data: Dict):
        """Cache game data"""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO game_predictions_cache
                (game_id, game_data, last_updated, expiry)
                VALUES (?, ?, datetime('now'), datetime('now', '+24 hours'))
            ''', (
                game_id,
                json.dumps(game_data)
            ))
            self.conn.commit()
            logger.info(f"Cached game data for game {game_id}")
        except Exception as e:
            logger.error(f"Error caching game data: {e}")