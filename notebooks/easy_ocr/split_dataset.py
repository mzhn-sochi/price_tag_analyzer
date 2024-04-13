import pandas as pd
import os
import shutil
from sklearn.model_selection import train_test_split

# Load the dataset
df = pd.read_csv('output.csv')

# Split the dataset into training and validation sets (80% training, 20% validation)
train_df, val_df = train_test_split(df, test_size=0.2, random_state=42)

# Create directories for the training and validation sets if they don't exist
train_dir = 'train_images'
val_dir = 'val_images'
os.makedirs(train_dir, exist_ok=True)
os.makedirs(val_dir, exist_ok=True)

# Function to copy images to the designated folder
def copy_images(dataframe, folder):
    for filename in dataframe['filename']:
        source = os.path.join('dataset', filename)
        destination = os.path.join(folder, filename)
        shutil.copy(source, destination)

# Copy images to the respective folders
copy_images(train_df, train_dir)
copy_images(val_df, val_dir)

# Save the new CSV files
train_df.to_csv('train_data.csv', index=False)
val_df.to_csv('val_data.csv', index=False)

print("Dataset split and files created successfully.")
