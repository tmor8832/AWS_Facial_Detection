# DefenceHackathon 2022 Team5

<h2> Problem 3 - Security </h1>

<h3> Team 5 aim to contribute to reducing the requirement for ID Cards through the use of facial recognition and cloud services to control building access. The system we built will use facial recognition to determine if someone should be granted entry, it is easily scalable and affordable </h2>

# 1.RPi / Camera setup

<image src="https://user-images.githubusercontent.com/64171887/192959105-3dd2929a-c605-42f2-9ad2-daa21c803c57.png" width="500" height="400"></image> 
<image src="https://user-images.githubusercontent.com/64171887/192960925-7a68fb01-bbd0-4499-8019-d125856ff778.png" width="500" height="400"></image> 
<image src="https://user-images.githubusercontent.com/64171887/192963223-af1ea7a5-d4f9-4840-bb76-47121aa28d4d.png" width="500" height="400"></image> 
<image src="https://user-images.githubusercontent.com/64171887/192965676-1af894e7-795b-45d7-a685-c245cfce9fce.png" width="500" height="400"></image> 


<h3> There are two cameras used in this project. One is used to take a still image of a face to check if the person is entitled to enter the building. You can see the interface the user sees on the above image.

The second camera is used as a secondary test, detecting motion clips.

Both cameras pass their imagery to  an S3 bucket which then triggers a lambda function to run AWS Rekognition service to determine if there are known faces (by comparing against the collection) and pulls information from DynamoDBs with the corresponding information. </h3>

Here are some code snippets of running AWS calls and using threading... 
```
  videoWriter.release()
                uploadthread = threading.Thread(target= doBoth, name='Uploader', args= (path,))
                uploadthread.start()
                recording = False
```
```
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

    def doBoth(path):
        uploaded = upload_to_aws("Video{}.mp4".format(path), 't5accessvideos', "Video{}.mp4".format(path))
        videoCheck("Video{}.mp4".format(path))
```
# 2. Tech stack

![image](https://user-images.githubusercontent.com/64171887/192972321-27d58ba9-f36f-4ce5-bf21-16ab0570bd45.png)

<h3> We used AWS services to make this work! </h3>

# 3. DB creation:

<h3> DB Creation
DB for this project are created on AWS DynamoDB which is a fully managed proprietary NoSQL database service and has been managed by us using python from raspberry Pis and lambda fuctions. Database creation was easily done on the AWS GUI but for a fully intergrated project would be done using mass imports </h3>

We created several DBs using the AWS GUI:

<image src="https://user-images.githubusercontent.com/78967307/192841648-7b9b7f9a-a118-4184-bcf3-910aefc6ffb4.jpg" width="500" height="400"></image> 
<image src="https://user-images.githubusercontent.com/78967307/192841847-3297318c-19e1-4c70-94a8-3a66fc6f8c0c.jpg" width="500" height="400"></image> 
<image src="https://user-images.githubusercontent.com/78967307/192842449-d9f7fd53-d667-46dd-9eb5-04b87b7d3be6.jpg" width="500" height="400"></image> 
<image src="https://user-images.githubusercontent.com/78967307/192842547-1a8185df-6a8d-474b-ab39-981854b75786.jpg" width="500" height="400"></image> 

The database requires a unique name and a partition key.
Once created we then added individual items using JSON input to our roles, personnel, areas and bases DB for testing and database interogation
These databases are now ready for use in the project

# 4. Logic

Using python, we push and pull from DynamoDB to get the information from the logs about whether someone should be allowed entry or not. If they are allowed entry, the python GUI will change to 'open'. 

The lambda function is triggered by S3:

<image src="https://user-images.githubusercontent.com/64171887/192971060-46126e74-2332-4fae-b0e7-d9eab4fb03a1.png" width="600" height="300"></image> 

```
#create the lambda handler, triggered by event in S3 bucket when something is uploaded to t5accessimages....
def lambda_handler(event, context):
    bucket='t5accessimages'     #variables which need to be changed to relevant folders....
    collectionId='T5-facecollection'
    fileName= event["Records"][0]["s3"]["object"]["key"]
    datetime = fileName[0:16] #slice the datetime from the file format

    threshold = 95 #how sure do you want it to be of seeing a face?
    maxFaces=2
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-2') #set right regions etc
    client=boto3.client('rekognition') #associate with rekognition service, all of this is copied from AWS example code.... https://docs.aws.amazon.com/rekognition/latest/dg/search-face-with-image-procedure.html
 
    response=client.search_faces_by_image(CollectionId=collectionId,
                                Image={'S3Object':{'Bucket':bucket,'Name':fileName}},
                                FaceMatchThreshold=threshold,
                                MaxFaces=maxFaces)
  ```

<h3> This is how the RPi queries dynamoDB to determine if the door should be opened </h3>

# Query AWS DynamoDb to see if pitcure was ientified and if the individual is allowed in the building
# Returns booleon to update the UI (or not)
```
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
```
<h3> This is how the video code determines what should be written to the log </h3>

```
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
```

![image](https://user-images.githubusercontent.com/64171887/192973213-2648fcdc-1fd4-47ee-9299-c46b874a57db.png)

An API was created to allow the front end to display log information in a more user-friendly format. The website is hosted in github and shown using AWS Amplify service.

This is an example of what the logs look like.. 

![image](https://user-images.githubusercontent.com/64171887/192968760-0a845292-73cc-4c45-9e60-c9ad9e92093c.png)


<h3>We also created an example of what an apple app might look like to notify the guard when there is unauthorised entry:</h3>

<image src="https://user-images.githubusercontent.com/64171887/192969792-c60a4b92-89e9-4adc-a7aa-2e7819036225.png" width="500" height="600"></image>

# 5. Our UI

<h3> A webpage was made on athena which makes use of an API to pull the information from DynamoDB whenever it is updated. Here is what that looks like... </h3>

![image](https://user-images.githubusercontent.com/64171887/193001305-45e7f567-cc3b-4a95-b36f-e9b9ceab7963.png)
![image](https://user-images.githubusercontent.com/64171887/193001375-4cf7d122-4b99-46d5-afb1-24fe00d20942.png)




