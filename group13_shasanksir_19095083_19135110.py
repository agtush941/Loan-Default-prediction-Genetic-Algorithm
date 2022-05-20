# -*- coding: utf-8 -*-
"""Group13_ShasankSir_19095083_19135110.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/12qgRp6fmuxEsRwNGf56ypc5fbsEqBSC5

#### "Predict whether a mammogram mass is benign or malignant"

1. BI-RADS assessment: 1 to 5 (ordinal)  
2. Age: patient's age in years (integer)
3. Shape: mass shape: round=1 oval=2 lobular=3 irregular=4 (nominal)
4. Margin: mass margin: circumscribed=1 microlobulated=2 obscured=3 ill-defined=4 spiculated=5 (nominal)
5. Density: mass density high=1 iso=2 low=3 fat-containing=4 (ordinal)
6. Severity: benign=0 or malignant=1 (binominal)

## Import Libraries
"""

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, precision_score, recall_score, classification_report, confusion_matrix, fbeta_score
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, KFold
from scipy import stats
from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import gradient_descent_v2, adam_v2, rmsprop_v2

"""## Get the Data"""

data = pd.read_csv('/content/mammographic_masses.data.txt', names=['BI_RADS','Age','Shape','Margin','Density','Severity'])

"""Convert missing data (indicated by a ?) into NaN and add the appropriate column names (BI_RADS, age, shape, margin, density, and severity)"""

data = data.replace('?',np.nan)
data

"""**Drop BI_RADS column because it has no influence on the severity forecast**"""

data = data.drop(columns=['BI_RADS'])

"""**Convert datatype 'object' to 'float64'**  """

data.info()

data = data.astype(float)
data

data.info()

data.describe()

"""### Analysing missing values
**First we get the missing values per feature.**

*Lets check them out as well*
"""

missing_values_feature = data.isnull().sum(axis=0)
graph = missing_values_feature.drop(labels='Severity')
graph

plt.figure(figsize=(15, 5))
plt.subplot(131)
plt.bar(graph.axes[0].to_list(), graph.values)

"""*Finally we can check the percentage of missing values per feature*"""

percent_missing = data.isnull().sum() * 100 / len(data)
missing_value_df = pd.DataFrame({'percent_missing': percent_missing})
print(missing_value_df)

"""**After analysing the columns, we should have a look at the rows**"""

data_missing = len(data.columns) - (data.apply(lambda x: x.count(), axis=1))
missing_values_data_rows = pd.DataFrame({'data_missing':data_missing})
missing_values_data_rows.sort_values('data_missing',inplace=True,ascending=False)
missing_values_data_rows

"""**Now lets analyse the missing data per class (Severity = 0 or Severity = 1).**

*First we group the missing values per class*
"""

grouped_data = data.groupby('Severity')
missing_values_class = grouped_data.count().rsub(grouped_data.size(), axis=0)
missing_values_class

"""*Now we split the dataframe per class so we can draw our plot*"""

m_new_1, m_new_2 = missing_values_class.head(1), missing_values_class.tail(1)

x = np.arange(len(m_new_1.axes[1].to_list()))
width = 0.4

fig, ax = plt.subplots()
rects1 = ax.bar(x - width/2, m_new_1.values[0], width=width, label = "Severity 0")
rects2 = ax.bar(x + width/2, m_new_2.values[0], width=width, label = "Severity 1")

ax.set_xticks(x)
ax.set_xticklabels(m_new_1.axes[1].to_list())
ax.legend()

"""**Finally, for each class we're going to calculate the number of rows that have 1 and 2 NaN values**"""

rows_mv1_sv0 = 0
rows_mv2_sv0 = 0
rows_mv1_sv1 = 0
rows_mv2_sv1 = 0

for index, row in data.iterrows():
    if(row['Severity'] == 0):
        if(row.isnull().sum() == 1):
            rows_mv1_sv0 += 1
        elif(row.isnull().sum() == 2):
            rows_mv2_sv0 += 1
    else:
        if(row.isnull().sum() == 1):
            rows_mv1_sv1 += 1
        elif(row.isnull().sum() == 2):
            rows_mv2_sv1 += 1

"""*We create a dataframe only for visualization purpose*"""

numberofnan_class = pd.DataFrame(np.array([[rows_mv1_sv0,rows_mv2_sv0], [rows_mv1_sv1,rows_mv2_sv1]]), 
                                    index=['Severity 0','Severity 1'], columns=['1 NaN', '2 NaN'])
numberofnan_class

