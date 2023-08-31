import machine
from machine import Pin,UART,I2C,PWM
import socket
import network
import _thread
import ssd1306
import time

#CPU overclock
#machine.freq(240000000)

#Change your Callsign and set work mode to AP, offline, wifi. Set your wifi credentials.
call_sign = "KP4RX"
work_mode = "wifi"
#Wifi Settings
ssid = "[your_wifi_network]"
psk = "[your_wifi_password]"
host = "hl2-xpa"
#AP Settings
ap_ssid = "HL2-XPA"
ap_password = "DEADBEEF"
ap_host = "hl2-xpa"

# HW Config
pwr=machine.Pin(20,machine.Pin.OUT)
amp=machine.Pin(21,machine.Pin.OUT)
atu=machine.Pin(22,machine.Pin.OUT)
sda_pin=18
scl_pin=19
uart_tx=12
uart_rx=13
i2c = I2C(1,sda=Pin(sda_pin), scl=Pin(scl_pin))
oled = ssd1306.SSD1306_I2C(128, 32, i2c)

#Band Power Pin Config
#Requires output filter with 10k resistor and 0.68uf capacitor
bandpin=PWM(Pin(2, mode=Pin.OUT))
bandpin.freq(30_000)

#Startup Variables
freq=0
freq_mhz=0
freq_ref=0
band=0
band_ref=0
freq_raw=0
duty_cycle=0
sys_state="ON"
pa_state="ON"
atu_state="ON"

#Display Credits
#oled.fill(0)
#oled.text("Starting Up...", 0, 15, 1)
##oled.show()
#print("Boot Wait...")
#print("Ctrl - C to Cancel")
#Boot wait to stop script before watchdog kicks in
#time.sleep(5)
print("HL2 XPA125B Interface by KP4RX")
oled.fill(0)
oled.text("HL2-XPA125B", 20, 0, 1)
oled.text("Interface", 27, 12, 1)
oled.text("By KP4RX", 32, 24, 1)
oled.show()

def hermes_interface():
    global freq
    global freq_mhz
    global freq_ref
    global freq_raw
    global band
    global work_mode
    global band_ref
    global duty_cycle
    if work_mode == "wifi":
        print('Wi-Fi Mode')
        oled.fill(0)
        oled.text(ip, 0, 0, 1)
        oled.text('http://'+ host, 0, 12, 1)
        oled.text('Set VFO in HL2', 0, 24, 1)
        oled.show()
    if work_mode == "offline":
        print('Offline Mode')
        oled.fill(0)
        oled.text(call_sign, 43, 0, 1)
        oled.text('Offline Mode', 18, 12, 1)
        oled.text('Set VFO in HL2', 10, 24, 1)
        oled.show()
    if work_mode == "AP":
        print('AP Mode')
        oled.fill(0)
        oled.text(call_sign, 43, 0, 1)
        oled.text('AP Mode', 30, 12, 1)
        oled.text('Set VFO in HL2', 10, 24, 1)
        oled.show()
    #Initialize UART
    uart=UART(0, baudrate=9600, tx=Pin(uart_tx), rx=Pin(uart_rx))
    uart.init(bits=8, parity=None, stop=1)
    while True:
        if uart.any(): 
            serialdata = bytearray(uart.read())
            if len(serialdata) == 14:
                freq_raw = ''.join(chr(x) for x in serialdata).strip("FA;")
                freq = f'{int(freq_raw):,}'.replace(',', '.')
                freq_mhz = int(freq_raw)
                if freq != freq_ref:
                    if 50000000 <= freq_mhz <= 54000000:
                        band = 6
                        duty_cycle=84
                    elif 28000000 <= freq_mhz <= 29700000:
                        band = 10
                        duty_cycle=77
                    elif 24890000 <= freq_mhz <= 24990000:
                        band = 12
                        duty_cycle=70
                    elif 21000000 <= freq_mhz <= 21450000:
                        band = 15
                        duty_cycle=56
                    elif 18068000 <= freq_mhz <= 18168000:
                        band = 17
                        duty_cycle=49
                    elif 14000000 <= freq_mhz <= 14350000:
                        band = 20
                        duty_cycle=42
                    elif 10100000 <= freq_mhz <= 10150000:
                        band = 30
                        duty_cycle=35
                    elif 7000000 <= freq_mhz <= 7300000:
                        band = 40
                        duty_cycle=28
                    elif 5330500 <= freq_mhz <= 5403500:
                        band = 60
                        duty_cycle=21
                    elif 3500000 <= freq_mhz <= 4000000:
                        band = 80
                        duty_cycle=14
                    elif 1800000 <= freq_mhz <= 2000000:
                        band = 160
                        duty_cycle=7
                    else:
                        band = 0
                        duty_cycle=0
                        oled.fill(0)
                        oled.text(call_sign, 43, 0, 1)
                        oled.text('FREQ: {}'.format(freq), 0, 12, 1)
                        oled.text('OUT OF BAND', 0, 24, 1)
                        oled.show()
                        print('Out Of band')
                        print('Freq:',freq)
                        band_ref = band
                        freq_ref = freq_mhz
                        bandpin.deinit()
                if band != band_ref:                    
                    print("Band Set:",band,'M')
                    bandpin.duty_u16(int((duty_cycle/100)*65_535))
                    band_ref = band                                                      
                if freq_ref != freq_mhz:
                    print('Freq:',freq)
                    oled.fill(0)
                    oled.text(call_sign, 43, 0, 1)
                    oled.text('FREQ: {}'.format(freq), 0, 12, 1)
                    oled.text('BAND: {} METERS'.format(band), 0, 24, 1)
                    oled.show()
                    freq_ref = freq_mhz
