import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score



# FILE_PATH = './emergency_events.csv'
FILE_PATH = 'emergency_events.csv'


# fig, ax = plt.subplots(figsize=(6, 6))

data = pd.read_csv(FILE_PATH)   # import data
# data = data.sort_values(by=['t'])   # sort by time


def make_plot(em_type, filename):
    subset = data[data["etype"] == em_type]
    X_train = subset["x"].values.reshape(-1, 1)
    y_train = subset["y"].values


    # Create a linear regression model object
    model = LinearRegression()

    # Train the model using the training data
    model.fit(X_train, y_train)

    x_line = np.linspace(subset["x"].min(), subset["x"].max(), 100).reshape(-1, 1)
    y_line = model.predict(x_line)

    color = "black"
    if (em_type == "police"):
        color = "blue"
    if(em_type == "medical"):
        color = "yellow"
    if (em_type == "fire"):
        color = "red"

    plt.figure()
    plt.scatter(X_train, y_train, color=color)
    plt.plot(x_line, y_line, color="black")
    plt.title(f"Linear Regression — {em_type.capitalize()}")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.savefig(filename) 
    plt.close()


for emerg in ["police", "fire", "medical"]:
    make_plot(emerg, f"{emerg}_linear_regression.png")