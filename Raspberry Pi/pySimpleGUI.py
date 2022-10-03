from asyncore import loop
from curses import COLOR_RED
import PySimpleGUI as sg
import cv2 as cv2
import numpy as np
from PIL import Image
import PIL
import time
from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Key, Attr
import json
from botocore.exceptions import NoCredentialsError
import threading

#####
# Filename:     pySimpleGUI 
# Dated:        20220928
# Created by:   Tiggaa
# Function:     Provide a GUI for image capture and uploading to AWS S3; providing feedback to the user on door status
####

ACCESS_KEY = 'AKIAZRZDL2OJ2KZHK6VV'
SECRET_KEY = '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'
filename = 'Startup'

# Delay Mechanism for keeping lock open for 4 seconds

def long_function_thread(window):
    time.sleep(4)
    global filename
    filename = 'slept 4'
    window.write_event_value('-THREAD_DONE-', '')

def long_function():
    threading.Thread(target=long_function_thread, args=(window,), daemon=True).start()

# Upload image to AWS S3 Bucket

def upload_to_aws(local_file, bucket, s3_file):
    s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY,
                      aws_secret_access_key=SECRET_KEY)

    try:
        s3.upload_file(local_file, bucket, s3_file)
        print("Upload Successful")
        return True
    except FileNotFoundError:
        print("The file was not found")
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False

# Query AWS DynamoDb to see if pitcure was ientified and if the individual is allowed in the building
# Returns booleon to update the UI (or not)

def lock_status(local_file):
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-2', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
    table = dynamodb.Table('Log')
    response = table.scan(
        FilterExpression=Attr('DateTime').eq(local_file[:-11]) & Attr('Building Number').eq('1')
    )
    items = response['Items']
    if items == []:
        print(local_file)
        return UI_Updated(False)
    else:
        item = items[0]['Access Granted']
        print('Open Status: ' + str(item))
        return UI_Updated(item)
    

sg.theme

# Left Frame

layout_frame1 = [
    [sg.Image(filename='', key='-IMAGE-')]
]

# Right Frame

layout_frame2 = [
    
    [sg.Text(key='-TEXT-', pad=(00, 50), border_width=10, size=(100, 1), justification='center', font='Helvetica 40', background_color='#f71504')],
    [sg.Button('Let Me In', size=(20, 2), font='Helvetica 40')]
]

# Combines Left and Right Frame

layout = [
    [sg.Text('Building Secure', size=(26, 1), justification='center', font='Helvetica 40')],
    [sg.Frame("Live Image", layout_frame1, size=(400, 380)),
     sg.Frame("Lock Status", layout_frame2, size=(400, 380), title_location=sg.TITLE_LOCATION_TOP)]
    ]

# Create window and show it; 800x600 is touchscreen size; keep on top stops alerts and removes the menubar
window = sg.Window('Building Secure',
                    layout, no_titlebar=True, location=(0,0), size=(800,600), keep_on_top=True)

# Update the UI to show the door is Open / Closed - Receives boolean

def UI_Updated(status):
    if status == True:
        window['-TEXT-'].update("OPEN", background_color='#38B000')
        print('UI_Updated True')
        long_function()
    else:
        window['-TEXT-'].update('LOCKED', background_color='#f71504')
        print('UI_Updated False')

# Captures still image and saves to file system; updates filename for query to Dynamo

def CaptureImage():
    global filename
    start_time = datetime.now()
    DTG = start_time.strftime("%Y%m%d-%H%M%SZ")
    filename = DTG + 'capture.jpg'
    cv2.imwrite('Images/' + filename, image)
    uploaded = upload_to_aws(('Images/' + filename), 't5accessimages', (filename))
    lock_status(filename)

cap = cv2.VideoCapture(0) # Setup the OpenCV capture device (webcam)

# ---===--- Event LOOP Read and display frames, operate the GUI --- #
while True:
    event, values = window.read(timeout=20)
    ret, frame = cap.read()

    lock_status(filename)

    if event in ('Exit', None):
        break
    elif event == 'Let Me In':
        print('Let Me In')
        return_value, image = cap.read()
        CaptureImage() 

    elif event == '-THREAD DONE-':
        print('Your long operation completed')

    if ret:
        imgbytes=cv2.imencode('.png', frame)[1].tobytes()   # Convert the image to PNG Bytes
        window['-IMAGE-'].update(data=imgbytes)             # Stream a series of images to apear on screen
    else: 
        print("Camera Not Streaming")                       # Error Notification
        break 

window.close()