labels = ['1 NaN', '2 NaN']
x = np.arange(len(labels))
width = 0.4

fig, ax = plt.subplots()
rects1 = ax.bar(x - width/2, [rows_mv1_sv0,rows_mv2_sv0], width=width, label = "Severity 0")
rects2 = ax.bar(x + width/2, [rows_mv1_sv1,rows_mv2_sv1], width=width, label = "Severity 1")

ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.legend()

"""*With this information we can also see the number of rows with 1 or 2 missing values per class*"""

nan_class = pd.DataFrame(np.array([[rows_mv1_sv0+rows_mv2_sv0], [rows_mv1_sv1+rows_mv2_sv1]]), 
                                    index=['Severity 0','Severity 1'], columns=['Sum'])
nan_class

plt.figure(figsize=(3, 5))
plt.bar(['Severity 0','Severity 1'],[rows_mv1_sv0+rows_mv2_sv0,rows_mv1_sv1+rows_mv2_sv1])

"""**The missing data seems randomly distributed, so we decided to go with the following strategy:**

* Drop rows with 2 NaN values

* Replace the NaN values from rows with 1 missing value

*First we get the mode of every feature for each class*
"""

mode_sv0 = data[data['Severity'] == 0].mode()
mode_sv1 = data[data['Severity'] == 1].mode()
mode_sv0 = mode_sv0.drop([1])
with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    print(mode_sv0)
    print(mode_sv1)

"""*After we create conditions to replace the NaN values on rows with 1 missing value.*

*For that we need the index of the rows which have 1 missing value.*
"""

rows_1nan = missing_values_data_rows.index[missing_values_data_rows['data_missing'] == 1].tolist()
mask_sv0 = (data['Severity'] == 0) & (data.index.isin(rows_1nan))
mask_sv1 = (data['Severity'] == 1) & (data.index.isin(rows_1nan))

"""*We can now proceed and replace the missing values for their class mode* """

data.loc[mask_sv0, 'Shape'] = data.loc[mask_sv0, 'Shape'].fillna(mode_sv0.loc[0,'Shape'])
data.loc[mask_sv0, 'Margin'] = data.loc[mask_sv0, 'Margin'].fillna(mode_sv0.loc[0,'Margin'])
data.loc[mask_sv0, 'Density'] = data.loc[mask_sv0, 'Density'].fillna(mode_sv0.loc[0,'Density'])
data.loc[mask_sv1, 'Age'] = data.loc[mask_sv1, 'Age'].fillna(mode_sv1.loc[0,'Age'])
data.loc[mask_sv1, 'Shape'] = data.loc[mask_sv1, 'Shape'].fillna(mode_sv1.loc[0,'Shape'])
data.loc[mask_sv1, 'Margin'] = data.loc[mask_sv1, 'Margin'].fillna(mode_sv1.loc[0,'Margin'])
data.loc[mask_sv1, 'Density'] = data.loc[mask_sv1, 'Density'].fillna(mode_sv1.loc[0,'Density'])
data

"""*Finally, we can drop rows with NaN values because the only ones that are left are the ones with 2 NaN*"""

data = data.dropna()
data.index = np.arange(1, len(data) + 1)
data

"""## Exploratory Data Analysis

**Auxiliar functions & General definitions**
"""

c_palette = ['tab:green','tab:red']

def categorical_summarized(dataframe, x=None, y=None, hue=None, palette='Set1', verbose=True):
    if x == None:
        column_interested = y
    else:
        column_interested = x
    series = dataframe[column_interested]
    print(series.describe())
    print('mode: ', series.mode())
    if verbose:
        print('='*80)
        print(series.value_counts())

    sns.countplot(x=x, y=y, hue=hue, data=dataframe, palette=palette)
    plt.show()

def quantitative_summarized(dataframe, x=None, y=None, hue=None, palette='Set1', ax=None, verbose=True, swarm=False):
    series = dataframe[y]
    print(series.describe())
    print('mode: ', series.mode())
    if verbose:
        print('='*80)
        print(series.value_counts())

    sns.boxplot(x=x, y=y, hue=hue, data=dataframe, palette=palette, ax=ax)

    if swarm:
        sns.swarmplot(x=x, y=y, hue=hue, data=dataframe,
                      palette=palette, ax=ax)

    plt.show()

"""**Countplot of the Severity (Benign 0 vs Malignant 1)**"""

sns.set_style('whitegrid')
ax = sns.countplot(x='Severity',data=data,palette=c_palette)


