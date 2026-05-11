import requests
import argparse
import pandas as pd
from bs4 import BeautifulSoup
import re
import matplotlib.pyplot as plt
import os
import json

# For CSV with Pricing Data
file_path = 'data/raw/Cars Datasets 2025.csv'


# For API with BodyType and use 2025 Models
base_url_api = 'https://vpic.nhtsa.dot.gov/api/vehicles'
groups = ['car','passenger_car','sedan','coupe','hatchback','mpv','suv','minivan','truck']

# The following function checks if the file exists first to avoid calling an API endpoint multiple times for efficiency.
# Then the function checks if the model is present inside the specific JSON file, and if it does, it returns the vehicleType, otherise it returns None
def getbodyType(make, model, vehicleType):
    file_name = f'{make}_{vehicleType}.json'
    if os.path.exists(file_name):
        try:
            with open('data/raw/'+file_name, 'r') as file:
                data = json.load(file)
            return vehicleType if any(model.lower() in item["Model_Name"].lower() for item in data.get('Results', [])) else None
        except:
            return None
    else:
        url = f'{base_url_api}/GetModelsForMakeYear/make/{make.lower()}/modelyear/2025/vehicletype/{vehicleType}?format=json'
        response = requests.get(url)
        try:
            r_json = response.json()
        except:
            r_json = None
        if response.status_code != 200:
            return None
        else:
            try:
                if r_json.get('Results',[]):
                    with open('data/raw/'+file_name, 'w') as file:
                        json.dump(r_json, file)
                return vehicleType if any(model.lower() in item["Model_Name"].lower() for item in r_json.get('Results', [])) else None
            except:
                return None

# For RepairPal with Reliability Rating
base_url_rp = 'https://repairpal.com/reliability'
rp_headers = {
    'User-Agent': 'Mozilla/5.0'}

# getreliabilityScore scrapes from RepairPal using BeautifulSoup
# First checks if the file exists already so the same page does not get scraped twice
# Uses regex to check if a score exists in the format "x.x out of 5.0" and returns the score if it exists, else returns None
def getreliabilityScore(make, model):

    if  os.path.exists(reliability_file):
        try:
            with open(reliability_file) as file:
                for line in file:
                    if line.split(',')[0] == make and line.split(',')[1] == model:
                        return float(line.split(',')[2])
        except:
            pass

    
    url = f'{base_url_rp}/{make}/{model}'
    response = requests.get(url, headers=rp_headers)

    if response.status_code != 200:
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    text = soup.get_text()
    
    match = re.search(r'(\d\.\d)\s*(out of 5.0)', text)

    score = float(match.group(1)) if match else None

    with open('data/processed/'+reliability_file, 'a') as file:
        file.write(f'{make},{model},{score}\n') if score != None else file.write(f'{make},{model},{None}\n')
    
    return score


