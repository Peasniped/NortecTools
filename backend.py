from datetime import datetime, timedelta
import requests, os
import matplotlib.pyplot as plt
import numpy as np

def delete_old_pngs() -> None:
    try:
        files = os.listdir("static")
        for file in files:
            os.remove(f"static//{file}")
    except Exception as e:
        print("Exception using delete_old_pngs():", e)
        pass

class Tid:
    
    def __init__(self, timezone_offset:int = 0) -> None:
        self.timezone_offset = timezone_offset
        self.get_time()

    def get_time(self, output:bool = True) -> None|dict:
        """ Gets the current time of the device running the code, returns today(today's date), hour(current hour) and hour_next(current hour + 1) """
        now                = datetime.now() + timedelta(hours=self.timezone_offset)
        clock_time         = now.strftime("%H:%M")
        s_to_next_hr       = 3600 - (now.minute*60 + now.second)
        self.hour          = now.strftime("%H:00")
        self.hour_short    = int(str(self.hour[0:2]))
        self.hour_next     = (now + timedelta(hours=1)).strftime("%H:00")
        self.date          = now.date()
        self.date_tomorrow = self.date + timedelta(days=1)
        self.month         = self.date.month

        if output: return  {"now": now,
                            "clock_time": clock_time,
                            "s_to_next_hr": s_to_next_hr,
                            "hour_short": self.hour_short,
                            "hour_next": self.hour_next,
                            "date": self.date,
                            "date_tomorrow": self.date_tomorrow,
                            "month":self.month}

class Elpris:

    def __init__(self, tids_objekt:object = Tid()) -> None:
        self.tid = tids_objekt
        self.vat_rate = 0.25            # VAT
        self.price_elafgift = 0.871     # Electric fee (paid to the state)
        self.price_energinet = 0.140    # Energi-net fee (paid to the transmission net-company)
        self.price_electriccompany = 0  # Charge paid to the electric company
        self.tarif_lav = 0              # Transport fee paid to the transmission company in low load times
        self.tarif_hoj = 0              # Transport fee paid to the transmission company in high load times

    def fetch_raw_pricedata(self) -> list:
        """ Outputs a list with today's raw energy price in kr./kWh without VAT """
        date_today = self.tid.get_time()["date"]
        date_tomorrow = self.tid.get_time()["date_tomorrow"]

        URL=f"https://api.energidataservice.dk/dataset/Elspotprices?start={date_today}T00:00&end={date_tomorrow}T23:59&filter={{%22PriceArea%22:[%22DK1%22]}}"
        r = requests.get(URL)
        pricedata = r.json()
        pricedata_list = []

        for data in pricedata["records"]:
            hour = data["HourDK"]
            price = data["SpotPriceDKK"] / 1000
            pricedata_list.append([hour, price])
        pricedata_list.reverse()
        
        return pricedata_list

    def add_fees(self, price_raw, hour) -> float:
        """ Adds VAT, transporttarifs and other things """
        month = self.tid.get_time()["month"]
        price_vat = price_raw * self.vat_rate                # Adds VAT to raw electric price
        if 17 <= hour <= 21 and ( 1 <= month <= 3 or 10 <= month <= 12 ): # Adds the transport tarif (paid to the transmission net-company)
            price_tarif = self.tarif_hoj
        else:
            price_tarif = self.tarif_lav
        price_total = (price_raw + price_vat + price_tarif + self.price_elafgift + self.price_energinet + self.price_electriccompany)
        return price_total
    
    def get_pricedata(self) -> float:
        """ Calls functions and returns the prices for each hour today and add fees and extras """
        raw_prices = self.fetch_raw_pricedata()
        price_list = []

        for price in raw_prices:
            hour = int(price[0][11:13])
            raw_price = price[1]
            total_price = self.add_fees(raw_price, hour)
            price_list.append([hour, total_price])

        return price_list