# Wi-fi Setup
if work_mode == "wifi":
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    network.hostname(host)
    wlan.connect(ssid, psk)
    wait = 10
    while wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        wait -= 1
        print('Connecting to Wi-Fi...')
        time.sleep(1)
    if wlan.status() != 3:
        raise RuntimeError('wifi connection failed')
    else:
        print('connected')
        ip=wlan.ifconfig()[0]
        print('IP: ', ip)
        print('Hostname: ', network.hostname())
        _thread.start_new_thread(hermes_interface, ())

if work_mode == "AP":
    network.hostname(ap_host)
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=ap_ssid, password=ap_password) 
    ap.active(True)
    _thread.start_new_thread(hermes_interface, ())

def webpage(band, freq, call_sign, sys_state, pa_state, atu_state):
    html = f"""
            <!DOCTYPE html>
            <html lang="en" class="">
            <head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
            <meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no">
            <title>HL2 to XPA125B Interface - {call_sign}</title>
            <script>
            window.history.replaceState({{}}, document.title, "/");
            </script>
            <style>div,fieldset,input,select{{padding:5px;font-size:1em;}}fieldset{{background:#282531;}}p{{margin:0.5em 0;}}input{{width:100%;box-sizing:border-box;-webkit-box-sizing:border-box;-moz-box-sizing:border-box;background:#282531;color:#eaeaea;}}input[type=checkbox],input[type=radio]{{width:1em;margin-right:6px;vertical-align:-1px;}}input[type=range]{{width:99%;}}select{{width:100%;background:#282531;color:#eaeaea;}}textarea{{resize:vertical;width:98%;height:318px;padding:5px;overflow:auto;background:#1d1b26;color:#d7ccff;}}body{{text-align:center;font-family:verdana,sans-serif;background:#252525;}}td{{padding:0px;}}button{{border:0;border-radius:0.3rem;background:#694fa8;color:#faffff;line-height:2.4rem;font-size:1.2rem;width:100%;-webkit-transition-duration:0.4s;transition-duration:0.4s;cursor:pointer;}}button:hover{{background:#4d3e7f;}}.bred{{background:#b73d5d;}}.bred:hover{{background:#822c43;}}.bgrn{{background:#1f917c;}}.bgrn:hover{{background:#156353;}}a{{color:#694fa8;text-decoration:none;}}.p{{float:left;text-align:left;}}.q{{float:right;text-align:right;}}.r{{border-radius:0.3em;padding:2px;margin:6px 2px;}}
            </style>
            </head>
            <body>
            <div style="text-align:left;display:inline-block;color:#eaeaea;min-width:340px;">
            <div style="text-align:center;color:#eaeaea;">
            <h1>{call_sign}</h1>
            <h2>HL2 to XPA125B Interface</h2>
            <noscript>To use Interface, please enable JavaScript<br></noscript>
            <h3>Band: <strong>{band} M</strong><br>VFO A:<strong> {freq} MHz</h3>
            </div>
            <div id="but3d" style="display: block;">
            <center>
			<table style="table-layout: fixed; width: 180px"><colgroup><col style="width: 60px"><col style="width: 60px"><col style="width: 60px"></colgroup><thead><tr><th>AMP</th><th>PA</th><th>ATU</th></tr></thead><tbody><tr><td align="center">{sys_state}</td><td align="center">{pa_state}</td><td align="center">{atu_state}</td></tr></tbody></table>
			</center>
            </div>
            <p></p>
            <form id="but3" style="display: block;" action="./amp" method="get">
            <button name="" id="pabut">PA State</button>
            </form>
            <p></p>
            <p></p>
            <form id="but4" style="display: block;" action="./atu" method="get">
            <button name="">ATU</button>
            </form>
            <p></p>
            <p></p>
            <form id="but5" style="display: block;" action="./tune" method="get">
            <button name="">Tune</button>
            </form>
            <p></p>
            <p></p>
            <form id="but0" style="display: block;" action="./pwron" method="get" onsubmit="return confirm(&quot;Confirm Power On&quot;);">
            <button name="" class="button bred">Power On</button>
            </form>
            <p></p>
            <p></p>
            <form id="but1" style="display: block;" action="./pwroff" method="get" onsubmit="return confirm(&quot;Confirm Power Off&quot;);">
            <button name="" class="button bred">Power Off</button>           
            </form>
            <p></p>
            <div style="text-align:right;font-size:11px;"><hr><a href="https://kp4rx.com" target="_blank" style="color:#aaa;">Hermes Lite 2 to XPA125B interface - By KP4RX</a>
            </div>
            </div>
            </body>
            </html>
           """
    return html
 
