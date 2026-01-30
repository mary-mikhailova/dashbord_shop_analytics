import configparser
import os
import pandas as pd
from faker import Faker
import random
from datetime import datetime as DT
from datetime import timedelta
import string

dirname = os.path.dirname(__file__)

config = configparser.ConfigParser()
with open(os.path.join(dirname, "config.ini"), 'r', encoding='utf-8') as f:
    config.read_file(f)

DATA_FOLDER = config['Files']['DATA_FOLDER']
dirname_generated_data = os.path.join(dirname, DATA_FOLDER)

if not os.path.exists(dirname_generated_data):
    os.makedirs(dirname_generated_data)

ITEMS_BY_CATEGORY = eval(config['Items_by_categoty']['ITEMS_BY_CATEGORY'])
CATEGOTY_SUPPLIERS = eval(config['Сategoty_Suppliers']['CATEGOTY_SUPPLIERS'])
SHOP_CITY = eval(config['Shop_city']['SHOP_CITY'])

fake = Faker("ru_RU")

def generate_goods():
    goods = []
    for key, values in ITEMS_BY_CATEGORY.items():
        for value in values:
            goods.append({"Category": key, "Item": value})
    
    df = pd.DataFrame(goods)
    df.to_csv(os.path.join(dirname_generated_data, f'Товары.csv'), index=False, encoding='utf-8')
    return df

def generate_suppliers():
    suppliers = []
    used_ids = set()  # Множество для отслеживания уникальных идентификаторов

    for category, suppliers_list in CATEGOTY_SUPPLIERS.items():
        for supplier_name in suppliers_list:
            # Генерация уникального supplier_id
            supplier_id = random.randint(100, 1000)
            while supplier_id in used_ids:
                supplier_id = random.randint(100, 1000)
            used_ids.add(supplier_id)

            suppliers.append({
                "Supplier_id": supplier_id,
                "Supplier": supplier_name,
                "Category": category,
                "Contact_person": fake.name(),
                "Email": fake.company_email()
            })
    df = pd.DataFrame(suppliers)
    df.to_csv(os.path.join(dirname_generated_data, f'Поставщики.csv'), index=False, encoding='utf-8')
    return df


def generate_clients():
    clients = []

    # используем внутреннюю функцию, чтобы для каждого года делать отдельную генерация (предполагая, что со временем будет регистрироваться больше клиентов)
    def generate_clients_years(year_start_date, year_end_date, quantity):

        for i in range (quantity):
            nonlocal clients

            gender = random.choice(["Male", "Female"])

            card = ''.join(random.choices(string.digits, k=20))

            if gender == "Male":
                fio = fake.name_male()
            else:
                fio = fake.name_female()

            date_reg = year_start_date + timedelta(random.randint(0, (year_end_date-year_start_date).days))

            clients.append({"Card number": card, 
                            "Date_Reg": date_reg, 
                            "Mail": fake.email(), 
                            "Phone": fake.phone_number(), 
                            "FIO": fio, 
                            "Gender": gender, 
                            "City": fake.city()})
            
    generate_clients_years(DT.strptime('2024.01.01', '%Y.%m.%d'), DT.strptime('2024.12.31', '%Y.%m.%d'), 100)
    generate_clients_years(DT.strptime('2025.01.01', '%Y.%m.%d'), DT.strptime('2025.12.31', '%Y.%m.%d'), 160)
    
    df = pd.DataFrame(clients)
    df.to_csv(os.path.join(dirname_generated_data, f'Клиенты.csv'), index=False, encoding='utf-8')
    return df


def generate_shops(quantity=10):
    shops = []
    for i in range(quantity):
        #на уровне SQL будет стоять ограничение на уникальность shop_id
        shops.append({"Shop_id": random.randint(1000, 2000), "City": random.choice(SHOP_CITY), "Format": random.choice(["Гипермаркет", "У дома"])})

    df = pd.DataFrame(shops)
    df.to_csv(os.path.join(dirname_generated_data, f'Магазины.csv'), index=False, encoding='utf-8')
    return df

goods = generate_goods()  
clients = generate_clients()
shops = generate_shops()
suppliers = generate_suppliers()

start_date = DT.strptime('2024.01.01', '%Y.%m.%d')
end_date = DT.strptime('2025.12.31', '%Y.%m.%d')
days_range = pd.date_range(start_date,end_date, freq='D').to_list()
                           
