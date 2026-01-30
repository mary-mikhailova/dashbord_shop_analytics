import os
import configparser
import re
import pandas as pd
import psycopg2

dirname = os.path.dirname(__file__)

config = configparser.ConfigParser()
file_path = os.path.join(dirname, "config.ini")

with open(file_path, 'r', encoding='utf-8') as file:
    config.read_file(file)

DATA_FOLDER = config['Files']['DATA_FOLDER']
DATABASE_CREDS = config['Database']

dirname_data = os.path.join(dirname, DATA_FOLDER)


conn = psycopg2.connect(
    host=DATABASE_CREDS['HOST'],
    port=DATABASE_CREDS['PORT'],
    database=DATABASE_CREDS['DATABASE'],
    user=DATABASE_CREDS['USER'],
    password=DATABASE_CREDS['PASSWORD']
)

cursor = conn.cursor()


def download_clients(df):
    for index, row in df.iterrows():
        query = """
        INSERT INTO clients (card, date_reg, client_email, client_phone, fio, gender, city)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        try:
            cursor.execute(query, (
                row['Card number'], row['Date_Reg'], row['Mail'], row['Phone'],
                row['FIO'], row['Gender'], row['City']
            ))
            conn.commit() 
        except psycopg2.Error as e:
            print(f"Ошибка при вставке данных: {e}")
            conn.rollback()

def download_shops(df):
    for index, row in df.iterrows():
        query = """
        INSERT INTO shops (shop_id, city, format)
        VALUES (%s, %s, %s)
        """
        try:
            cursor.execute(query, (
                row['Shop_id'], row['City'], row['Format']
            ))
            conn.commit() 
        except psycopg2.Error as e:
            print(f"Ошибка при вставке данных: {e}")
            conn.rollback()

def download_suppliers(df):
    for index, row in df.iterrows():
        query = """
        INSERT INTO suppliers (id, company_name, category, contact_person, company_email)
        VALUES (%s, %s, %s, %s, %s)
        """
        try:
            cursor.execute(query, (
                row['Supplier_id'], row['Supplier'], row['Category'], row['Contact_person'], row['Email']
            ))
            conn.commit() 
        except psycopg2.Error as e:
            print(f"Ошибка при вставке данных: {e}")
            conn.rollback()

def download_goods(df):
    for index, row in df.iterrows():
        query = """
        INSERT INTO goods (category, item)
        VALUES (%s, %s)
        """
        try:
            cursor.execute(query, (
                row['Category'], row['Item']
            ))
            conn.commit() 
        except psycopg2.Error as e:
            print(f"Ошибка при вставке данных: {e}")
            conn.rollback()

def download_sales(df):
    for index, row in df.iterrows():
        query = """
        INSERT INTO sales (shop_number, check_number, card_number, dt, item, quantity, price_per_unit, discount, cost_per_unit, supplier_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            cursor.execute(query, (
                row['Shop_number'], row['Check_number'], None if pd.isna(row['Card_number']) else row['Card_number'], row['Day_time'], row['Item'], row['Quantity'], row['Price_per_unit'], 
                row['Discount'], row['Cost_per_unit'], row['Supplier_id']
            ))
            conn.commit() 
        except psycopg2.Error as e:
            print(f"Ошибка при вставке данных: {e}")
            conn.rollback()


# Загрузка всех CSV-файлов в папке
filenames_in_order = ["Клиенты.csv", "Магазины.csv", "Поставщики.csv", "Товары.csv", "Продажи.csv"]

for filename in filenames_in_order:
    file_path = os.path.join(dirname_data, filename)

    if os.path.exists(file_path) and filename.endswith('.csv'):

        table_name = os.path.splitext(filename)[0].lower()

        if table_name == "клиенты":
            df = pd.read_csv(file_path)
            download_clients(df)
        elif table_name == "магазины":
            df = pd.read_csv(file_path)
            download_shops(df)
        elif table_name == "поставщики":
            df = pd.read_csv(file_path)
            download_suppliers(df)
        elif table_name == "товары":
            df = pd.read_csv(file_path)
            download_goods(df)
        elif table_name == "продажи":
            # Загрузка файла с продажами по частям
            for chunk in pd.read_csv(file_path, chunksize=5000):  # 5000 - это количество строк в одном куске
                download_sales(chunk) 



# Закрытие соединения
cursor.close()
conn.close()