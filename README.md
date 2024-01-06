# Welcome to NortecTools
This is planned to be a simple web-application with various tools used with my charging provider Nortec.

The web-app is currently running for my personal use, and can be demoed at https://ladepris.znk.dk/

## Current features:
* The electricity price used by Nortec/Vivabolig (4 hour average full price + 0.74kr/kWh) is fetched, calculated and displayed in a bar graph.
* The next cheapest price of the day (elapsed prices are not considered) and the cheapest price of tomorrow is displayed.
* Pricedata is cached as to make the website more efficient; it is fetched up to once per day. The chart is also cached and is plotted up to once per hour.
  * When pricedata is no longer valid, the invalid data is discarded and new data is fetched the next time the website is visited.
  * The same for the chart, when the current hour is no longer current, a new graph is plotted.
* The graph and data is hosted on a very simple Flask-application using HTML/CSS

## Future goals:
* A page using API-data from companies like Carnot to provide an indicative price forecast for the next (2,3,4,5?) days
* A page that uses API-functions to connect to Nortecs backend in order to control the charging with features like:
  * Delay the start of charging to some given time
  * Stop the charging, when the car has charged a given amount of kWh
  * Use calculations to stop the charging at a given battery charge %
