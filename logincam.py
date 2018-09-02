#!/usr/bin/python36

from flask import Flask, render_template, Response
from camera import VideoCamera
import cv2
import numpy as np
import subprocess as sp
import webbrowser
from os import listdir
from os.path import isfile, join

app = Flask(__name__,template_folder='/var/www/html')

@app.route('/')
def index():
    return render_template('afterloginface.html')

face_cascade=cv2.CascadeClassifier('/var/www/cgi-bin/haarcascade_frontalface_default.xml')
def faceextrator(img):
	gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
	faces=face_cascade.detectMultiScale(gray,1.3,5)
	if faces is ():
		return None
	for (x,y,w,h) in faces:
		cropped=img[y:y+h,x:x+w]
	return cropped


face_classifier = cv2.CascadeClassifier('/var/www/cgi-bin/haarcascade_frontalface_default.xml')
def face_detector(img, size=0.5):
	# Convert image to grayscale
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	faces = face_classifier.detectMultiScale(gray, 1.3, 5)
	if faces is ():
		return img,[]

	for (x, y, w, h) in faces:
		cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 255), 2)
		roi = img[y:y + h, x:x + w]
		roi = cv2.resize(roi, (200, 200))
	return img, roi


def gen(camera):

	data_path = '/var/www/faces/user/'
	onlyfiles = [f for f in listdir(data_path) if isfile(join(data_path, f))]

	# Create arrays for training data and labels
	Training_Data, Labels = [], []

	# Open training images in our datapath
	# Create a numpy array for training data
	for i, files in enumerate(onlyfiles):
		image_path = data_path + onlyfiles[i]
		images = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
		Training_Data.append(np.asarray(images, dtype=np.uint8))
		Labels.append(i)

	# Create a numpy array for both training data and labels
	Labels = np.asarray(Labels, dtype=np.int32)

	# Initialize facial recognizer
	model = cv2.face_LBPHFaceRecognizer.create()
	# NOTE: For OpenCV 3.0 use cv2.face.createLBPHFaceRecognizer()

	# Let's train our model
	model.train(np.asarray(Training_Data), np.asarray(Labels))
	print("Model trained sucessfully")

	while True:
		frame = camera.get_frame1()
		image, face = face_detector(frame)
		try:
			face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
			results = model.predict(face)
			print(results)
			if results[1] < 500:
				confidence = int(100 * (1 - (results[1]) / 400))
				display_string = str(confidence) + '% Confident it is User'
				cv2.putText(image, display_string, (100, 120), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 120, 150), 2)
			if confidence > 85:
				cv2.putText(image, "Hey User", (250, 450), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
				ret1, jpeg1 = cv2.imencode('.jpg', image)
				jpeg1 = jpeg1.tobytes()
			else:
				cv2.putText(image, "Locked", (250, 450), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
				ret1,jpeg1 = cv2.imencode('.jpg', image)
				jpeg1 = jpeg1.tobytes()

		except:
			cv2.putText(image, "No Face Found", (220, 120), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
			cv2.putText(image, "Locked", (250, 450), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
			ret1, jpeg1 = cv2.imencode('.jpg', image)
			jpeg1 = jpeg1.tobytes()
			pass

		yield (b'--frame\r\n' 
			   b'Content-Type: image/jpeg\r\n\r\n' + jpeg1 + b'\r\n\r\n')



	
@app.route('/video_feed')
def video_feed():
    return Response(gen(VideoCamera()),mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
	app.run(host='0.0.0.0',port=1236)