total = len(data['Severity'])

for p in ax.patches:
    height = p.get_height()
    ax.text(p.get_x()+p.get_width()/2.,
            height + 3,
            '{:.1f}%'.format(100 * height/total),
            ha="center")

"""**Severity on Age**"""

g = sns.FacetGrid(data,hue='Severity',palette=c_palette,size=6,aspect=2)
bins=[5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100]
g.map(plt.hist, "Age", bins=bins, alpha=0.6).add_legend()
plt.xticks([5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100])
plt.show()

"""**Severity on Shape (mass shape: round=1 oval=2 lobular=3 irregular=4)**"""

categorical_summarized(data, y = 'Shape', hue='Severity', palette=c_palette)

"""**Severity on Margin (mass margin: circumscribed=1 microlobulated=2 obscured=3 ill-defined=4 spiculated=5)**"""

categorical_summarized(data, y = 'Margin', hue='Severity', palette=c_palette)

"""**Severity on Density (mass density high=1 iso=2 low=3 fat-containing=4)**"""

categorical_summarized(data, y = 'Density', hue='Severity', palette=c_palette)

categorical_summarized(data, y = 'Margin', hue='Shape')

categorical_summarized(data, y = 'Density', hue='Shape')

categorical_summarized(data, y = 'Density', hue='Margin')

"""### Detect Outliers using Scatter plot (Multi-variate outlier)"""

fig, ax = plt.subplots(figsize=(16,8))
ax.scatter(data['Age'], data['Shape'])
ax.set_xlabel('Age')
ax.set_ylabel('Shape')
#ax.set_ylabel('Margin')
#ax.set_ylabel('Density')
plt.show()

"""### Detect outliers using mathematical function Z-Score"""

z = np.abs(stats.zscore(data))
threshold = 3
print(np.where(z > threshold))
# The first array contains the list of row numbers and second array respective column numbers

"""Column 3 (density) has all outliers

## Data Preparation

### Remove Outliers using Z-Score
"""

# Z score implementation
#data = data[(np.abs(stats.zscore(data)) < 3).all(axis=1)]
#data.index = np.arange(1, len(data) + 1)
#data

"""**StandardScaler to Age and One Hot Encode to other features**"""

col_names = ['Age']
features = data[col_names]
scaler = StandardScaler().fit(features.values)
features = scaler.transform(features.values)
data[col_names] = features

one_hot = pd.get_dummies(data['Shape'])
data = data.drop('Shape',axis = 1)
data = data.join(one_hot)
data = data.rename(columns={1.0: "Shape_1", 2.0: "Shape_2", 3.0: "Shape_3", 4.0: "Shape_4"})

one_hot = pd.get_dummies(data['Margin'])
data = data.drop('Margin',axis = 1)
data = data.join(one_hot)
data = data.rename(columns={1.0: "Margin_1", 2.0: "Margin_2", 3.0: "Margin_3", 4.0: "Margin_4", 5.0: "Margin_5"})

one_hot = pd.get_dummies(data['Density'])
data = data.drop('Density',axis = 1)
data = data.join(one_hot)
data = data.rename(columns={1.0: "Density_1", 2.0: "Density_2", 3.0: "Density_3", 4.0: "Density_4"})


data

"""## Train Test Split

**Create training and testing sets of the data**
"""

X = data.drop('Severity',axis=1).to_numpy()
y = data['Severity'].to_numpy()

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.30)
data

np.info(X_train)
print("---")
np.info(X_test)
print("---")
np.info(y_train)
print("---")
np.info(y_test)

"""## Neural Networks & Genetic Algorithms"""

# Function that builds the ANN model
def buildModel(hidden_layers, nodes_per_layer, activation_fn, optimizer, lr, loss_fn, metrics, inputs=14):
    model = Sequential()
    #add input layer
    model.add(Dense(inputs, activation="sigmoid", input_shape=(inputs,)))

    #add hidden layers    
    for i in range(int(hidden_layers)):
        model.add(Dense(int(nodes_per_layer), activation=activation_fn))

    #add output layer
    model.add(Dense(1,activation="sigmoid"))
   

    
    if(optimizer=='SGD'): optimizer = gradient_descent_v2.SGD(learning_rate=lr)
    elif(optimizer=='RMSprop'): optimizer = rmsprop_v2.RMSprop(learning_rate=lr)
    elif(optimizer=='Adam'): optimizer = adam_v2.Adam(learning_rate=lr)

    #compile model
    model.compile(optimizer, loss=loss_fn, metrics=metrics)

    return model

