import network
import urequests
import secrets
import time
import json

from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY
from pimoroni import RGBLED

# set up the hardware
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY, rotate=270)

# set the display backlight to 20%
display.set_backlight(0.5)
display.set_font("sans")
display.set_thickness(2)

# turn off the RGB LED
led = RGBLED(6, 7, 8)
led.set_rgb(0,0,0)

# set up constants for drawing
WIDTH, HEIGHT = display.get_bounds()
# setup some colours
RED = display.create_pen(209, 34, 41)
YELLOW = display.create_pen(255, 216, 0)
GREEN = display.create_pen(0, 216, 0)
WHITE = display.create_pen(255, 255, 255)
BLUE = display.create_pen(116, 215, 238)
BLACK = display.create_pen(0, 0, 0)

def connectWifi():
   # Connect to WiFi
   print('Connecting to WiFi...')
   wlan = network.WLAN(network.STA_IF)
   wlan.active(True)
   wlan.connect(secrets.WIFI_SSID, secrets.WIFI_PASSWORD)
   while not wlan.isconnected():
      pass
   print('Connected to WiFi')


def getMixergyStatus():
    print('Mixergy: Connecting to API...')
    username = secrets.MIXERGY_USER
    password = secrets.MIXERGY_PASSWORD
    serial_number = secrets.MIXERGY_TANK
    # Get login URL
    result = urequests.request('GET',"https://www.mixergy.io/api/v2")
    root_result = result.json()
    account_url = root_result["_links"]["account"]["href"]
    result = urequests.request('GET',account_url)
    account_result = result.json()
    login_url = account_result["_links"]["login"]["href"]
    result = urequests.request('POST',login_url, json = {'username': username, 'password': password})
    if result.status_code != 201:
       print("Mixergy: authentication failure. Check your credentials and try again!")
       exit()

    print("Mixergy: authentication successful!")

    login_result = result.json()

    login_token = login_result["token"]

    headers = {'Authorization': f'Bearer {login_token}'}

    result = urequests.request('GET',"https://www.mixergy.io/api/v2", headers=headers)

    root_result = result.json()

    tanks_url = root_result["_links"]["tanks"]["href"]

    result = urequests.request('GET',tanks_url, headers=headers)

    tanks_result = result.json()

    tanks = tanks_result['_embedded']['tankList']
    for i, subjobj in enumerate(tanks):
      if serial_number == subjobj['serialNumber']:
        print("Mixergy: Found tanks serial number", subjobj['serialNumber'])

        tank_url = subjobj["_links"]["self"]["href"]
        print("Mixergy: Tank Url:", tank_url)
        
        print("Mixergy: Fetching details...")

        result = urequests.request('GET',tank_url, headers=headers)

        tank_result = result.json()

        latest_measurement_url = tank_result["_links"]["latest_measurement"]["href"]
        control_url = tank_result["_links"]["control"]["href"]
        modelCode = tank_result["tankModelCode"]


        result = urequests.request('GET',latest_measurement_url, headers=headers)

        latest_measurement_result = result.json()
        charge = latest_measurement_result["charge"]
        print("Mixergy: Charge={}".format(charge))

        state = json.loads(latest_measurement_result["state"])

        current = state["current"]
        heat_source = current["heat_source"]
        heat_source_on = current["immersion"] == "On"

        print('Mixergy: Heat Source={}, Heat Source On={}'.format(heat_source,heat_source_on))
    return (charge,heat_source, heat_source_on)

def getGivEnergyStatus():
    print('GivEnergy: Connecting to API...')
    # Make GivEnergy API call to get Inverter data
    url = "https://api.givenergy.cloud/v1/inverter/"+secrets.GIVENERGY_INVERTER+"/system-data/latest"
    headers = {
      'Authorization': 'Bearer '+ secrets.GIVENERGY_API_KEY,
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    }
    print('GivEnergy: Retreiving Status')
    response = urequests.request('GET',url,headers=headers)
    data = response.json()
    batt_lvl = data['data']['battery']['percent']
    pwr_lvl = data['data']['battery']['power']
    #print("GivEnergy: Battery Level=%d%,Power Level=%dW",batt_lvl,pwr_lvl)
    print("GivEnergy: Battery Level={}%,Power Level={}W".format(batt_lvl,pwr_lvl) )
    return (batt_lvl, pwr_lvl)

# fills the screen with black
display.set_pen(BLACK)
display.clear()
display.set_pen(WHITE)
display.text("WAIT..", 3, 20, 0, 1)
display.update()
    
connectWifi()
while True:
    
    # fills the screen with white
    display.set_pen(BLACK)
    display.clear()
    display.set_thickness(3)
    # get GivEnergy stats from the API
    batt_lvl, pwr_lvl = getGivEnergyStatus()
    
    # write labels to the screen
    display.set_pen(WHITE)
    display.text("BATTERY", 3, 20, 0, 1)
    display.text("MIXERGY", 3, 155, 0, 1)
    
    # writes the battery level as text
    if (batt_lvl <= 10):
        display.set_pen(RED)
        display.text("{:02d}".format(batt_lvl) + "%", 3, 60, 0, 2)
    elif (batt_lvl > 10):
        display.set_pen(GREEN)
        display.text("{:02d}".format(batt_lvl) + "%", 3, 60, 0, 2)
        
    # writes the instantaneous power level as text (negative value means it's charging)
    display.set_pen(WHITE)
    display.text("{:04d}".format(pwr_lvl) + "W", 3, 100, 0, 1)

    # writes the Mixergy charge level as text
    charge,heat_source,heat_source_on = getMixergyStatus()
  
    # writes the mixergy charge level as text
    display.text("{:d}".format(int(charge)) + "%", 3, 195, 0, 2)
    # writes the mixergy heating status
    if heat_source_on:
        display.set_pen(GREEN)
        display.text(heat_source, 3, 227, 0, 1)
    
    
    # finally... update the display from the framebuffer
    display.update()
    # wait 30s before next update
    time.sleep(30)
 

