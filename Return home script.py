# -*- coding: utf-8 -*-
"""
Created on Mon Jan  9 12:33:37 2023

@author: mosiah
"""

# HTML URL modules
import re
import requests
from bs4 import BeautifulSoup
import numpy as np
from datetime import datetime

if(False):
    from tkinter import *
    root = Tk()
    root.geometry("1024x768")
    frame = Frame(root)
    frame.pack()
     
    leftframe = Frame(root)
    leftframe.pack(side=LEFT)
     
    rightframe = Frame(root)
    rightframe.pack(side=RIGHT)
     
    label = Label(frame, text = "Hello world")
    label.pack()
     
    button1 = Button(leftframe, text = "Button1")
    button1.pack(padx = 3, pady = 3)
    button2 = Button(rightframe, text = "Button2")
    button2.pack(padx = 3, pady = 3)
    button3 = Button(leftframe, text = "Button3")
    button3.pack(padx = 3, pady = 3)
     
    root.title("Test")
    root.mainloop()


def get_time():
    now = datetime.now()
    date, time = str(now).split(" ")
    print("date =", date)
    print("time =", time)

    # extract the hours and minutes from the daytime object
    hours, minutes, seconds = time.split(":")
    return date, hours, minutes


def convert24(time_array):
    
    t_24 = []
    for time in time_array:
        # print(time)
        hours, minutes_am_pm = time.split(":")
        am_pm = minutes_am_pm[-2:]
        minutes=minutes_am_pm[0:-2]
        #print(min_time)
       
        if (am_pm == "pm") or (am_pm == "PM"):
            if hours != "12":
                hours = str(int(hours) + 12)
        
        time_24_value = hours + ":" + minutes
        t_24.append(time_24_value)
    
    time_24 = np.asarray(t_24, dtype=object)
    return time_24

   
def convert_from_absolute(absolute_time):
    test_hour, test_min = divmod(absolute_time, 60)
    
    # AM/PM test
    pm = False
    if test_hour > 12:
        test_hour -= 12
        pm = True
    
    readable_time = f"{int(test_hour):2}:{int(test_min):02}"
    
    if pm:
        readable_time += "PM"
    else:
        readable_time += "AM"
    
    return readable_time
    

def create_time_table(time_array):
    """
    time_array is a list/array of 24 hour times formatted (05:07)
    An equally sized numpy array is generated to store the equivalent time
    value as an absolute number generated using 60*hours + minutes.
    The purpose is to have an array which we can quickly find the closest time
    to the current time.
    """
    
    # If time_array is multiline string, convert to list
    if isinstance(time_array, str):
        time_table = time_array.split(sep='\n')
    else:
        time_table = time_array
    
    
    empty_table = np.empty(len(time_table))
    index = 0
    while index < np.size(empty_table):
        hours, mins = time_table[index].split(":")
        absolute_time = (int(hours) * 60) + int(mins)
        empty_table[index] = absolute_time
        index += 1
    
    return empty_table
        

def get_absolute_time_arrays(*IDS, streetcars=False):
    absolute_time_arrays = []
    # print(str(streetcars))
    for ID in IDS:
        if streetcars:
            array_12_hour = get_streetcar_arrivals(ID)  
        else:
            array_12_hour = get_arrivals(ID)
        
        array_24_hour = convert24(array_12_hour)
        array_time_table = create_time_table(array_24_hour)
        absolute_time_arrays.append(array_time_table)
        
    return absolute_time_arrays


