# main.py
from predictor import NFLPredictor
from config import API_KEY
from database import init_database

def main():
    # Initialize database
    init_database()

    # Create predictor instance
    predictor = NFLPredictor(API_KEY)

    # Test prediction
    predictor.print_prediction('Eagles', 'Commanders')

if __name__ == "__main__":
    main()