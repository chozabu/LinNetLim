#LinNetLim

This is a program to show how which TCP ports are using data, and limit it - similar to "NetLimiter" for Windows

GUI is in Kivy  
chains is used to read current net usage  
bash, tc and iptables are used to impose port limits  

Do not use if you have a custom iptables setup! This will wipe any custom rules (from the mangle table, and probably others too)

##Running

Create a python 2.7 env, install requirements and run the UI as root

    virtualenv env
    . env/bin/activate
    pip install -r requirements.txt
    sudo env/bin/python kivy_ui.py 

toggle the button next to ports you want to limit, type in an up/down limit in kb and press apply 

To clear limits - uncheck all limits and press apply - closing the program will not stop limiting 