if __name__ == '__main__':

    # Define and parse all arguments using argeparse
    parser = argparse.ArgumentParser('Arguments')
    parser.add_argument('--min_price', required=True)
    parser.add_argument('--max_price', required=True)
    parser.add_argument('--body', choices=groups, required=True)
    args = parser.parse_args()

    # Cleaning data by deleting $ signs and converting prices to a numeric value
    df_csv = pd.read_csv(file_path, encoding='cp1252')
    df_csv['Cars Prices'] = df_csv['Cars Prices'].replace({r'[\$,\-\s]':''}, regex = True)
    df_csv['Cars Prices'] = pd.to_numeric(df_csv['Cars Prices'], errors='coerce')

    # Filtering the dataset to only include those with prices in the user specified price range
    df_csv = df_csv[(int(args.min_price)<=(df_csv['Cars Prices'])) & (df_csv['Cars Prices']<=int(args.max_price))]

    # Cleaning the car names to only include the model and not the trim for scraping and API purposes
    df_csv["Model"] = df_csv["Cars Names"].str.split().str[0]

    # Initializing the file to house the reliability scores
    reliability_file = f'{args.body}_reliability_scores.csv'
    with open('data/processed/'+reliability_file, 'w') as file:
        file.write('Company Names,Cars Name,Reliability Score\n')

    # Group all body types applicable as Passenger Cars
    if args.body in groups[0:5]:

        # Appending Body Type field to dataframe and dropping any null values (dropped values are not passenger cars)
        df_csv['Body Type'] = df_csv.apply(lambda row: getbodyType(row['Company Names'],row['Model'], 'passenger car'),axis=1)
        df_csv = df_csv.dropna(subset = ['Body Type'])

        # Appending Reliability Score field to dataframe, dropping null values, and ordering by Reliability Score, then Price
        df_csv['Reliability Score'] = df_csv.apply(lambda row: getreliabilityScore(row['Company Names'],row['Model']),axis=1)
        df_csv = df_csv.dropna(subset=['Reliability Score'])
        df_csv = df_csv.sort_values(by=['Reliability Score', 'Cars Prices'], ascending=[False, True])

    # Group all body types applicable as MPVs
    elif args.body in groups[5:8]:

        # Appending Body Type field to dataframe and dropping any null values (dropped values are not MPVs)
        df_csv['Body Type'] = df_csv.apply(lambda row: getbodyType(row['Company Names'],row['Model'],'mpv'),axis=1)
        df_csv = df_csv.dropna(subset = ['Body Type'])
    
        # Appending Reliability Score field to dataframe, dropping null values, and ordering by Reliability Score, then Price
        df_csv['Reliability Score'] = df_csv.apply(lambda row: getreliabilityScore(row['Company Names'],row['Model']),axis=1)
        df_csv = df_csv.dropna(subset=['Reliability Score'])
        df_csv = df_csv.sort_values(by=['Reliability Score', 'Cars Prices'], ascending=[False, True])

    # Group all body types applicable as Trucks
    elif args.body == groups[8]:

        # Appending Body Type field to dataframe and dropping any null values (dropped values are not trucks)
        df_csv['Body Type'] = df_csv.apply(lambda row: getbodyType(row['Company Names'],row['Model'],'truck'),axis=1)
        df_csv = df_csv.dropna(subset = ['Body Type'])

        # Appending Reliability Score field to dataframe, dropping null values, and ordering by Reliability Score, then Price
        df_csv['Reliability Score'] = df_csv.apply(lambda row: getreliabilityScore(row['Company Names'],row['Model']),axis=1)
        df_csv = df_csv.dropna(subset=['Reliability Score'])
        df_csv = df_csv.sort_values(by=['Reliability Score', 'Cars Prices'], ascending=[False, True])

    else:
        raise ValueError('Please Enter a Valid Body Type')
    
    # Save the final dataset to CSV
    df_csv.to_csv(f'results/{args.body}_final_dataset.csv', index=False)

    # Top 10 cars used for visualization
    top_10_cars = df_csv.head(10)
    # Top 3 cars used to print
    top_3_cars = df_csv.head(3)

    # Creating and saving a bar graph of top 10 most reliable vehicles within the price range ranked by reliability, then price.
    plt.figure(figsize=(12, 6))
    plt.bar(top_10_cars['Company Names'] + ' ' + top_10_cars['Cars Names'], top_10_cars['Cars Prices'])
    plt.ylim(int(args.min_price) - 2000 if int(args.min_price) > 2000 else None, None)
    plt.grid(axis='y')
    plt.xticks(rotation=45, ha='right')
    plt.xlabel('Make and Model')
    plt.ylabel('Prices')
    plt.title(f'Top {len(top_10_cars)} Most Reliable {args.body.capitalize()}s Between \\${args.min_price} and \\${args.max_price} From Left to Right ')
    plt.tight_layout()
    plt.savefig(f'results/{args.body}_plot.png')
    plt.close()

    # Printing the top 3 recommendations
    print(f"Here Are Your Top {len(top_3_cars)} Most Reliable {args.body}s:\n{top_3_cars[['Cars Prices','Company Names','Cars Names','Reliability Score']].reset_index(drop=True)}")

