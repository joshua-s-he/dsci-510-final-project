
# A Data-Driven Automobile Recommendation Model

## (1) Program Requirements
Run the following in your terminal to install all required libraries 
```bash
pip install -r requirements.txt
```
Additionally, you will need to visit [Kaggle](https://www.kaggle.com/datasets/abdulmalik1518/cars-datasets-2025) to download the Cars Datasets CSV.

## (2) How to Run
The program is run through the terminal with the following format:
```bash
python src/recommender.py --min_price {min_price} --max_price {max_price} --body {body}
```
The body argument can be one of the following choices:
```bash
['car','passenger_car','sedan','coupe','hatchback','mpv','suv','minivan','truck']
```
#### Program Arguments Notes
* All arguments are required
* min_price and max_price need to be integers
* car, passenger_car, sedan, coupe, hatchback are grouped into passenger_car
* mpv, suv, minivan are grouped into mpv (multipurpose passenger vehicle)
* truck is it's own category

Once the program is run, no further steos are required. All datasets and visualizations are produced by recommender.py