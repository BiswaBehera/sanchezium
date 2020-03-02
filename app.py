from flask import Flask, render_template, request, redirect, url_for,session,Response
from flask_sqlalchemy import SQLAlchemy
import pymysql
from flask_mail import Mail
import urllib.request as urllib2
import mysql.connector
from mysql.connector import Error
import json
from PIL import Image
import cv2
import time
import qrcode
from pyzbar import pyzbar
import qrcode.image.svg
import argparse
import datetime
import imutils
from imutils.video import VideoStream
import os
proxy_support = urllib2.ProxyHandler({"http":"http://61.233.25.166:80"})
opener = urllib2.build_opener(proxy_support)
urllib2.install_opener(opener)
app = Flask(__name__)
app.secret_key = '12345678'
# app.config['SESSION_TYPE'] = 'filesystem'

# session.init_app(app)
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = '99jagannath@gmail.com',
    MAIL_PASSWORD=  'nuapatna'
)
mail = Mail(app)



pymysql.install_as_MySQLdb()


app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/flask'
connection = mysql.connector.connect(host='localhost',
                                         database='flask',
                                         user='root',
                                         password='')
db = SQLAlchemy(app)
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    sub = db.Column(db.String(120), nullable=False)
    msg = db.Column(db.String(220), nullable=False)
class Speakers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    about = db.Column(db.String(50), nullable=False)
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    photo = db.Column(db.String(100), nullable=False) 
    price = db.Column(db.String(100), nullable=False)
    barcode = db.Column(db.String(100), nullable=False) 
class Temp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, nullable=False) 
    approved = db.Column(db.Integer,default=0)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(50), nullable=False) 
class Retail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(50), nullable=False)       
              

k=0

@app.route('/')
def home():
    speakers = Speakers.query.filter_by().all()
    return render_template('index.html',speakers = speakers)

@app.route('/scan_your_product')
def test():
    return render_template('test.html')  
@app.route('/resister')
def resister():
    return render_template('resister.html') 
@app.route('/resistration',methods=['GET','POST'])
def resistration():
    if(request.method=='POST'):
        email = request.form.get('email')
        password = request.form.get('password')
        entry = User(email=email,password=password)
        db.session.add(entry)
        db.session.commit()
        return redirect(url_for('resister'))
@app.route('/login')
def login():
    return render_template('login.html')        

@app.route('/login_check', methods=['POST'])
def login_check():
    email = request.form['email'].strip()
    password = request.form['password']
    auth_data = User.query.filter_by(email=email).first()
    if(auth_data):
        if(auth_data.password == password):
            session['id'] = auth_data.id
            session['email'] = email
            return render_template('index.html')
        else:
            return render_template('login.html') 
    else:
        return render_template('login.html')         
@app.route('/profile')
def profile():
    if 'email' in session:
        if os.path.isfile("static/img/images/myqrq_"+str(session['id'])+".png"):
            print('achi')
            os.remove("static/img/images/myqrq_"+str(session['id'])+".png")
            
        else:
            print('nahi')

        qr = qrcode.QRCode(version=1,box_size=15,border=5)
        ids = Temp.query.filter_by(customer_id=session['id']).all()
        id_str = ''
        for id in ids:
            id_str=id_str+str(id.product_id)
            id_str=id_str+'_'
        qr.add_data(id_str)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        img.save("static/img/images/myqrq_"+str(session['id'])+".png")
        # if session['qr']:
        #     print('achi')
        #     session.pop('qr', None)
        session['qr']="/static/img/images/myqrq_"+str(session['id'])+".png"    
        return render_template('profile.html')
    else:
        return render_template('login.html')     
   
  

@app.route('/reatil_scan_here')
def retail_scan_here():
    print("[INFO] starting video stream...")
    vs = VideoStream(src=0).start()
    #time.sleep(0.5)
    # csv = open(args["output"], "a") #a
    found = set()
    while True:
        frame = vs.read()
        frame = imutils.resize(frame, width=400)
        barcodes = pyzbar.decode(frame)
        if barcodes:
            for barcode in barcodes:
                print('h')
                barcodeData = barcode.data.decode("utf-8")
                barcodeType = barcode.type
                print(barcodeData)
            vs.stop()
            break      
        print('l')
    l=[]   
    m=0
    for data in barcodeData:
        if m%2==0:
            l.append(data) 
        m=m+1    
    data =[]
    for id in l:
        details = Product.query.filter_by(id=id).first()
        data.append(details)
        rows_changed = Temp.query.filter_by(product_id=id).update(dict(approved=1))
        db.session.commit()              
    return render_template('retail_scan.html',products=data)  