def make_trip_request(from_place=10767, to_place=11771, time="", return_time = False):
    # Url for example trip-planner request
    trip = ("https://developer.trimet.org/ws/V1/trips/tripplanner?"
    "fromPlace={}"   # Starting Location
    "&toPlace={}"    # Ending Location
    "&time={}"          # Specified time
    "&Arr=D"            # Arrival by (A) / Depart after (D)
    "&MaxItineraries=6" # Maximum number of options shown
    "&appID=5B1680B033D32C8D64A577CAA")     # Authentication
    if time != "":
        time = convert24([time])
    # Make the request to Trimet's trip-planner
    page = requests.get(trip.format(from_place, to_place, time))
    soup = BeautifulSoup(page.content, 'xml')  #alternatively, html.parser
    #print(soup.prettify())
    
    # Find all the potential options
    options = soup.find("itineraries").find_all("itinerary")
    end_times = []
    for item in options:
        print("\nOption", item.attrs["id"])
        schedule = item.find("time-distance")
        start_time = schedule.find("startTime")
        end_time = schedule.find("endTime")
        print("Departure time:", start_time.text)
        print("Arrival time:  ", end_time.text)
        if return_time:
            end_times.append(end_time.text)
    
    print("---")
    if return_time:
        return end_times


def next_arrivals(time_table, now_absolute=0):
    """
    Pass in numpy array (time_table)

    Parameters
    ----------
    time_table : TYPE
        DESCRIPTION.
    now_absolute : TYPE, optional
        DESCRIPTION. The default is 0.

    Returns
    -------
    readable_time_array : TYPE
        DESCRIPTION.

    """
    # convert total minutes to hour, min
    good_times = time_table[time_table > (now_absolute)]

    readable_time_array = np.empty(good_times.size, dtype=object)
    for index in range(len(good_times)):
        # print(arrival_time)
        readable_time_array[index] = convert_from_absolute(good_times[index])
    
    return readable_time_array


def get_streetcar_arrivals(stopID):
    # Base url for Trimet's stop schedule
    url = "https://trimet.org/ride/stop_schedule.html"
        
    # Using the stop ID passed in, get schedules sorted by destinations
    stop_url = "{}?stop_id={}&sort=time".format(url,stopID)
    
    page = requests.get(stop_url)
    soup = BeautifulSoup(page.content, 'html.parser')
   
    arrivalTimes = []
    streetcars = soup.select('ul.sortbytime')[0].select('b')
    for time in streetcars:
        # print(time.text)
        arrivalTimes.append(time.text)
        
    return np.array(arrivalTimes)


def get_arrivals(stopID):
    # Base url for Trimet's stop schedule
    url = "https://trimet.org/ride/stop_schedule.html"
        
    # Using the stop ID passed in, get schedules sorted by destinations
    stop_url = "{}?stop_id={}&sort=destination".format(url,stopID)
    
    page = requests.get(stop_url)
    soup = BeautifulSoup(page.content, 'html.parser')
   
    # Create top_items as empty list
    bus_lines = {}  # List of dictionaries for the buses passing through this stop

    # Extract and store in top_items according to instructions on the left
    schedules = soup.select('div.scheduletimes')
    for elem in schedules:
        info = {}   # The dictionary of an individual bus

        description = elem.select('h3')[0].text
        # format description to be more readable by removing long spaces, tabs, and newlines
        description = description.replace("\t", "").replace("\r", "").replace("\n", "")
        description = description.replace("                ", "").replace("Next arrivals", "")
        
        # Separate the line number away from the description
        descriptionParts = description.partition("-")
        info["ID"] = descriptionParts[0]
        info["Description"] = descriptionParts[2]
        
        buses = elem.select('ul.sortbydestination')
        arrivalTimes = [] # List to contain arrival times for this bus
        for bus in buses:
            arrivalTime = bus.select('span')
            for time in arrivalTime:
                arrivalTimes.append(time.text.strip())
            
        
        info["Arrivals"] = arrivalTimes[:]
        bus_lines[descriptionParts[0]] = info

    BusID = list(bus_lines.keys())
    if len(BusID) < 2:
        # Return list of arrival times as an array
        return np.array(bus_lines[BusID[0]]["Arrivals"])
    else:
        print("\nMultiple transportation services found!\n")
        for ID in BusID:
            print("ID:", bus_lines[ID]["ID"])
            print("Description:", bus_lines[ID]["Description"])
            print("Arrival Schedule:\n", bus_lines[ID]["Arrivals"])
            print("\n---\n")
        # Currently a stub which returns the busline dictionary
        # Consider asking the user which service they want to use
        return bus_lines
    