# Function that performs a prediction for the model
def evaluatePredictions(model, input_attributes, labels):
    predicted = model.predict(input_attributes)
    

    LP = roundPredictions(predicted)
    f = fbeta_score(labels, LP, beta=2.0)
    accuracy = accuracy_score(labels, LP)
    recall = recall_score(labels, LP, average=None)
    precision = precision_score(labels, LP, average=None)
    
    return accuracy, recall[0], precision[0], recall[1], precision[1],f

    
#Function that creates the initial population
#parameters=[hidden_layers,nodes_per_layer,activation_fn,learning_rate,optimizer,loss_fn]
def create_new_population():
    
    population=[]
    
    for i in range(10):
        cromo=[]
        cromo.append(np.random.randint(low=1, high=13))
        cromo.append(np.random.choice([1, 2, 4, 8, 16, 32, 64, 128]))
        cromo.append(np.random.randint(low=0, high=6))
        cromo.append(np.random.choice([0.001, 0.01, 0.1]))
        cromo.append(np.random.randint(low=0, high=3))
        cromo.append(np.random.randint(low=0, high=3))
        population.append(cromo)
        
    return np.array(population)

#Generic function that updates classifier arguments
#parameters=[hidden_layers,nodes_per_layer,activation_fn,learning_rate,optimizer,loss_fn]
def update_model_parameters(parameters):
    
    if((parameters[2]) == 0): a_f = 'relu'
    if((parameters[2]) == 1): a_f = 'selu'
    if((parameters[2]) == 2): a_f = 'sigmoid'
    if((parameters[2]) == 3): a_f = 'tanh'
    if((parameters[2]) == 4): a_f = 'linear'
    if((parameters[2]) == 5): a_f = 'softmax'
        
        
    if((parameters[4]) == 0): opt_f = 'SGD'
    if((parameters[4]) == 1): opt_f = 'RMSprop'
    if((parameters[4]) == 2): opt_f = 'Adam'
        
    if((parameters[5]) == 0): loss = 'binary_crossentropy'
    if((parameters[5]) == 1): loss = 'hinge'
    if((parameters[5]) == 2): loss = 'squared_hinge'
        
    model = buildModel(parameters[0], parameters[1], a_f, opt_f, parameters[3], loss, metrics=['accuracy'])

    return model

def select_mating_pool(pop, fitness, parents_fitness, num_parents):
    # Selecting the best individuals in the current generation as parents for producing the offspring of the next generation.
    parents = np.empty((num_parents, pop.shape[1]))
    parents_fitness = []
    for parent_num in range(num_parents):
        #save fitness values of best parents
        parents_fitness.append(np.max(fitness))
        #save best parents
        max_fitness_idx = np.where(fitness == np.max(fitness))
        max_fitness_idx = max_fitness_idx[0][0]
        parents[parent_num, :] = pop[max_fitness_idx, :]
        fitness[max_fitness_idx] = -99999999999
        
    return parents, parents_fitness

def crossover(parents, offspring_size):
    offspring = np.empty(offspring_size)
    # The point at which crossover takes place between two parents. Usually it is at the center.
    crossover_point = np.uint8(offspring_size[1]/2)

    for k in range(offspring_size[0]):
        # Index of the first parent to mate.
        parent1_idx = k%parents.shape[0]
        # Index of the second parent to mate.
        parent2_idx = (k+1)%parents.shape[0]
        # The new offspring will have its first half of its genes taken from the first parent.
        offspring[k, 0:crossover_point] = parents[parent1_idx, 0:crossover_point]
        # The new offspring will have its second half of its genes taken from the second parent.
        offspring[k, crossover_point:] = parents[parent2_idx, crossover_point:]
    return offspring

def mutation(offspring_crossover):
    # Mutation changes a single gene in each offspring randomly.
    for idx in range(offspring_crossover.shape[0]):
        
        # Select which gene to mutate
        select_gene = np.random.randint(low=0, high=6)
 
        if(select_gene == 0):
            #num_hidden_layers mutation
            random_value = np.random.randint(low=1, high=13)
            offspring_crossover[idx,0] = random_value
        if(select_gene == 1):
            #num_nodes_per_layer mutation
            random_value = np.random.choice([4, 8, 16, 32, 64, 128])
            offspring_crossover[idx,1] = random_value
        if(select_gene == 2):
            #activation function mutation
            random_value = np.random.randint(low=0, high=6)
            offspring_crossover[idx,2] = random_value
        if(select_gene == 3):
            #learning rate mutation
            random_value = np.random.choice([0.001, 0.01, 0.1])
            offspring_crossover[idx,3] = random_value
        if(select_gene == 4):
            #optimizer mutation
            random_value = np.random.randint(low=0, high=3)
            offspring_crossover[idx,4] = random_value
        if(select_gene == 5):
            #loss function mutation
            random_value = np.random.randint(low=0, high=3)
            offspring_crossover[idx,5] = random_value
            
    return offspring_crossover

