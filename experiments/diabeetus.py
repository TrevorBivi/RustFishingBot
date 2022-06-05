import math as m
import matplotlib.pyplot as plt
import numpy as np
from sklearn import datasets, linear_model
from sklearn.metrics import mean_squared_error, r2_score



df = [
    [2600, 3.0, 20 ],
    [3000, 4.0, 15 ],
    [3200, 15//4, 18 ],
    [3600, 3, 30],
    [4000, 5,8]
]
dfprice = [
550000,565000,610000,595000,760000
    ]
reg = linear_model.LinearRegression()
reg.fit(df,dfprice)
