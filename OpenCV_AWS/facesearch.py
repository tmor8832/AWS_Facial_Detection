#name: facesearch.py
#date created: 27/09/2022

#basic hard code of aws face search from db collection
#import aws module
import boto3

if __name__ == "__main__":
    bucket = 't5accessimages' #bucket of uploaded images
    collectionId = 'T5-facecollection' #collection of indexed "personnel Face DB"
    fileName = '164020220927.jpg' #hardcoded image for testing
    threshold = 97 # % requirement of confidence to return poestive result
    maxFaces = 1 #max faces in image

    client = boto3.client('rekognition') #access to aws rekognition system
    #call to compare image to face collection
    response = client.search_faces_by_image(CollectionId=collectionId, Image={'S3Object': {'Bucket': bucket, 'Name': fileName}}, FaceMatchThreshold=threshold, MaxFaces=maxFaces)
    faceMatches = response['FaceMatches']
    print('Matching faces')
    #loop through matches and return person Service number
    for match in faceMatches:
        print('FaceId:' + match['Face']['FaceId'])
        print('Similarity: ' + "{:.2f}".format(match['Similarity']) + "%")
        print('ExternalImageId ' + match['Face']['ExternalImageId'])
        SN = match['Face']['ExternalImageId'][:-4]
        print(SN)
        print
