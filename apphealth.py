import streamlit as st
from pydantic import BaseModel
from datetime import date, datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import requests
from bs4 import BeautifulSoup
import os
import pandas as pd
import numpy as np

st.set_page_config(page_title="Здоров'я: щоденник і калькулятор", layout="wide")
st.markdown("""
    <style>
        .main {background-color: #F5F6FA;}
        h1, h2, h3 { color: #CC0000; }
        .stButton>button {background-color:#CC0000; color:white;}
    </style>
""", unsafe_allow_html=True)

class BMIInput(BaseModel):
    height_cm: float
    weight_kg: float

class BMIOutput(BaseModel):
    bmi: float
    status: str

def calculate_bmi(input: BMIInput) -> BMIOutput:
    bmi = input.weight_kg / ((input.height_cm / 100) ** 2)
    if bmi < 18.5:
        status = "Недостатня вага"
    elif bmi < 25:
        status = "Норма"
    elif bmi < 30:
        status = "Надмірна вага"
    else:
        status = "Ожиріння"
    return BMIOutput(bmi=round(bmi, 2), status=status)

CALORIE_TABLE = {
    "яблуко": 52,
    "хліб": 265,
    "молоко": 42,
    "яйце": 155,
}

def calculate_calories(product: str, grams: float) -> float:
    kcal_per_100 = CALORIE_TABLE.get(product.lower(), 0)
    calories = kcal_per_100 * grams / 100
    return round(calories, 2)

def save_entry(entry_date: date, weight: float, calories: float, notes: str) -> str:
    line = f"{entry_date},{weight},{calories},{notes}\n"
    with open("diary.csv", "a", encoding="utf-8") as f:
        f.write(line)
    return "Запис збережено!"

def plot_weight_progress(df):
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(df["Дата"], df["Вага (кг)"], marker="o", linestyle='-', color='#007ACC', linewidth=2, markersize=8, label="Вага")
    ax.fill_between(df["Дата"], df["Вага (кг)"], color='#A4D3F7', alpha=0.3)
    ax.set_title("Динаміка ваги", fontsize=18, fontweight='bold')
    ax.set_xlabel("Дата", fontsize=14)
    ax.set_ylabel("Вага (кг)", fontsize=14)
    ax.legend()
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.gcf().autofmt_xdate()
    st.pyplot(fig)

def plot_calories_progress(df):
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(df["Дата"], df["Калорії"], marker="s", color='orange', linewidth=2, markersize=7, label="Калорії")
    ax.set_title("Динаміка калорій", fontsize=16)
    ax.set_xlabel("Дата")
    ax.set_ylabel("Ккал")
    ax.legend()
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.gcf().autofmt_xdate()
    st.pyplot(fig)

def plot_weight_vs_calories(df):
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.scatter(df["Калорії"], df["Вага (кг)"], c=df["Дата"].dt.year, cmap='viridis', s=70)
    ax.set_title("Залежність ваги від калорій", fontsize=16)
    ax.set_xlabel("Калорії")
    ax.set_ylabel("Вага (кг)")
    st.pyplot(fig)

def get_calories_from_web(product: str) -> str:
    try:
        base_url = "https://www.tablycjakalorijnosti.com.ua/tablytsya-yizhyi"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        page = 1
        product_lower = product.lower()

        while True:
            url = f"{base_url}?page={page}"
            response = requests.get(url, headers=headers)
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.text, "html.parser")
            rows = soup.select("table tbody tr")

            if not rows:
                break  

            for row in rows:
                columns = row.find_all("td")
                if len(columns) >= 2:
                    name = columns[0].get_text(strip=True).lower()
                    if product_lower in name:
                        cal = columns[1].get_text(strip=True)
                        protein = columns[2].get_text(strip=True)
                        carbs = columns[3].get_text(strip=True)
                        fat = columns[4].get_text(strip=True)
                        fiber = columns[5].get_text(strip=True) if len(columns) > 5 else "—"
                        return (
                            f"Продукт: {name.capitalize()}\n"
                            f"Калорійність: {cal} ккал / 100 г\n"
                            f"Білки: {protein} г\n"
                            f"Вуглеводи: {carbs} г\n"
                            f"Жири: {fat} г\n"
                            f"Клітковина: {fiber} г"
                        )

            page += 1  

        return "Не знайдено інформації"
    except Exception as e:
        return f"Помилка при підключенні: {e}"

