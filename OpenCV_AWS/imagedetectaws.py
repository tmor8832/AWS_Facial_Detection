import json
import boto3


def lambda_handler(event, context):
    # TODO implement
    bucket='t5accessimages'
    collectionId='T5-facecollection'
    fileName= event["Records"][0]["s3"]["object"]["key"]
    
    print(fileName)
    threshold = 80
    maxFaces=2

    client=boto3.client('rekognition')

  
    response=client.search_faces_by_image(CollectionId=collectionId,
                                Image={'S3Object':{'Bucket':bucket,'Name':fileName}},
                                FaceMatchThreshold=threshold,
                                MaxFaces=maxFaces)

                                
    faceMatches=response['FaceMatches']
    print ('Matching faces')
    SN = []
    for match in faceMatches:
            print ('FaceId:' + match['Face']['FaceId'])
            print ('Similarity: ' + "{:.2f}".format(match['Similarity']) + "%")
            print
            SN.append(match['Face']['ExternalImageId'][:-4])
            print(SN)
    return { 
            'Service_Number':SN,
            'statusCode': 200,
        }
    