def printChromo(chromo, tab=False):
    
    identation = "\t" if tab else ""
    
    if((chromo[2]) == 0): a_f = 'relu'
    if((chromo[2]) == 1): a_f = 'selu'
    if((chromo[2]) == 2): a_f = 'sigmoid'
    if((chromo[2]) == 3): a_f = 'tanh'
    if((chromo[2]) == 4): a_f = 'linear'
    if((chromo[2]) == 5): a_f = 'softmax'
        
        
    if((chromo[4]) == 0): opt_f = 'SGD'
    if((chromo[4]) == 1): opt_f = 'RMSprop'
    if((chromo[4]) == 2): opt_f = 'Adam'
        
    if((chromo[5]) == 0): loss = 'binary_crossentropy'
    if((chromo[5]) == 1): loss = 'hinge'
    if((chromo[5]) == 2): loss = 'squared_hinge'
        
    print(identation + "Layers: {} |".format(int(chromo[0])),"Nodes: {} |".format(int(chromo[1])),"Act_F: {} |".format(a_f),"Opti: {} |".format(opt_f), "LR: {} |".format(chromo[3]),"Loss: {}".format(loss))
    
def printChromos(chromos, tab=False):
    for chromo in chromos:
        printChromo(chromo, tab)
    
def roundPredictions(predicted):
    # Rounded to 0 or 1 as a binary output is intended
    LP = []
    f = lambda x: int(round(x))
    vfunc = np.vectorize(f)
    
    for prev in predicted:
        prev = vfunc(prev)
        LP.append(prev)
    
    return LP

"""**K-Fold Cross Validation**"""

from sklearn.model_selection import KFold

num_folds = 10

# Define the K-fold Cross Validator
kfold = KFold(n_splits=num_folds, shuffle=True)

"""**Keras ANN built from specific parameters (one specific chromosome)**"""

def evaluateChromosome(chromosome):
    scores=[]
    recalls_0=[]
    precisions_0=[]
    recalls_1=[]
    precisions_1=[]
    fbeta_1 = []
    
    model = update_model_parameters(chromosome)
    
    fold_no=1
    
    for train, test in kfold.split(X_train, y_train):

        history = model.fit(X_train[train], y_train[train],
              epochs=50,
              batch_size=64,
              verbose=0)

        score = model.evaluate(X_train[test], y_train[test], batch_size=64, verbose=0)      
        accuracy, recall_0, precision_0, recall_1, precision_1, fbeta = evaluatePredictions(model, X_train[test], y_train[test])

        #Adding all metrics to arrays
        scores.append(score[1])
        recalls_0.append(recall_0)
        precisions_0.append(precision_0)
        recalls_1.append(recall_1)
        precisions_1.append(precision_1)
        fbeta_1.append(fbeta)
    
        fold_no+=1
    
    score = sum(scores)/len(scores)
    recall_0 = sum(recalls_0)/len(recalls_0)
    precision_0 = sum(precisions_0)/len(precisions_0)
    recall_1 = sum(recalls_1)/len(recalls_1)
    precision_1 = sum(precisions_1)/len(precisions_1)
    fbeta_1 = sum(fbeta_1)/len(fbeta_1)


    return score, recall_0, precision_0, recall_1, precision_1, fbeta_1

population = create_new_population()
print("Initial population:")
printChromos(population, True)
num_parents_mating = 5
num_generations = 9
# number of genes for each chromosome
num_genes = 6
# number of chromosomes for each population
num_chromosomes = 10 

pop_size=(num_chromosomes,num_genes)

# fitness values for each chromosome for the current generation
fitness_values = []
# fitness vaalues for each chromosome of the last generation
last_fitness_values = []

gen = 0
cromo = 0

parents=[]
# Parents fitness so we do not repeat calculations on parents
parents_fitness = []

performances=[]
hiperparameters=[]


