🌾 APMC Market Price & Farmer Information System

This project is a web-based platform that helps farmers and traders view APMC market prices, historical trends, seasonal insights, and agricultural news.
The system is built using Flask, HTML templates, and SQL databases.

The platform allows users to select a city and commodity to analyze price trends, helping them make better selling decisions.

📂 Project Structure
⚙️ Backend (Python Scripts)
📌 app.py

This is the main application file and the core of the system.
It runs a Flask web server that handles all website operations.

Key responsibilities:

Manages URL routing between pages

Processes user input such as city, commodity, and date range

Connects to the market databases

Fetches and processes price trend data

Sends processed data to the frontend templates for display

In simple terms, app.py controls how the entire website works.

📌 scrape_farmer_news.py

This script collects latest agricultural news from farming and market-related websites.

Main functions:

Scrapes headlines and article links

Extracts useful news for farmers

Stores or passes the news data to the website

This helps farmers stay informed about:

Crop price trends

Government policies

Agricultural updates

📌 check_db.py

This is a database testing and debugging tool.

Purpose:

Checks whether the database connection is working

Verifies that SQL queries return correct results

Helps developers debug issues with data loading

It ensures that market price data is correctly stored and accessible.

📌 .gitignore

This file tells Git which files should not be uploaded to the repository.

Examples of ignored files:

Cache files (__pycache__)

Temporary files

Environment files

Secret configuration keys

This keeps the repository clean and secure.

🖥️ Frontend (HTML Templates)

These templates create the user interface of the website.

🏠 home.html

The main landing page of the system.

Users can:

Select City

Choose Commodity

Define date range

This page acts as the starting point for market analysis.

🔐 login.html

Provides a login interface for users.

Purpose:

Authenticate users

Restrict access to system features if required.

📊 result.html

Displays the search results after a user selects city and commodity.

Shows:

Market price tables

Date-wise price data

Commodity statistics

📈 chart.html

A data visualization page that displays price trends in graph format.

Likely uses Chart.js to generate:

Price trend charts

Market comparisons

Visual analytics

📰 news.html

Displays agriculture and market news collected by the scraper.

Helps farmers stay updated with:

Market conditions

Farming policies

Agricultural developments

🌱 season.html

Provides seasonal market analysis.

Shows:

Best months to sell commodities

Year-to-year price comparison

Seasonal demand patterns

This helps farmers plan crop selling strategies.

📜 history.html

Displays historical market price data.

Users can review:

Past commodity prices

Long-term market trends

Historical price comparisons

🗄️ Database Files

These SQL files contain market price data for different APMC markets.

📍 apmc_ahmedabad.sql

Contains commodity price records for Ahmedabad APMC market.

📍 gondalmarket.sql

Stores market data from Gondal APMC including historical price records.

📍 market.sql

Acts as a general or combined database that may include:

Multiple city market data

Shared commodity information

Centralized market records

🎯 Project Purpose

The main objective of this system is to:

Provide real-time and historical market price information

Help farmers analyze trends before selling crops

Offer data visualization and seasonal insights

Keep farmers updated with agricultural news

This platform improves decision-making and market transparency for farmers and traders.
