import pickle
from tkinter import *
from tkinter import ttk

import requests
from bs4 import BeautifulSoup


class Scraper:
    """This class contains the method for scraping the data from webpage and serialize as file."""

    def __init__(self):
        """Constructor method"""
        # The data is maintained as a dictionary.
        # Methods will be specific to the type of scraping work and the scraped data will be stored with specific key.
        self.data = {}

    def scrape_bus_routes(self):
        """This method does below actions -
        - Try to read the list of Bus objects from serialized file
        - Try to read the total list of stops from serialized file
        - If the serialized files do not exist, retrieve the bus routes from URL
        - Store the retrieved data as serialized file"""
        buses = []
        stops = []
        try:
            # Retrieve the serialized list of Bus objects.
            buses = pickle.load(open('./busroutes.pkl', 'rb'))
            # Retrieve the serialized list of all bus stops.
            stops = pickle.load(open('./allstops.pkl', 'rb'))
        except FileNotFoundError as e:
            # Retrieve the data from URL if files are not found
            print('File not found, starting to scrape.')
            url = "http://www.londonbusroutes.net/routes.htm"
            r = requests.get(url)
            # Read the URL content and create a BeautifulSoup object. Using html.parser whereas
            # other parsers can be used as well
            soup = BeautifulSoup(r.content,
                                 'html.parser')
            # The data retrieval process from the scraped web page heavily depends on how the page is designed.
            # This page contains the data in a tabular manner. So, it is best to retrieve as rows.
            # Find all the table rows in the page
            rows = soup.findAll('table')[2].findAll('tr')

            # Iterate through the rows
            # Each row contains information about one bus.
            # So, one Bus object will be created with extracted information from each row.
            for row in rows:
                bus = Bus()
                # Get the columns in a row.
                columns = row.findAll('td')
                # First column contains the bus number
                bus.bus_number = columns[0].text
                # Third column contains the bus line
                bus.bus_line = columns[2].text
                # Second column contains the stops separated by ' - '
                # However, there are variations in the texts in the second column.
                # So, we need some special processing for this column.
                # Get the html representation of the column content.
                stops_str = columns[1].prettify()
                # Since only the first line contains the stops related information, we need to split and retrieve the
                # first line only.
                if '<br/>' in stops_str:
                    stops_str = stops_str.split('<br/>')[0]
                stops_str = stops_str.replace('\n', '')

                # Now parse with BeautifulSoup to get the text content of the first line before the <br>
                bus_stops_str = BeautifulSoup(stops_str, 'html.parser').get_text()
                # Split with ' - ' to get the list of stops
                bus_stops = bus_stops_str.strip().split(' - ')
                # Iterate through the stops
                for bus_stop in bus_stops:
                    # Check blank
                    if bus_stop.strip() != '':
                        # Convert multiple spaces within stop text with single space
                        bus_stop = ' '.join(bus_stop.split())
                        # Append into the stops list within Bus object
                        bus.stops.append(bus_stop.strip())
                # Append the Bus object into list
                buses.append(bus)
                # Append the stops into the total list of stops. Use set operation to prevent duplicates
                stops.extend(set(bus.stops) - set(stops))
            # Store the prepared lists as serialized files
            pickle.dump(buses, open('busroutes.pkl', 'wb'))
            pickle.dump(stops, open('allstops.pkl', 'wb'))

        # Store the two lists into the data variable with respective keys
        self.data['london_buses'] = buses
        self.data['london_bus_stops'] = stops


class Bus:
    """This class contains the bus related details and the stops the bus travels through."""

    # Constructor method
    def __init__(self):
        """This is the constructor method."""
        self.bus_number = ''
        self.bus_line = ''
        self.stops = []

    # Overriding method to return the string representation of the attributes in the Bus object.
    def __str__(self):
        """Overriding method to return text representation of the Bus object."""
        return f'Bus number - {self.bus_number}, Bus line - {self.bus_line}, Stops - {self.stops}'


class LondonBuses:
    """This class contains the variables and methods to execute the application for searching direct bus
    between two bus stops in London"""
    def __init__(self):
        """Constructor method for the application.
        This method invokes the Scraper method to retrieve the list of stops and the bus information."""
        # Retrieve the required data of Bus objects and all stops
        scraper = Scraper()
        scraper.scrape_bus_routes()
        self.bus_routes = scraper.data['london_buses']
        self.all_stops = scraper.data['london_bus_stops']
        # Variables for the screen fields
        # The Combobox for the starting bus stop
        self.start_combo = None
        # The Combobox for the ending bus stop
        self.end_combo = None
        # The variable to show the bus found after search
        self.bus_variable = None

    def get_bus_numbers(self):
        """This method reads the selected stops from the screen fields and retrieves the first instance of
        matching bus detail where the bus runs between the selected stops."""
        # Read the name of the starting stop
        start_pos = self.start_combo.get()
        # Read the name of the ending stop
        end_pos = self.end_combo.get()

        # Iterate through the list of Bus objects
        for bus in self.bus_routes:
            # Check that the input stops are both present in the list of stops of the Bus object
            if start_pos in bus.stops and end_pos in bus.stops:
                print(bus)
                # Print the matching Bus details on the screen.
                self.bus_variable.set(
                    f'Bus number - {bus.bus_number},\nBus line - {bus.bus_line},\nStops - {bus.stops}')
                return
        # Show that no matching bus was found
        self.bus_variable.set('No direct bus found between these stations.')

    def show_components(self):
        """This method renders the screen components."""

        # Initiate Tk surface
        root = Tk()
        root.geometry('370x400')
        # Assign title for the dialog window
        root.title("Find direct bus between stops")

        # Now create two screen elements for the starting position and the ending position.
        # User needs to see all stops and choose one option
        # The stops should be sorted alphabetically
        # Used Combobox instead of OptionMenu because scrollbar is needed
        # For Combobox, create a container first and then use the container with the Combobox
        start_container = ttk.LabelFrame(root, text="Select start location")
        self.start_combo = ttk.Combobox(start_container, values=sorted(self.all_stops))
        self.start_combo.pack()
        start_container.place(x=30, y=50, height=50, width=300)

        end_container = ttk.LabelFrame(root, text="Select end location")
        self.end_combo = ttk.Combobox(end_container, values=sorted(self.all_stops))
        self.end_combo.pack()
        end_container.place(x=30, y=120, height=50, width=300)

        # Create a button to invoke the get_bus_numbers() method with the selected start and end stops
        Button(root, text='Submit', command=self.get_bus_numbers, width=20, bg='brown', fg='white').place(x=100, y=190)

        # Create a Label to show the matching bus details.
        # Create a variable with the label so that the text can be updated from the get_bus_numbers() method.
        self.bus_variable = StringVar(root)
        self.bus_variable.set('Select start and end stations to search for direct bus details.')
        result_label = Label(root, textvariable=self.bus_variable, font=("bold", 10), wraplength=300, justify="left")
        result_label.place(x=30, y=250)

        # Render the dialog box with all fields
        root.mainloop()


# Check whether the game is executed from command
if __name__ == '__main__':
    # Initiate the LondonBuses object
    london_buses = LondonBuses()
    # Initiate method to display screen components
    london_buses.show_components()
