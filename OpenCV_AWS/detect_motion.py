# This was created by Tom M for RAF hackathon event Sep 22, this file reads in video stream from RPi and records a video when motion is detected
#It uses AWS S3 as the file storage location

# Import the neccessary libraries
import cv2
import numpy as np
import time
from datetime import datetime
from skimage.metrics import structural_similarity as compare_ssim
import json
import os
import boto3
from botocore.exceptions import NoCredentialsError

ACCESS_KEY = 'AKIAZRZDL2OJ2KZHK6VV'
SECRET_KEY = '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'


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

#cap = cv2.VideoCapture('rtsp://192.168.134.181:8554/cam')
cap = cv2.VideoCapture(0)
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fourcc = cv2.VideoWriter_fourcc(*'MP4V')  # this is the codec type used to write your output file, x264, h264 or this

# init our loop by faking the previous iteration
ret, prev_frame = cap.read()
recording = False

while True:  # run the loop continuously

    ret, current_frame = cap.read()

    diff = np.sum(cv2.absdiff(prev_frame, current_frame))
    grayA = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
    grayB = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    (score, diff) = compare_ssim(grayA, grayB, full=True)

    # we have a difference between frames...
    if score < 0.93:

        # not already recording? start recording
        if not recording:
            recording = True

            # this sets up the file to be written to using opencv
            start_time = datetime.now()
            path = start_time.strftime("%Y%m%d-%H%M%SZ")

            videoWriter = cv2.VideoWriter("Video{}.mp4".format(path), fourcc, 30.0, (frame_width, frame_height))

        # we're recording already - do nothing
        else:
            pass

        # reset spare frames
        end_frames = 5

    # # we don't have a difference between frames...
    else:

        # but we are recording (ie we are recording motion that has now stopped)
        if recording:
            # no more dead frames left? stop recording
            if end_frames == 0:
                videoWriter.release()
                uploaded = upload_to_aws("Video{}.mp4".format(path), 't5accessimages2', "Video{}.mp4".format(path))
                print('I have uploaded something!')
                recording = False


            end_frames -= 1

        # no motion and not recording - do nothing
        else:
            pass

    if recording:
        videoWriter.write(current_frame)

    # finally, current frame is now previous frame
    prev_frame = current_frame

cap.release()
connection.close()
