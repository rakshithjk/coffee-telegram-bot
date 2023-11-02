from bs4 import BeautifulSoup
import requests
from datetime import date, timedelta
import csv
import os
import matplotlib.pyplot as plt
import io

TELEGRAM_BOT_TOKEN = '6744365741:AAGU6MzaFI87wr1-o3M96iNVWs3XzXDGcpA'
TELEGRAM_CHAT_ID = '-1002056928323'
# List of CSV filenames
csv_filenames = [
    "arabica_cherry_prices.csv",
    "arabica_parchment_prices.csv",
    "black_pepper_prices.csv",
    "robusta_cherry_prices.csv",
    "robusta_parchment_prices.csv",
]


def get_data():
    # Send an HTTP GET request to the URL of the webpage
    today = date.today() - timedelta(days = 1)
    formatted_date = today.strftime("%d-%m-%Y")
    url = f"http://kirehalli.com/coffee-prices-karnataka-{formatted_date}/"
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content of the webpage
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all <h3> elements
        h3_elements = soup.find_all('h3')

        # Create a dictionary to store the data for each category
        category_data = {}

        # Iterate through the <h3> elements to extract the specific content
        for h3 in h3_elements:
            text = h3.get_text(strip=True)
            if ":Rs" in text:
                category_name = text.split(':')[0]
                price_string = text.split(':')[1].strip()
                # Extract and average the two values in the price_string
                price_values = [int(val.strip())
                                for val in price_string.replace('Rs', '').replace(' / 50KG', '').replace(' / KG', '').replace(' ', '').split('-')]
                average_price = sum(price_values) / len(price_values)
                category_data[category_name] = average_price

        final_message = f"Date: {formatted_date}\n"
        # Create separate files for each category and write the data
        for category, price in category_data.items():
            filename = f"{category.lower().replace(' ','_')}prices.csv"
            append_mode = os.path.exists(filename)
            with open(filename, "a" if append_mode else "w", newline='') as file:
                writer = csv.writer(file)
                # Write the data
                writer.writerow([formatted_date, category, price])

            # Send a telegram message with the price update
            final_message =final_message + f"{category} - {average_price} \n"
            plot_and_send_graph_wrapper(filename, category)

        send_telegram_message(final_message)
        print("Data written to files for each category and date.")
    else:
        print(f"Failed to fetch data from {url}")


def send_telegram_message(text_message):
    base_url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}'
    send_message_url = f'{base_url}/sendMessage'

    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': text_message,
    }

    response = requests.post(send_message_url, data=data)

    if response.status_code == 200:
        print("Message sent successfully.")
    else:
        print(f"Failed to send message. Status code: {response.status_code}")


def plot_and_send_graph_wrapper(filename, category):
    with open(filename, "r", newline='') as file:
        reader = csv.reader(file)
        last_5_records = []

        for row in reader:
            last_5_records.append(row)
            if len(last_5_records) > 5:
                last_5_records.pop(0)  # Keep only the last 5 records

        if last_5_records:
            plot_and_send_graph(category, last_5_records)


def plot_and_send_graph(category, data):
    dates = [row[0] for row in data]
    prices = [float(row[2].replace("Rs ", "").replace(
        ",", "").split("-")[0]) for row in data]

    plt.figure(figsize=(8, 4))
    plt.plot(dates, prices, marker='o')
    plt.title(f'{category} - Last 5 Records')
    plt.xlabel('Date')
    plt.ylabel('Average Price (Rs)')
    plt.grid(True)

    # Save the graph to a BytesIO object
    graph_buffer = io.BytesIO()
    plt.savefig(graph_buffer, format='png')
    graph_buffer.seek(0)

    # Send the graph as a photo
    send_graph_as_photo(category, graph_buffer)


def send_graph_as_photo(filename, graph_buffer):
    base_url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}'
    send_photo_url = f'{base_url}/sendPhoto'

    files = {'photo': ('graph.png', graph_buffer)}
    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'caption': f'Last 5 days trend {filename}',
    }

    response = requests.post(send_photo_url, data=data, files=files)
    if response.status_code == 200:
        print(f"Graph sent successfully for {filename}.")
    else:
        print(
            f"Failed to send graph for {filename}. Status code: {response.status_code}")


if __name__ == '__main__':
    get_data()