def show_and_download_diary():
    if not os.path.exists("diary.csv"):
        st.warning("Файл diary.csv не знайдено.")
        return
    try:
        df = pd.read_csv("diary.csv", header=None, names=["Дата", "Вага (кг)", "Калорії", "Примітки"])
        st.dataframe(df)
        with open("diary.csv", "rb") as f:
            st.download_button(
                label="Завантажити diary.csv",
                data=f,
                file_name="diary.csv",
                mime="text/csv"
            )
    except Exception as e:
        st.error(f"Помилка при читанні файлу: {e}")

st.markdown("<h1 style='text-align:center;'>Здоров'я: Ваш особистий калькулятор і щоденник </h1>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "ІМТ (BMI)",
    "Підрахунок калорій",
    "Додати запис в щоденник",
    "Графіки та статистика",
    "Калорії з web",
    "Завантажити щоденник",
])

with tab1:
    st.header("Калькулятор ІМТ (BMI)")
    col1, col2 = st.columns(2)
    with col1:
        height = st.number_input("Введіть зріст (см):", min_value=50.0, max_value=250.0, value=170.0)
    with col2:
        weight = st.number_input("Введіть вагу (кг):", min_value=10.0, max_value=300.0, value=65.0)
    if st.button("Розрахувати ІМТ"):
        input_data = BMIInput(height_cm=height, weight_kg=weight)
        result = calculate_bmi(input_data)
        st.success(f"Ваш ІМТ: {result.bmi} — {result.status}")
        if result.status == "Норма":
            st.balloons()
        elif result.status == "Ожиріння":
            st.warning("Зверніть увагу на раціон та фізичну активність!")

with tab2:
    st.header("Підрахунок калорій")
    col1, col2 = st.columns(2)
    with col1:
        product = st.selectbox("Продукт:", list(CALORIE_TABLE.keys()) + ["інше"])
    with col2:
        grams = st.number_input("Вага продукту (г)", min_value=0.0, max_value=1000.0, value=100.0)
    if st.button("Розрахувати калорійність"):
        if product != "інше":
            calories = calculate_calories(product, grams)
            st.info(f"Калорійність {grams} г {product}: {calories} ккал")
        else:
            st.info("Для інших продуктів скористайтесь пошуком у вкладці 'Калорії з web'.")

with tab3:
    st.header("Додати запис в щоденник")
    entry_date = st.date_input("Дата запису", value=date.today())
    weight_entry = st.number_input("Вага (кг)", min_value=10.0, max_value=300.0, value=65.0, key="weight_entry")
    calories_entry = st.number_input("Калорії (ккал)", min_value=0.0, max_value=10000.0, value=2000.0, key="calories_entry")
    notes = st.text_area("Примітки")
    if st.button("Зберегти запис"):
        msg = save_entry(entry_date, weight_entry, calories_entry, notes)
        st.success(msg)
        st.info("Дані записуються у файл diary.csv у цій папці.")

with tab4:
    st.header("📈 Графіки та статистика")
    if os.path.exists("diary.csv"):
        df = pd.read_csv("diary.csv", header=None, names=["Дата", "Вага (кг)", "Калорії", "Примітки"])
        df["Дата"] = pd.to_datetime(df["Дата"], errors="coerce")
        df = df.dropna(subset=["Дата"])
        df = df.sort_values("Дата")

        if not df.empty:
            # Метрики
            col1, col2, col3 = st.columns(3)
            col1.metric("Середня вага", f"{df['Вага (кг)'].mean():.2f} кг")
            col2.metric("Мінімальна вага", f"{df['Вага (кг)'].min():.2f} кг")
            col3.metric("Максимальна вага", f"{df['Вага (кг)'].max():.2f} кг")

            col4, col5, col6 = st.columns(3)
            col4.metric("Середні калорії", f"{df['Калорії'].mean():.0f} ккал")
            col5.metric("Мін. калорії", f"{df['Калорії'].min():.0f} ккал")
            col6.metric("Макс. калорії", f"{df['Калорії'].max():.0f} ккал")

            st.markdown("#### 📉 Графік ваги")
            plot_weight_progress(df)

            with st.expander("Динаміка калорій"):
                plot_calories_progress(df)

            with st.expander("Вага vs Калорії"):
                plot_weight_vs_calories(df)

            st.markdown("### 📝 Всі записи")
            st.dataframe(df)
        else:
            st.info("Ще не додано жодного запису.")
    else:
        st.info("Ще не додано жодного запису.")

with tab5:
    st.header("Пошук калорій з українського сайту")
    product_web = st.text_input("Продукт:")
    if st.button("Знайти калорії") and product_web:
        st.info("Йде пошук на tablycjakalorijnosti.com.ua ...")
        st.write(get_calories_from_web(product_web))

with tab6:
    st.header("Завантажити щоденник")
    show_and_download_diary()
