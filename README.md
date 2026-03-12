# 🌾 APMC Market Price & Farmer Information System

A web-based platform that helps **farmers and traders analyze APMC market prices, historical trends, seasonal insights, and agricultural news**.

The system allows users to **select a city and commodity to view price trends**, helping farmers make **better selling decisions**.

---

🚀 Features

- 📊 View **APMC commodity price data**
- 📈 Analyze **historical price trends**
- 🌱 View **seasonal analysis of crops**
- 📰 Read **latest agricultural market news**
- 🏙️ Select **different APMC cities**
- 📉 Visualize data using **interactive charts**

---

🛠️ Technologies Used

- Backend: Python with **Flask**
- Frontend: HTML, CSS, JavaScript
- Charts: **Chart.js**
- Database: MySQL / SQL
- Web Scraping: Python (Requests / BeautifulSoup)

---

---

⚙️ Backend Files
📌 `app.py`
The **main application file** that runs the Flask web server.

Functions:
- Handles **page routing**
- Processes **user inputs**
- Connects to the **database**
- Fetches and processes **market price data**
- Sends data to the **HTML templates**

---

📌 `scrape_farmer_news.py`
A **web scraping script** that collects agricultural news from farming websites.

Functions:
- Scrapes **latest headlines**
- Extracts **article links**
- Provides **market updates for farmers**

---

📌 `check_db.py`
A **database debugging script** used to verify that the SQL database is working correctly.

Functions:
- Tests **database connection**
- Runs **sample queries**
- Helps debug **data loading issues**

---

📌 `.gitignore`
This file tells Git which files should **not be uploaded** to the repository.

Ignored files include:
- Cache files (`__pycache__`)
- Temporary files
- Environment variables
- Secret configuration files

---

🖥️ Frontend Templates

🏠 `home.html`
The **main landing page** where users can:
- Select **City**
- Choose **Commodity**
- Pick **date range**

---
🔐 `login.html`
Provides a **login interface** for authentication.

---

📊 `result.html`
Displays **market price results** including:
- Commodity price tables
- Date-wise price data

---
📈 `chart.html`
Displays **price trends using charts** created with **Chart.js**.

---
📰 `news.html`
Shows **latest agricultural news** collected by the scraper.

--
🌱 `season.html`
Displays **seasonal crop analysis**, including:
- Best selling months
- Year-over-year price comparisons
- Seasonal demand trends

---

📜 `history.html`
Shows **historical market data** for commodity prices.

---

 🗄️ Database Files

📍 `apmc_ahmedabad.sql`
Contains **APMC price data for Ahmedabad market**.

📍 `gondalmarket.sql`
Contains **price data for Gondal market**.

 📍 `market.sql`
A **general database** containing combined market data.

---

🎯 Project Objective

The main goal of this project is to:

- Provide **transparent APMC market price information**
- Help farmers **analyze trends before selling crops**
- Offer **visual insights through charts**
- Deliver **latest agricultural news updates**

This system improves **decision-making for farmers and traders** by making market data easy to access and understand.

---

📌 Future Improvements

- Add **more APMC markets**
- Implement **user accounts and dashboards**
- Provide **price prediction using machine learning**
- Add **mobile-friendly UI**

---

👨‍💻 Author

**Hardik Dabhi**

---

⭐ Support

If you like this project, consider **starring the repository on GitHub**.