def generate_csv_files(shops):
    shop_id_list = []

    # для каждого магазина и мд
    for _, shop in shops.iterrows():
        shop_id = shop["Shop_id"]
        # для каждого дня анализируемого переиода
        for day in days_range:

            #определение дня недели
            weekday = day.weekday()

            #определение количества чеков и позиций в зависимости от дня недели
            if weekday < 5: #в будни меньше
                checks_per_day = random.randint(1,10)
                items_per_checks = random.randint(5,10)
            else: #в выходной больше
                checks_per_day = random.randint(10,20)
                items_per_checks = random.randint(6,15)

            # ограничим начало и конец рабочего дня
            start_of_day = day + timedelta(hours=10)  # 7 утра
            end_of_day = day + timedelta(hours=23) - timedelta(seconds=1)  # 11 вечера

            #для каждого чека
            for chek in range (1, checks_per_day):
                client_card = None  # Инициализация переменной
                #генерация уже существующей карты клиента (из df clients)
                #из предположения, что 40% будут не авторизированы (покупка без карты лояльности)
                if random.random()<0.4:
                    client_card = None
                else:
                    eligible_clients = clients[clients["Date_Reg"] <= day]
    #если у выбранного покупателя дата рагистарации позже покупки (что невозможно) - не вносим его в генерацию
                    if not eligible_clients.empty:

                        client = eligible_clients.sample(n=1).iloc[0]
                        client_card = client["Card number"]


                #генерация намера чека из букв и цифр  
                chek_numder = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))

                random_seconds = random.randint(0, int((end_of_day-start_of_day).total_seconds()))
                random_time_of_day = start_of_day + timedelta(seconds=random_seconds)

                for line_num in range (1, items_per_checks):
                    #если в чеке будет несколько позиций, предположим, что они пробиваются с интервалом в 2 секунды
                    dt = (random_time_of_day + timedelta(seconds=2 * line_num)).strftime('%Y-%m-%d %H:%M:%S')
                    #категрия и тип товара выбираются из усталонвленного в сети магазинов ассортимента (в конфиге)
                    category = random.choice(list(ITEMS_BY_CATEGORY.keys()))
                    item = random.choice(list(ITEMS_BY_CATEGORY[category]))
                    
                    supplier_ids = suppliers[suppliers["Category"] == category]["Supplier_id"].values
                    if len(supplier_ids) > 0:
                        supplier_id = random.choice(supplier_ids)
                    else:
                        supplier_id = None

                    amount = random.randint(1,10)

                    #у каждого продукта генерируется цена из установленной ценовой категории
                    if category == 'бытовая химия':
                        price_per_unit = round(random.uniform(100, 500),2)
                    elif category == 'текстиль':
                        price_per_unit = round(random.uniform(400, 4000),2)
                    elif category == 'посуда':
                        price_per_unit = round(random.uniform(300, 2000),2)
                    elif category == 'фрукты и овощи':
                        price_per_unit = round(random.uniform(50, 300),2)
                    elif category == 'молоко и молочные продукты':
                        price_per_unit = round(random.uniform(70, 250),2)
                    elif category == 'напитки и соки':
                        price_per_unit = round(random.uniform(100, 300),2)
                    elif category == 'заморозка':
                        price_per_unit = round(random.uniform(150, 1000),2)
                    
                    # генерация маржинальности и вычисление цены закупки
                    cost_per_unit = round(price_per_unit*random.uniform(0.66, 0.85),2)

                    #генерация скидки с предположением, что она не может быть больше 30% от стоимости единицы товара
                    discount = round(random.uniform(0.00, price_per_unit*0.3),2)
            
                    shop_id_list.append({"Shop_number": shop_id, "Check_number": chek_numder, "Card_number": client_card, "Day_time": dt, "Item": item, 
                                         "Quantity": amount, "Price_per_unit": price_per_unit, "Discount": discount, "Cost_per_unit": cost_per_unit, "Supplier_id": supplier_id})
    
    df = pd.DataFrame(shop_id_list)
    df.to_csv(os.path.join(dirname_generated_data, f'Продажи.csv'), index=False, encoding='utf-8')

print(generate_csv_files(shops))