@app.route('/remove_from_check_out',methods=['GET','POST'])
def remove_from_check_out():
    if(request.method=='POST'):
        id = request.form.get('id')
        details = Temp.query.filter_by(product_id=id).first()
        db.session.delete(details)
        db.session.commit()
    return redirect(url_for('check_out_list'))  

@app.route('/check_out_list',methods=['GET','POST'])
def check_out_list():
    
    if 'email' not in session:
        return redirect(url_for('login')) 
    products = Temp.query.filter_by().all()
    data=[]
    for product in products:
        details = Product.query.filter_by(id=product.product_id).first()
        data.append(details)
    return render_template('check_out_list.html',products_details=data)
@app.route('/add_check_out',methods=['GET','POST'])
def add_check_out():
    if(request.method=='POST'):
        id = request.form.get('id')
        print(id)
        entry = Temp(customer_id=1,product_id=id)
        db.session.add(entry)
        db.session.commit()
    return render_template('test.html')    
    
def gen(i):
    cap = cv2.VideoCapture(0)
    j=0
    timeout = time.time() + 60
    while(cap.isOpened()):
        if i==1:
            break
        ret, img = cap.read()
        img = cv2.resize(img, (0,0), fx=0.5, fy=0.5) 
        # if j==0:
        #     cv2.imwrite('jagannath.jpg',img) 
        #     j=j+1

        cv2.putText(img, 'jaga', (0, 30), cv2.FONT_HERSHEY_SIMPLEX,0.5, (0, 0, 255), 2)
        
        frame = cv2.imencode('.jpg', img)[1].tobytes()
        if k==0:
            if ret == True:
                    
                yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                time.sleep(0.1)
            else: 
                break
            
        else:
            if ret == True:
                # cv2.imwrite('static/img/images/jagannath3.jpg',img) 
                
                cur_img = cv2.imread('static/img/images/qr1.jpg')
                barcodes = pyzbar.decode(cur_img)
                print("[INFO] Found {} barcode: {}".format(barcodes[0].type, barcodes[0].data.decode("utf-8")))
                break
            else: 
                break

    cap.release()
    cv2.destroyAllWindows()        
           

@app.route('/catch',methods=['GET','POST'])
def catch():
    k=1
    cap1 = cv2.VideoCapture(0)
    ret, img = cap1.read()
    # img = cv2.resize(img, (0,0), fx=0.5, fy=0.5)
    if os.path.isfile("static/img/images/qr"+str(session['id'])+".png"):
        print('achi')
        os.remove("static/img/images/qr"+str(session['id'])+".png")        
    else:
        print('nahi') 
    cv2.imwrite("static/img/images/qr"+str(session['id'])+".png",img)
    cur_img = cv2.imread("static/img/images/qr"+str(session['id'])+".png")
    barcodes = pyzbar.decode(cur_img)
    barcodeData=0
    for barcode in barcodes:
        (x, y, w, h) = barcode.rect
        barcodeData = barcode.data.decode("utf-8")
        barcodeType = barcode.type
    cap1.release()
    cv2.destroyAllWindows()  
    print(barcodeData)
    details = Product.query.filter_by(barcode= barcodeData).first()
    print(details)
    return render_template('check_out.html',details=details)
       
        

    
@app.route('/user_logout')
def user_logout():
    session.pop('id', None)
    session.pop('email', None)
    session.pop('qr', None)
    return render_template('index.html')


@app.route('/video_feed',methods=['GET','POST'])
def video_feed():
    i=0
    if(request.method=='POST'):
        i=1
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(i),
                    mimetype='multipart/x-mixed-replace; boundary=frame') 
               
      
app.run(debug=True)    