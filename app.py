import numpy as np
import requests
import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier, StackingClassifier  
import time
from sklearn.pipeline import Pipeline
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import SimpleImputer, IterativeImputer
from sklearn.preprocessing import OrdinalEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import BayesianRidge
from flask import Flask, render_template, request, jsonify



def getModel(choice):
    list = []
    if choice == 1:
        # Load the Random Forest model
        with open('modelWinLossDraw.pkl', 'rb') as file:
            model = pickle.load(file)
            list.append(model)
        return list
    elif choice == 2:
        # Load the Stacking Classifier model
        with open('modelWinLoss.pkl', 'rb') as file:
            model = pickle.load(file)
            with open('win_loss_theshold.txt', 'r') as file2:
                threshold = float(file2.read().strip())
                print(threshold)
            list.append(model)
            list.append(threshold)
        return list

# usernameWhile = input("Enter the username of the player playing white: ")
# usernameBlack = input("Enter the username of the player playing black: ")

def getPlayerData(usernameWhite, usernameBlack):
    url1 = f"https://lichess.org/api/user/{usernameWhite}"
    url2 = f"https://lichess.org/api/user/{usernameBlack}"
    response1 = requests.get(url1)
    time.sleep(1)  # To avoid hitting the API rate limit
    response2 = requests.get(url2)
    if response1.status_code == 200 and response2.status_code == 200:
        data1 = response1.json()
        data2 = response2.json()
        player_data = {
            'white_rating': data1.get('perfs', {}).get('rapid', {}).get('rating', None),
            'black_rating': data2.get('perfs', {}).get('rapid', {}).get('rating', None),
            'white_flag': data1.get('profile', {}).get('flag', None),
            'black_flag': data2.get('profile', {}).get('flag', None),
            'whit_rd': data1.get('perfs', {}).get('rapid', {}).get('rd', None),
            'black_rd': data2.get('perfs', {}).get('rapid', {}).get('rd', None),
            'white_playtime': data1.get('playtime', None),
            'black_playtime': data2.get('playtime', None),
        }
        return player_data
    else:
        print("Error fetching player data")
        return None


# eco = input("Enter the ECO code of the game: ")
# timme = input("Enter the time control of the game (e.g., '3', '5'): ")
# increment = input("Enter the increment of the game (e.g., '2', '0'): ")

# event = 'rapid'
# rated = 1




def predictOutcome(model, player_data, eco, timme, increment, event, rated,choicePlayer):
    if model is None or player_data is None:
        print("Model or player data is missing.")
        return None
    rating_diff = player_data['white_rating'] - player_data['black_rating']

    event = 'rapid'
    # Prepare the input data for prediction
    input_data = {
        'event': 'Rated Rapid game',
        'white_elo': player_data['white_rating'],
        'black_elo': player_data['black_rating'],
        'eco': eco,
        'event_type': event,
        'rd_white': player_data['whit_rd'],
        'rd_black': player_data['black_rd'],
        'flag_white': player_data['white_flag'],
        'flag_black': player_data['black_flag'],
        'play_time_white': player_data['white_playtime'],
        'play_time_black': player_data['black_playtime'],
        'rated': rated,
        'time': timme,
        'increment': increment,
        'rating_diff': rating_diff
    }
    
    # Convert to DataFrame
    input_df = pd.DataFrame([input_data])
    
    # Create the pipeline

    if len(model) == 1:
        pipeline = pickle.load(open('pipelineWLD.pkl', 'rb'))
    elif len(model) == 2:
        pipeline = pickle.load(open('pipelineWL.pkl', 'rb'))
    else:
        print("Invalid model choice.")
        return None
    # Transform the input data
    input_df = pipeline.transform(input_df)

    # Predict the outcome probabilities
    if len(model)==1:
        prediction = model[0].predict_proba(input_df)
    else:
        threshold = model[1]
        prediction = model[0].predict_proba(input_df)
        if choicePlayer == 1:
            print(prediction[0])
            prob = prediction[0][1]
        elif choicePlayer == 0:
            print(prediction[0])
            prob = prediction[0][0]
        else: 
            prob = None
        print(f"Prediction probabilities: {prediction}")
        print(f"Probabilities: {prob}")
        prediction = prediction[:, 1]
        prediction = (prediction >= threshold).astype(int)
        
        print(f"Prediction after thresholding: {prediction}")
    # Map the prediction to the outcome
    if len(model)==1:
        outcome = model[0].classes_[np.argmax(prediction)]
        if choicePlayer == 1:
            print(prediction[0])
            prob = prediction[0][2]
        elif choicePlayer == 0:
            print(prediction[0])
            prob = prediction[0][0]
        else: 
            prob = None
        print(f"Outcome: {outcome}, Prediction: {prediction}")
    else:
        outcome = model[0].classes_[prediction[0]]
    return outcome, prob

# choice = int(input("Enter 1 for Random Forest or 2 for Stacking Classifier: "))
# model = getModel(choice)
# player_data = getPlayerData(usernameWhile, usernameBlack)
# if player_data is not None:
#     outcome, prediction = predictOutcome(model, player_data, eco, timme, increment, event, rated)
#     if outcome is not None:
#         print(f"Predicted outcome: {outcome}")
#         print(f"Prediction probabilities: {prediction}")
# else:
#     print("Failed to fetch player data or make a prediction.")
app = Flask(__name__)
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/predict', methods=['POST'])
def predict():
    print("Received request for prediction")
    event = 'rapid'
    rated = 1
    data = request.get_json()
    print(f"Received data: {data}")
    choice = int(data.get('choice'))
    usernameWhite = str(data.get('usernameWhite'))
    usernameBlack = str(data.get('usernameBlack'))
    eco = str(data.get('eco'))
    timme = int(data.get('time'))
    increment = int(data.get('increment'))

    model = getModel(choice)
    player_data = getPlayerData(usernameWhite, usernameBlack)
    print(f"Model: {model}")
    print(f"Player data: {player_data}")
    if model is not None and len(model) > 0:
        print("Model loaded successfully")
    else:
        print("Failed to load model")
    print(f"Player data: {player_data}")
    print(f"ECO: {eco}, Time: {timme}, Increment: {increment}, Event: {event}, Rated: {rated}")
    print(f"Username White: {usernameWhite}, Username Black: {usernameBlack}")
    print(f"Choice: {choice}")
    choicePlayer = data.get('choicePlayer')
    
    if player_data is not None:
        outcome, prob = predictOutcome(model, player_data, eco, timme, increment, event, rated, choicePlayer)
        print(f"Predicted outcome: {outcome}")
        return jsonify({'outcome': int(outcome), 'probability': prob})
    else:
        return jsonify({'error': 'Failed to fetch player data or make a prediction.'}), 400
if __name__ == '__main__':
    app.run(debug=True)