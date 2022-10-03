# This was created by Tom M for RAF hackathon event Sep 22, this file reads in video stream from RPi or webcam and records a video when motion is detected
# It uses AWS S3 as the file storage location

# This is a merge between a detect motion.py file and a file which pushes videos to an S3 bucket and then does compare collection against that video file. The results
# of that comparison are then pushed to an existing DynamoDB within AWS and it writes if an intruder has been detected by seeing if an unknown face is within the 
# video e.g. not in the collection. It will also test if a known face should not be in the building....

# The file is messy but the code does work... uses threading too :) 


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
import sys
import threading

dynamodb = boto3.resource('dynamodb', region_name='eu-west-2') #set right regions etc
client=boto3.client('rekognition') #associate with rekognition service, all of this is copied from AWS example code.... https://docs.aws.amazon.com/rekognition/latest/dg/search-face-with-image-procedure.html
    

ACCESS_KEY = 'AKIAZRZDL2OJ2KZHK6VV' #get the AWS access keys and set these values
SECRET_KEY = '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'

class VideoDetect: #this is all copied from AWS 
    jobId = ''
    rek = boto3.client('rekognition')
    sqs = boto3.client('sqs')
    sns = boto3.client('sns')
    
    roleArn = ''
    bucket = ''
    video = ''
    startJobId = ''

    sqsQueueUrl = ''
    snsTopicArn = ''
    processType = ''

    def __init__(self, role, bucket, video):    
        self.roleArn = role
        self.bucket = bucket
        self.video = video

    def GetSQSMessageSuccess(self):

        jobFound = False
        succeeded = False
    
        dotLine=0
        while jobFound == False:
            sqsResponse = self.sqs.receive_message(QueueUrl=self.sqsQueueUrl, MessageAttributeNames=['ALL'],
                                        MaxNumberOfMessages=10)

            if sqsResponse:
                
                if 'Messages' not in sqsResponse:
                    if dotLine<40:
                        print('.', end='')
                        dotLine=dotLine+1
                    else:
                        print()
                        dotLine=0    
                    sys.stdout.flush()
                    time.sleep(5)
                    continue

                for message in sqsResponse['Messages']:
                    notification = json.loads(message['Body'])
                    rekMessage = json.loads(notification['Message'])
                    print(rekMessage['JobId'])
                    print(rekMessage['Status'])
                    if rekMessage['JobId'] == self.startJobId:
                        print('Matching Job Found:' + rekMessage['JobId'])
                        jobFound = True
                        if (rekMessage['Status']=='SUCCEEDED'):
                            succeeded=True

                        self.sqs.delete_message(QueueUrl=self.sqsQueueUrl,
                                    ReceiptHandle=message['ReceiptHandle'])
                    else:
                        print("Job didn't match:" +
                            str(rekMessage['JobId']) + ' : ' + self.startJobId)
                    # Delete the unknown message. Consider sending to dead letter queue
                    self.sqs.delete_message(QueueUrl=self.sqsQueueUrl,
                                ReceiptHandle=message['ReceiptHandle'])


        return succeeded

    def StartLabelDetection(self):
        response=self.rek.start_label_detection(Video={'S3Object': {'Bucket': self.bucket, 'Name': self.video}},
            NotificationChannel={'RoleArn': self.roleArn, 'SNSTopicArn': self.snsTopicArn})

        self.startJobId=response['JobId']
        print('Start Job Id: ' + self.startJobId)


    def GetLabelDetectionResults(self):
        maxResults = 10
        paginationToken = ''
        finished = False

        while finished == False:
            response = self.rek.get_label_detection(JobId=self.startJobId,
                                            MaxResults=maxResults,
                                            NextToken=paginationToken,
                                            SortBy='TIMESTAMP')

            print('Codec: ' + response['VideoMetadata']['Codec'])
            print('Duration: ' + str(response['VideoMetadata']['DurationMillis']))
            print('Format: ' + response['VideoMetadata']['Format'])
            print('Frame rate: ' + str(response['VideoMetadata']['FrameRate']))
            print()

            for labelDetection in response['Labels']:
                label=labelDetection['Label']

                print("Timestamp: " + str(labelDetection['Timestamp']))
                print("   Label: " + label['Name'])
                print("   Confidence: " +  str(label['Confidence']))
                print("   Instances:")
                for instance in label['Instances']:
                    print ("      Confidence: " + str(instance['Confidence']))
                    print ("      Bounding box")
                    print ("        Top: " + str(instance['BoundingBox']['Top']))
                    print ("        Left: " + str(instance['BoundingBox']['Left']))
                    print ("        Width: " +  str(instance['BoundingBox']['Width']))
                    print ("        Height: " +  str(instance['BoundingBox']['Height']))
                    print()
                print()
                print ("   Parents:")
                for parent in label['Parents']:
                    print ("      " + parent['Name'])
                print ()

                if 'NextToken' in response:
                    paginationToken = response['NextToken']
                else:
                    finished = True
    
    
    def CreateTopicandQueue(self):
    
        millis = str(int(round(time.time() * 1000)))

        #Create SNS topic
        
        snsTopicName="AmazonRekognitionExample" + millis

        topicResponse=self.sns.create_topic(Name=snsTopicName)
        self.snsTopicArn = topicResponse['TopicArn']

        #create SQS queue
        sqsQueueName="AmazonRekognitionQueue" + millis
        self.sqs.create_queue(QueueName=sqsQueueName)
        self.sqsQueueUrl = self.sqs.get_queue_url(QueueName=sqsQueueName)['QueueUrl']

        attribs = self.sqs.get_queue_attributes(QueueUrl=self.sqsQueueUrl,
                                                    AttributeNames=['QueueArn'])['Attributes']
                                        
        sqsQueueArn = attribs['QueueArn']

        # Subscribe SQS queue to SNS topic
        self.sns.subscribe(
            TopicArn=self.snsTopicArn,
            Protocol='sqs',
            Endpoint=sqsQueueArn)

        #Authorize SNS to write SQS queue 
        policy = """{{
"Version":"2012-10-17",
"Statement":[
    {{
    "Sid":"MyPolicy",
    "Effect":"Allow",
    "Principal" : {{"AWS" : "*"}},
    "Action":"SQS:SendMessage",
    "Resource": "{}",
    "Condition":{{
        "ArnEquals":{{
        "aws:SourceArn": "{}"
        }}
    }}
    }}
]
}}""".format(sqsQueueArn, self.snsTopicArn)

        response = self.sqs.set_queue_attributes(
            QueueUrl = self.sqsQueueUrl,
            Attributes = {
                'Policy' : policy
            })

    def DeleteTopicandQueue(self):
        self.sqs.delete_queue(QueueUrl=self.sqsQueueUrl)
        self.sns.delete_topic(TopicArn=self.snsTopicArn)

#Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#PDX-License-Identifier: MIT-0 (For details, see https://github.com/awsdocs/amazon-rekognition-developer-guide/blob/master/LICENSE-SAMPLECODE.)

    # ============== Face Search ===============
    def StartFaceSearchCollection(self,collection):
        response = self.rek.start_face_search(Video={'S3Object':{'Bucket':self.bucket,'Name':self.video}},
            CollectionId=collection,
            NotificationChannel={'RoleArn':self.roleArn, 'SNSTopicArn':self.snsTopicArn})
        
        self.startJobId=response['JobId']
        
        print('Start Job Id: ' + self.startJobId)


    def GetFaceSearchCollectionResults(self):
        maxResults = 10
        paginationToken = ''

        finished = False

        while finished == False:
            response = self.rek.get_face_search(JobId=self.startJobId,
                                        MaxResults=maxResults,
                                        NextToken=paginationToken)

            print(response['VideoMetadata']['Codec'])
            print(str(response['VideoMetadata']['DurationMillis']))
            print(response['VideoMetadata']['Format'])
            print(response['VideoMetadata']['FrameRate'])

            ##################################################

            # This is where the bulk of the code is actually written!

            ###################################################

            #initialise some variables to hold things...
            SN = []
            Names = []
            hasAccess = False
            Intruder = False
            for personMatch in response['Persons']:
                print('Person Index: ' + str(personMatch['Person']['Index']))
                print('Timestamp: ' + str(personMatch['Timestamp']))
                if(personMatch['FaceMatches']):
                    for match in personMatch['FaceMatches']:
                        x = datetime.now()
                        y = x.strftime("%Y%m%d-%H%M%SZ")
                        print('Face ID: ' + match['Face']['FaceId'])
                        print('Similarity: ' + str(match['Similarity']))
                        sn = match["Face"]['ExternalImageId'][:-4]
                        SN.append(sn)
                        table = dynamodb.Table('personnel') #read from personnel table set up in dynamo DB
                        response = table.get_item(Key={"service number": str(sn)}) #now search another table based on this value. Linking the two DBs.
                        Sur = response['Item']['Surname'] #get the surname from the dictionary
                        Names.append(str(response))
                        pid = (response['Item']['PID']) #get their pid from the response dict
                        table2 = dynamodb.Table('Roles') #now link to second table to get their building access info
                        access = table2.get_item(Key={"PID": pid})
                        for item in access['Item']['Areas']: #loop through each of the buildings they have access to
                            if item== 1: #if they have access to bldg 1 great, break as thats the building we want.
                                hasAccess =True
                                Intruder = 'NO'
                                break
                        else:
                            hasAccess = False #if they don't have building 1 access, set this to false.
                            Intruder = 'NO - KNOWN INTRUDER'
                            break

                        table = dynamodb.Table('Log') #set up for writing to the log database...
            
                        table.put_item( #put the variables obtained as a new entry into the log db
                        Item={
                            'ID stamp': y + '-1',
                            'Access Granted': hasAccess,
                            'DateTime': str(y),
                            'Service Number': str(sn),
                            'Building Number': '1',
                            'Surname': Sur,
                            'Authorised Access?' : Intruder,
                        }
                        )
                            #if the face is not matched, we have to write that there is an unknown intruder to the log.
                else:
                    xx = datetime.now()
                    yy = xx.strftime("%Y%m%d-%H%M%SZ")

                    table = dynamodb.Table('Log') #set up for writing to the log database...
        
                    table.put_item( #put the variables obtained as a new entry into the log db
                    Item={
                        'ID stamp': yy + '-1',
                        'Access Granted': 'NO!',
                        'DateTime': str(yy),
                        'Service Number': 'N/A',
                        'Building Number': '1',
                        'Surname': 'N/A',
                        'Authorised Access?' : 'NO - UNKNOWN INTRUDER',
                    }
                    )
        

            if 'NextToken' in response:
                paginationToken = response['NextToken']
            else:
                finished = True
            print()