#### TO DO ####
"""
Give user more feedback and user friendly outputs regarding the travel time/options
Allow the user to input desired departure time and/or destinations based on stopid

Add an optional mode to request certain time to arrive on campus by
(duplicate this process but heading (from home to campus) instead)
"""
# Get streetcar times
FAB_building, Urban, Library = get_absolute_time_arrays(12382, 10764, 10767, streetcars=True)

# Get current time
date, hours, minutes = get_time()
now_absolute = 60*int(hours) + int(minutes)

# convert array of total minutes to hour, min
# and retrieve the scheduled arrivals based on current time
good_times = next_arrivals(FAB_building, now_absolute)

next_streetcar_arrivals = good_times[:3]
print("\nNext 3 streetcars arrive at: ")
for arrival in next_streetcar_arrivals:
    print(arrival)

print("\nIt takes 9 minutes to get to Central Library")

# Find earliest arrival times to Central library
# Average travel time is 9 minutes (add 1 for walking distance/cushion)
minutes = int(good_times[0][-4:-2]) + 10    # Add 10 minutes to first arrival
if minutes >= 60:
    minutes -= 60
    hours = str(int(hours)+1)

# Prepare a copy of adjusted time for trip-planner
time = str(hours) + ":" + str(minutes)

pm = False
if int(hours) > 12:
    hours = int(hours)
    hours -= 12
    pm = True

print(f"Earliest arrival at Central Library: {int(hours):2}:{int(minutes):02}", end="")
if pm:
    print("PM")
else:
    print("AM")

if(False):
    # Print out next 3 trips
    make_trip_request()


arrival_times = make_trip_request(10767, 10042, return_time=True)
earliest_arrival_destination = convert24([arrival_times[0]])
#print(earliest_arrival_destination)
# Get bus times
home_47, campus_47 = get_absolute_time_arrays(10042, 11770)
home_arrivals = next_arrivals(home_47[:], create_time_table(earliest_arrival_destination))
print("Remaining buses home")
for arrival in home_arrivals:
    print(arrival)
    
    
#############
# Resourses #
#############

"""
https://stackabuse.com/parsing-xml-with-beautifulsoup-in-python/
https://beautiful-soup-4.readthedocs.io/en/latest/#making-the-soup

https://developer.trimet.org/ws_docs/tripplanner_ws.shtml
11771: 45.520206,-122.917079
"""

# https://www.freecodecamp.org/news/url-encoded-characters-reference/#:~:text=There%20are%20only%20certain%20characters,that%20can%20have%20special%20meanings.
# %20 = ' ', %26 = '&', %3A = ':'

# https://developer.trimet.org/ws/V1/trips/tripplanner? # xml response
# https://trimet.org/home/planner-trip? # Website address

# Buildable url which requests Trimet's trip planner to travel home from campus
url = """
https://developer.trimet.org/ws/V1/trips/tripplanner?
fromPlace=8384
&toPlace=11771
&date={}
&time={}%3A{}
&arriveBy=false
&mode=WALK%2CBUS%2CTRAM%2CRAIL%2CGONDOLA
&showIntermediateStops=true
&maxWalkDistance=1207
&optimize=QUICK
&walkSpeed=1.34
&ignoreRealtimeUpdates=false
&numItineraries=3
&otherThanPreferredRoutesPenalty=900
&appID=5B1680B033D32C8D64A577CAA
"""

# Fill in current time and date
# timed_url = url.format(date, hours, minutes)

# # Check the schedules for the three offered options
# options = dict.fromkeys(["Option1", "Option2", "Option3"])
# option_number = 1
# for item in options:     # Get 3 options

# Add the trip option parameter to the url
# complete_url = timed_url + "&tripOption={}".format(option_number)