for generation in range(num_generations):
    gen+=1
    cromo = 0
    best_perf_per_gen = -1
    
    for chromosome in population:
        known=False
        cromo+=1
        score=-1
        parentNumber=0
        
        # If it's a known chromosome we dont need to train the ANN again
        # Skips the first generation because we didnt select the parents yet
        for savedCromo in parents:
            parentNumber+=1
            if (np.array_equal(chromosome,savedCromo)):
                score = parents_fitness[parentNumber-1]
                known = True
        
        # If it's a new chromosome we need to train the ANN in order to get the accuracy
        if (score < 0):
            accuracy, recall_0, precision_0, recall_1, precision_1, fbeta = evaluateChromosome(chromosome)
            #score = 0.5*accuracy + 0.225 *recall_1 + 0.15 *precision_0 + 0.1 * recall_0 + 0.025 * precision_1
            score = fbeta
            
        if(not known):
            print("Generation-{}".format(gen),"Chromosome-{}:".format(cromo))
            printChromo(chromosome, True)
            print("\tScore {:.2f}".format(score)," || Acc: {:.2f}".format(accuracy),"|R0: {:.2f} ".format(recall_0),"|P0: {:.2f} ".format(precision_0), "|R1: {:.2f} ".format(recall_1),"|P1: {:.2f} ".format(precision_1))
        else:
            print("Generation-{}".format(gen),"Chromosome-{}".format(cromo),"scored {:.2f}".format(score), " (Chromosome already knowned)")

        
        # Keep the scores in fitness_values
        fitness_values.append(score)
        
        # Getting the best hyperparameters per generation to check the evolution at the end
        if(best_perf_per_gen < score):
            best_perf_per_gen = score
            best_cromo_per_gen = chromosome
                   
    performances.append(best_perf_per_gen)
    hiperparameters.append(best_cromo_per_gen)
   
    #print(performances,"Best accuracies of each generation")
    #print(hiperparameters,"Best of each generation")
    
    # We store last generation in other array because fitness_values is changed by the select_mating_pool
    if(gen == num_generations):
        for i in fitness_values:
            last_fitness_values.append(i)
        print(last_fitness_values,"Last Fitness Values")
    
    parents,parents_fitness = select_mating_pool(population,fitness_values,parents_fitness,num_parents_mating)

    # Generating next generation using crossover.
    offspring_crossover = crossover(parents,
                                        offspring_size=(pop_size[0]-parents.shape[0], num_genes))

    # Adding some variations to the offspring using mutation.
    offspring_mutation = mutation(offspring_crossover)

    # Creating the new population based on the parents and offspring.
    population[0:parents.shape[0], :] = parents
    population[parents.shape[0]:, :] = offspring_mutation
    
    # Reset fitness_values
    fitness_values=[]

# Getting the best solution
best_solution = population[last_fitness_values.index(np.max(last_fitness_values))]
print("The best hyperparameters obtained are:")
printChromo(best_solution, True)
print("with a score of",np.max(last_fitness_values))

generations=[1,2,3,4,5,6,7,,8,9]
plt.plot(generations,performances,color='g')
plt.xlabel('Generations')
plt.xticks([1,2,3,4,5,6,7,8,9])
plt.ylabel('Accuracy')
plt.title('Accuracy improvement through generations')
plt.show()

"""### Analisys of parameters select by GA"""

model = update_model_parameters(chromosome)

    
history = model.fit(X_test, y_test, validation_split=0.45, epochs=50, batch_size=64, verbose=0)


# Visualize history
# Plot history: Loss
plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('Validation loss history')
plt.ylabel('Loss value')
plt.xlabel('No. epoch')
plt.legend(['train', 'test'], loc='upper left')
plt.show()

# Plot history: Accuracy
plt.plot(history.history['accuracy'])
plt.plot(history.history['val_accuracy'])
plt.title('Validation accuracy history')
plt.ylabel('Accuracy value (%)')
plt.xlabel('No. epoch')
plt.legend(['train', 'test'], loc='upper left')
plt.show()

score = model.evaluate(X_test, y_test, batch_size=64, verbose=0)      
accuracy, recall_0, precision_0, recall_1, precision_1,fbeta = evaluatePredictions(model, X_test, y_test)

predicted = model.predict(X_test)

y_pred = roundPredictions(predicted)

        
target_names = ['Benign', 'Malignant']
print(fbeta)
print(classification_report(y_test, y_pred, target_names=target_names))

tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()

print("True Positives: " +str(tp))
print("True Negatives: " +str(tn))
print("False Positives: " +str(fp))
print("False Negatives: " +str(fn))