#put keys from AWS in here... this function is straight from AWS site
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
cap = cv2.VideoCapture(4)
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
                uploadthread = threading.Thread(target= doBoth, name='Uploader', args= (path,))
                #use threading to enable processes to run simultaneously so we don't get a bottleneck!
                uploadthread.start()
                recording = False

            end_frames -= 1

        # no motion and not recording - do nothing
        else:
            pass

    if recording:
        videoWriter.write(current_frame)

    # finally, current frame is now previous frame
    prev_frame = current_frame

#Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#PDX-License-Identifier: MIT-0 (For details, see https://github.com/awsdocs/amazon-rekognition-developer-guide/blob/master/LICENSE-SAMPLECODE.)


    def videoCheck(vidname):
        roleArn = 'arn:aws:iam::656667300755:role/Team5'   
        bucket = 't5accessvideos'
        video = vidname

        analyzer=VideoDetect(roleArn, bucket,video)
        analyzer.CreateTopicandQueue()

        collection='T5-facecollection'
        analyzer.StartFaceSearchCollection(collection)
        
        if analyzer.GetSQSMessageSuccess()==True:
            analyzer.GetFaceSearchCollectionResults()
        
        analyzer.DeleteTopicandQueue()

    
#function used by threading

    def doBoth(path):
        uploaded = upload_to_aws("Video{}.mp4".format(path), 't5accessvideos', "Video{}.mp4".format(path))
        videoCheck("Video{}.mp4".format(path))