def serve(connection):
    global sys_state
    global pa_state
    global atu_state
    while True:
        client = connection.accept()[0]
        request = client.recv(1024)
        request = str(request)
        try:
            request = request.split()[1]
        except IndexError:
            pass        
        print(request)      
        if request == '/atu?' and sys_state == "ON":
            if atu_state == "ON":
                atu_state = "OFF"
            elif atu_state == "OFF":
                atu_state = "ON"
            atu.high()
            time.sleep_ms(100)
            atu.low()
        elif request == '/pwron?' and sys_state == "OFF":
            sys_state = "ON"
            pwr.high()
            time.sleep_ms(600)
            pwr.low()
        elif request == '/pwroff?' and sys_state == "ON":
            sys_state = "OFF"
            pwr.high()
            time.sleep_ms(3000)
            pwr.low()
        elif request == '/amp?' and sys_state == "ON":
            if pa_state == "ON":
                pa_state = "OFF"
            elif pa_state == "OFF":
                pa_state = "ON"
            amp.high()
            time.sleep_ms(100)
            amp.low()
        elif request == '/tune?' and atu_state == "ON":
            time.sleep_ms(2500)
            atu.high()
            time.sleep_ms(700)
            atu.low()

        html=webpage(band, freq, call_sign, sys_state, pa_state, atu_state)
        client.send(b"HTTP/1.1 200 OK\n\n")
        client.send(html)
        client.close()
 
def open_socket(ip):
    # Open a socket
    address = (ip, 80)
    connection = socket.socket()
    connection.bind(address)
    connection.listen(1)
    print(connection)
    print("System Ready!")
    return(connection)
 
try:
    if work_mode == 'offline':
        hermes_interface()
    elif work_mode == 'AP':
        while ap.active == False:
            pass
        ip=ap.ifconfig()[0]
        print(ip)
        connection=open_socket(ip)
        serve(connection)
    elif ip is not None:
        connection=open_socket(ip)
        serve(connection)
except KeyboardInterrupt:
    machine.reset()