class Ladepris:

    def __init__(self, tids_objekt:object = Tid()) -> None:
        self.nortec_cost = 0.74
        self.tid = tids_objekt
        self.hour_marker_expiry = None
        self.pricedata_expiry = None
        self.pricedata = None
        self.pricedata_date = None
        self.img_filename = None

    def check_data_expired(self, debug:bool = False) -> None:
        time_dict  = self.tid.get_time() 
        now        = time_dict["now"]
        hour_short = time_dict["hour_short"]

        date_today = datetime(now.year, now.month, now.day)
        date_data = datetime(self.pricedata_date.year, self.pricedata_date.month, self.pricedata_date.day) if self.pricedata_date is not None else None

        # Check if existing data is expired
        if self.pricedata_expiry == None or self.pricedata_expiry < now or self.pricedata == None or self.img_filename == None:
            self.pricedata = self.fetch_pricedata()
            self.pricedata_date = now
            delete_old_pngs()
            self.plot_graph()

            tomorrow = now.date() + timedelta(days=1)
            if hour_short >= 13: self.pricedata_expiry = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 13)
            else:                self.pricedata_expiry = datetime(now.year, now.month, now.day, 13)
            self.hour_marker_expiry = datetime(now.year, now.month, now.day, now.hour + 1)
            if debug: print(f"DEBUG: {self.tid.get_time()['now']} ::", "New data fetched, new graph plotted")

        # Check if existing hour-marker is expired
        elif self.hour_marker_expiry == None or self.hour_marker_expiry <= now:
            # Check if it is time to discard the "today"-data from yesterday
            if date_data is not None and date_today > date_data and len(self.pricedata) == 2:
                self.pricedata = self.pricedata[1:]
                if debug: print(f"DEBUG: {self.tid.get_time()['now']} ::", f"'today'-data from yesterday discarded. Pricedata now has length {len(self.pricedata)}")

            delete_old_pngs()
            self.plot_graph()

            self.hour_marker_expiry = datetime(now.year, now.month, now.day, now.hour + 1)
            if debug: print(f"DEBUG: {self.tid.get_time()['now']} ::", "Data not expired, new graph plotted")
        
        elif debug:
            print(f"DEBUG: {self.tid.get_time()['now']} ::", ": No data expired")
            print("     >> Data expiry:", self.pricedata_expiry, "-- Hour expiry:", self.hour_marker_expiry)

    def fetch_pricedata(self) -> tuple:
        data = Elpris(tids_objekt=self.tid).get_pricedata()
        if   len(data) == 24: pre_release = True
        elif len(data) == 48: pre_release = False
        else: raise ValueError(f"The length of the pricedata in variable \"data\" is {len(data)}, which is not a valid length. Accepted lengths: 24 or 48")
        
        data_today = data[0:24] if pre_release else data[0:27]
        data_tomorrow = data[24:48] if not pre_release else [None]

        def apply_four_hour_avg(pricelist, from_hour, hours = 4) -> float:
            sum = 0
            for hour_inc in range(hours):
                hour = from_hour + hour_inc
                price = pricelist[hour][1]
                sum += price
            average = sum / hours
            return round(average + self.nortec_cost, 2)
        
        def format_price_list(list):
            extended = False if len(list) > 24 else True
            charge_prices = []
            
            for price in list:
                if extended and price[0] > 20: break
                if not extended and len(charge_prices) > 23: break
                charge_price = apply_four_hour_avg(list, price[0])
                if not charge_price == 0:
                    charge_prices.append([price[0], charge_price])
            return charge_prices

        data_today = format_price_list(data_today)
        if not data_tomorrow == [None]:
            data_tomorrow = format_price_list(data_tomorrow)
            return (data_today, data_tomorrow)
        else: return (data_today,)

    def plot_graph(self) -> None:
        def extend_list_with_zeroes(list:list, prepend:bool, target_length:int = 24) -> list:
            item_delta = target_length - len(list)
            for i in range(item_delta):
                if prepend: list = [0] + list
                else:       list.append(0)
            return list

        def plot(charge_prices_today, charge_prices_tomorrow) -> None:
            if not len(charge_prices_today) == 24:
                raise ValueError(f"The length of the charge_prices in variable \"charge_prices_today\" is {len(charge_prices_today)}, valid length is 24.")
            elif charge_prices_tomorrow is not None and not len(charge_prices_tomorrow) == 24:
                raise ValueError(f"The length of the charge_prices in variable \"charge_prices_tomorrow\" is {len(charge_prices_tomorrow)}, valid length is 24.")

            time_dict      = self.tid.get_time()
            date           = time_dict["date"]
            time           = time_dict["clock_time"]
            hour_short     = time_dict["hour_short"]
            pricedata_date = self.pricedata_date.strftime("%Y-%m-%d %H:%M")

            tomorrow = False if charge_prices_tomorrow == None else True
            hours = [x[0] for x in charge_prices_today]
            prices_today_elapsed = [x[1] for x in charge_prices_today if x[0] < hour_short]
            prices_today_elapsed = extend_list_with_zeroes(prices_today_elapsed, prepend=False)
            prices_today_now = [charge_prices_today[hour_short][1]]
            prices_today_now = extend_list_with_zeroes(prices_today_now, prepend=True, target_length=hour_short+1)
            prices_today_now = extend_list_with_zeroes(prices_today_now, prepend=False)
            prices_today = [x[1] for x in charge_prices_today if x[0] > hour_short]
            prices_today = extend_list_with_zeroes(prices_today, prepend=True)
            if tomorrow: prices_tomorrow = [x[1] for x in charge_prices_tomorrow]
            
            if tomorrow: y_vals = [x for x in prices_today_elapsed + prices_today_now + prices_today + prices_tomorrow if x > 0]
            else:        y_vals = [x for x in prices_today_elapsed + prices_today_now + prices_today if x > 0]
            y_min = min(y_vals) * 0.95
            y_max = max(y_vals) * 1.043
            box_height = y_max * 0.995

            bar_width = 0.4
            hours = np.arange(len(hours))
            
            plt.figure(figsize=(10,8))
            if tomorrow:
                bar_offset = -bar_width/2
                plt.bar(hours - bar_width/2, prices_today_elapsed, bar_width, color="gainsboro")
                plt.bar(hours - bar_width/2, prices_today_now,     bar_width, color="red",        label="Ladepris nu")
                plt.bar(hours - bar_width/2, prices_today,         bar_width, color="royalblue",  label="Ladepris i dag")
                plt.bar(hours + bar_width/2, prices_tomorrow,      bar_width, color="royalblue",  label="Ladepris i morgen", alpha=0.4, hatch="///")
            else: 
                bar_offset = 0
                plt.bar(hours, prices_today_elapsed, bar_width, color="silver")
                plt.bar(hours, prices_today_now,     bar_width, label="Ladepris nu", color="red")
                plt.bar(hours, prices_today,         bar_width, label="Ladepris i dag")
            plt.ylim(bottom=y_min, top=y_max)
            plt.xlabel("Time hvori opladning påbegyndes")
            plt.xticks(hours)
            plt.ylabel("kr./kWh for hele opladningen")
            plt.title(f"Ladepris for Nortec-stander i N1-serviceområde")
            plt.legend(loc = "upper right")
            plt.text(-1.0 + bar_offset, box_height, f"Data hentet: {pricedata_date}\nData plottet: {date} {time}", ha="left", va="top", fontsize=10, bbox=dict(boxstyle = "round", facecolor="white", edgecolor="lightgrey", alpha=1))
            
            # Find the lowest price of the day and render in textbox
            prices_today = [x for x in prices_today_now + prices_today if x > 0]
            index_min_today = prices_today.index(min(prices_today))
            if tomorrow:
                prices_tomorrow = [x for x in prices_tomorrow if x > 0]
                index_min_tomorrow = prices_tomorrow.index(min(prices_tomorrow))
                plt.text(6.9 + bar_offset, box_height, f"Billigst i dag:       {prices_today[index_min_today]} kr./kWh @ {index_min_today+hour_short}:00\nBilligst i morgen: {prices_tomorrow[index_min_tomorrow]} kr./kWh @ {index_min_tomorrow}:00", ha="left", va="top", fontsize=10, bbox=dict(boxstyle = "round", facecolor="white", edgecolor="lightgrey", alpha=1))
            else:    
                plt.text(6.7 + bar_offset, box_height, f"Billigst i dag: {prices_today[index_min_today]} kr./kWh @ {index_min_today+hour_short}:00", ha="left", va="top", fontsize=10, bbox=dict(boxstyle = "round", facecolor="white", edgecolor="lightgrey", alpha=1))

            self.img_filename = f"{date}-T{hour_short}.png"
            plt.savefig(f"static//{self.img_filename}")        

        if len(self.pricedata) == 1:
            today = self.pricedata[0] if len(self.pricedata[0]) == 24 else self.pricedata[0][0:24]
            for i in range(21, 24):
                today.append([i, 0])
            plot(today, None)

        elif len(self.pricedata) == 2:
            today = self.pricedata[0] if len(self.pricedata[0]) == 24 else self.pricedata[0][0:24]
            tomorrow = self.pricedata[1] if len(self.pricedata[1]) == 24 else self.pricedata[1][0:24]
            for i in range(21, 24):
                tomorrow.append([i, 0])
            plot(today, tomorrow)
        
        else: raise Exception(f"Something is wrong with the length of the pricedata. Length is {len(self.pricedata)}. Valid lengths are 1 and 2")

if __name__ == "__main__":
    Ladepris().check_data_expired(debug=True)