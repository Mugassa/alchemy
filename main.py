# Modifications
#Include flask login extension for logins and logouts.
# add admin_required and login required decorators.
# include option for if forgot password
# shiftendtime should be beyond start time.
# location for accountability track
# prompt box shift set succesfully
# shiftdate should be ahead of current date.
# shiftend time should be ahead of starttime.
# one admin for each company
# shift expiry time
# notifications
# 

# swap shifts
# cancelshifts
# shift report
# coincidences to approve
# request change
# manager to query report#

import mysql.connector
from flask import Flask, request, jsonify,redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, exists,func
from sqlalchemy.orm import relationship
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import requests
from datetime import datetime, date, timedelta
import time
import base64

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://Howard:12345678@localhost:3306/test'
app.config['SECRET_KEY'] = 'Ntigwambukwa12'

login_manager = LoginManager(app)
db = SQLAlchemy(app)

with app.app_context():
    
    class User(UserMixin, db.Model):
        __tablename__="users"
        id = db.Column(db.Integer, primary_key=True)
        firstname = db.Column(db.String(120), nullable=False)
        lastname = db.Column(db.String(120), nullable=False)
        #fullname = db.Column(db.String(120), nullable=False)
        emailaddress = db.Column(db.String(120), unique=True)
        username = db.Column(db.String(80), unique=True, nullable=False)
        password = db.Column(db.String(120), nullable=False)
        role = db.Column(db.String(120), nullable=False)
        about = db.Column(db.String(500))
        company = db.Column(db.String(100))
        job = db.Column(db.String(100))
        profilepic = db.Column(db.LargeBinary)
        shifts = relationship('Shift', backref='user')
        shiftrequests = relationship('ShiftRequest', backref='user')
        notifications = relationship('Notification', backref='user')
        #userinfo = relationship('Userinfo', backref='user')

    class Shift(db.Model):
        __tablename__="shifts"
        id = db.Column(db.Integer, primary_key=True)
        employeename = db.Column(db.String(120), nullable=False)
        company = db.Column(db.String(100))
        job = db.Column(db.String(100))
        userid = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
        shiftdate = db.Column(db.Date, nullable=False)
        shiftstarttime = db.Column(db.Time, nullable=False)
        shiftendtime = db.Column(db.Time, nullable=False)
        shiftrequestreason = db.Column(db.String(500))
        approved = db.Column(db.Integer, default=0)
        createdat = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def delete_old_records():
        cutoff_date = datetime.utcnow() - timedelta(days=7) 
        Shift.query.filter(Shift.createdat < cutoff_date).delete()
        db.session.commit()

    
    class Attendance(db.Model):
        __tablename__="attendances"
        id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        employeename = db.Column(db.String(120), nullable=False)
        userid = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
        latitude = db.Column(db.Float, nullable=False)
        longitude = db.Column(db.Float, nullable=False)
        address = db.Column(db.String(250))
        date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
        createdat = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

        user = db.relationship('User', backref=db.backref('attendances', lazy=True))
    
    class ShiftRequest(db.Model):
        __tablename__="shiftrequests"
        id = db.Column(db.Integer, primary_key=True)
        employeename = db.Column(db.String(120), nullable=False)
        userid = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
        requesteddate = db.Column(db.Date, nullable=False)
        shiftstarttime = db.Column(db.Time, nullable=False)
        shiftendtime = db.Column(db.Time, nullable=False)
        shiftrequestreason = db.Column(db.String(500))

    class Notification(db.Model):
        __tablename__="notifications"
        id = db.Column(db.Integer, primary_key=True)
        employeename = db.Column(db.String(120), nullable=False)
        userid = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
        message = db.Column(db.String(120),nullable=False)
        is_Read = db.Column(db.Boolean, default=False)
    '''
    class Userinfo(db.Model):
        __tablename__="userinfo"
        id = db.Column(db.Integer, primary_key=True)
        userid = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
        fullname = db.Column(db.String(120), nullable=False)
        about = db.Column(db.String(500))
        company = db.Column(db.String(100))
        job = db.Column(db.String(100))
        '''
    db.create_all()

    delete_old_records()

@app.route("/register/")
def register():
    return render_template("pages-register-edit.html")
    #return render_template("register.html")

@app.route("/storeuser/", methods = ['POST'])
def storeuser():
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        emailaddress = request.form['emailaddress']
        username = request.form['username']
        password = request.form['password']
        repassword = request.form['repassword']
        role = request.form['role']

        if db.session.query(User).filter(User.emailaddress==emailaddress).count()==0:
            if password != repassword:
                return render_template("pages-register-edit.html", text1="Entered Password MUST be same as Re-entered password")
            user = User(firstname=firstname,lastname=lastname,emailaddress=emailaddress,username=username,password=password,role=role) 
            db.session.add(user)
            db.session.commit()
            login_user(user)
            if user.role == 'Admin':
                return redirect(url_for('adminhome'))
                #return redirect(url_for('adminhome'))
            else:
                return redirect(url_for('providerhome'))
                #return redirect(url_for('providerhome'))
    return render_template("pages-register-edit.html", text="The Email Address was already used")
    #return render_template("register.html", text="The Email Address was already used")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template("pages-login-edit.html")

@app.route("/authenticateuser", methods = ['POST'])    
def authenticateuser():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user:
            if user.password != password:
                return render_template("pages-login-edit.html", 
                text="Wrong password, Please re-check it")
        #if user and user.password == password:
            login_user(user)
            if user.role == 'Admin':
                return redirect(url_for('adminhome'))
            else:
                return redirect(url_for('providerhome'))
        else:
            return render_template("pages-login-edit.html", 
                text="Seems like you do not have an account, Click the link below to register yourself")
        return render_template("pages-login-edit.html")


'''
@app.route('/upload', methods=['POST'])
def uploadfile():
    if request.method == 'POST':
        file = request.files['file']
        fullname = f'{current_user.firstname} {current_user.lastname}'
        checker = db.session.query(User).filter(User.firstname +' '+ User.lastname==fullname).first()
        checker.profilepic = file.read()
        db.session.commit()
        return "Image uploaded successfully"
    return redirect(url_for('providerhome'))
'''

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/about/')
def about():
    return render_template("about.html")

@app.route('/mark_as_read/<int:notification_id>')
@login_required
def mark_as_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    notification.is_Read = True
    db.session.commit()
    return redirect(url_for('providerhome'))

@app.route('/mark_as_readmin/<int:notification_id>')
@login_required
def mark_as_readmin(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    notification.is_Read = True
    db.session.commit()
    return redirect(url_for('adminhome'))

#PROVIDER FUNCTIONS
@app.route('/providerhome/')
@login_required
def providerhome():
    company = f"{current_user.company}"
    about = f"{current_user.about}"
    job = f"{current_user.job}"

    #text = f"Welcome, {current_user.firstname}"
    name = f"{current_user.firstname} {current_user.lastname}"
    email = f"{current_user.emailaddress}"
    notifications = Notification.query.filter_by(employeename=current_user.firstname+' '+current_user.lastname, is_Read=False).all()

    fullname = f'{current_user.firstname} {current_user.lastname}'
    checker = db.session.query(User).filter(User.firstname +' '+ User.lastname==fullname).first()  
    if checker.profilepic:
        imagedata = base64.b64encode(checker.profilepic).decode('utf-8')
        imagesrc = f"data:image/jpeg;base64,{imagedata}"
    else:
        imagesrc = None

    return render_template("provider-profile-edit.html", name=name, company=company,job=job,
                                                        imagesrc=imagesrc,notifications=notifications,about=about,email=email)



@app.route('/providerhome/editprofile', methods=['POST'])
@login_required
def proviiderhome():
    
    if request.method == 'POST':
        file = request.files['file']
        about = request.form['about']
        company = request.form['company']
        job = request.form['job']

        fullname = f'{current_user.firstname} {current_user.lastname}'
        checker = db.session.query(User).filter(User.firstname +' '+ User.lastname==fullname).first()
        checker.about = about
        checker.company = company
        checker.job = job
        checker.profilepic = file.read()
        #updates = User(about=about,company=company,job=job) 
        #db.session.add(updates)
        db.session.commit()
        

    fullname = f'{current_user.firstname} {current_user.lastname}'
    checker = db.session.query(User).filter(User.firstname +' '+ User.lastname==fullname).first()  
    if checker.profilepic:
        imagedata = base64.b64encode(checker.profilepic).decode('utf-8')
        imagesrc = f"data:image/jpeg;base64,{imagedata}"
    else:
        imagesrc = None
    
    #checker = User.query.filter_by(fullname =name).first()
    
    company = f"{current_user.company}"
    about = f"{current_user.about}"
    job = f"{current_user.job}"
    profilepic = {current_user.profilepic}

    #text = f"Welcome, {current_user.firstname}"
    name = f"{current_user.firstname} {current_user.lastname}"
    email = f"{current_user.emailaddress}"
    notifications = Notification.query.filter_by(employeename=current_user.firstname+' '+current_user.lastname, is_Read=False).all()
    return render_template("provider-profile-edit.html", name=name, notifications=notifications,company=company,job=job,imagesrc=imagesrc,
                                                        about=about,email=email)


@app.route('/providerhome/changepassword', methods=['POST'])
@login_required
def changepassword():
    
    if request.method == 'POST':
        currentpassword = request.form['currentpassword']
        newpassword = request.form['newpassword']
        renewpassword = request.form['renewpassword']

        company = f"{current_user.company}"
        about = f"{current_user.about}"
        job = f"{current_user.job}"

        text = f"Welcome, {current_user.firstname}"
        name = f"{current_user.firstname} {current_user.lastname}"
        email = f"{current_user.emailaddress}"
        fullname = f'{current_user.firstname} {current_user.lastname}'
        notifications = Notification.query.filter_by(employeename=current_user.firstname+' '+current_user.lastname, is_Read=False).all()
        checker = db.session.query(User).filter(User.firstname +' '+ User.lastname==fullname).first()
        
        if checker.password == currentpassword:
            if newpassword == renewpassword:
                checker.password = newpassword
                db.session.commit()
                success = f'Password changed succesfully'
                return render_template("provider-profile-edit.html", success=success,name=name,notifications=notifications, company=company,job=job,
                                                        about=about,email=email, text=text)
            else:
                message = f"New password should be same as re entersed password"
                return render_template("provider-profile-edit.html",name=name, company=company,job=job,
                                                        about=about,email=email,notifications=notifications, text=text,message=message)
        else:
            message1 = f"Incorrect current password"
            return render_template("provider-profile-edit.html",name=name,notifications=notifications, company=company,job=job,
                                                        about=about,email=email, text=text,message1=message1)
        
    #checker = User.query.filter_by(fullname =name).first()
    
    
    return render_template("provider-profile-edit.html", name=name, company=company,job=job,notifications=notifications,
                                                        about=about,email=email, text=text)


@app.route('/home/viewschedule')
@login_required
def viewschedule():
    hifts = Shift.query.filter_by(employeename=f'{current_user.firstname} {current_user.lastname}')
    if hifts:
        shifts = hifts.filter_by(approved=1)        
        #shiftdatetime = datetime.combine(shifts.shiftdate, datetime.min.time())
        #day = shifts.shiftdate.strftime("%A")
        name = f"{current_user.firstname} {current_user.lastname}"

        fullname = f'{current_user.firstname} {current_user.lastname}'
        checker = db.session.query(User).filter(User.firstname +' '+ User.lastname==fullname).first()  
        if checker.profilepic:
            imagedata = base64.b64encode(checker.profilepic).decode('utf-8')
            imagesrc = f"data:image/jpeg;base64,{imagedata}"
        else:
            imagesrc = None
        
        job = f"{current_user.job}"
        notifications = Notification.query.filter_by(employeename=current_user.firstname+' '+current_user.lastname, is_Read=False).all()

        return render_template("pages-viewschedule-edit.html", job=job,name=name,notifications=notifications,imagesrc=imagesrc,shifts = shifts)

@app.route('/home/requestshift')
@login_required
def requestshift():
    name = f"{current_user.firstname} {current_user.lastname}"

    fullname = f'{current_user.firstname} {current_user.lastname}'
    checker = db.session.query(User).filter(User.firstname +' '+ User.lastname==fullname).first()  
    if checker.profilepic:
        imagedata = base64.b64encode(checker.profilepic).decode('utf-8')
        imagesrc = f"data:image/jpeg;base64,{imagedata}"
    else:
        imagesrc = None
    
    job = f"{current_user.job}"
    notifications = Notification.query.filter_by(employeename=current_user.firstname+' '+current_user.lastname, is_Read=False).all()

    return render_template("pages-requestschedule-edit.html", job=job,name=name,notifications=notifications,imagesrc=imagesrc)

@app.route('/home/requestshiftsave', methods = ['POST'])
@login_required
def requestshiftsave():
    if request.method == 'POST':
        requesteddate = request.form['requesteddate']
        shiftstarttime = request.form['shiftstarttime']
        shiftendtime = request.form['shiftendtime']
        shiftrequestreason = request.form['shiftrequestreason']

        fullname = f'{current_user.firstname} {current_user.lastname}'
        checker = db.session.query(User).filter(User.firstname +' '+ User.lastname==fullname).first()  
        if checker.profilepic:
            imagedata = base64.b64encode(checker.profilepic).decode('utf-8')
            imagesrc = f"data:image/jpeg;base64,{imagedata}"
        else:
            imagesrc = None

        name = f"{current_user.firstname} {current_user.lastname}"
        notifications = Notification.query.filter_by(employeename=current_user.firstname+' '+current_user.lastname, is_Read=False).all()

        dateobj = datetime.strptime(requesteddate, "%Y-%m-%d").date()
        timeobj = datetime.strptime(shiftstarttime, "%H:%M").time()
        #if db.session.query(User).filter_by(firstname=f'{current_user.firstname}'):
        if (dateobj >= date.today()):
            if (shiftendtime > shiftstarttime):
                if (timeobj >= datetime.now().time()):
                    userid = db.session.query(User).filter(User.firstname+' '+User.lastname == current_user.firstname+' '+current_user.lastname).first().id
                    company = current_user.company
                    name = f"{current_user.firstname} {current_user.lastname}"
                    quest = Shift(employeename=name,company=company,userid=userid,shiftdate=requesteddate,shiftstarttime=shiftstarttime,shiftendtime=shiftendtime,shiftrequestreason=shiftrequestreason)
                    success = f"Your Request was sent Successfully"
                    db.session.add(quest)

                    myadmin = User.query.filter_by(role='Admin',company=current_user.company).first()
                    employeename = myadmin.firstname+' '+myadmin.lastname
                    user_id = myadmin.id
                    notification_message = f"You have a Shift Request"
                    notification = Notification(employeename=employeename,userid=user_id,message=notification_message)
                    db.session.add(notification)

                    db.session.commit()
                else:
                    warn1 = f"Please check, Your start time selection is Overdue"
                    return render_template("pages-requestschedule-edit.html", imagesrc=imagesrc,notifications=notifications,name=name, warn1=warn1)
            else:
                warn2 = f"Please check, Your Ending time is prior to Start time"
                return render_template("pages-requestschedule-edit.html", imagesrc=imagesrc,notifications=notifications,name=name, warn2=warn2)
        else:
            warn3 = f"Your Date is invalid!, it has already pass"
            return render_template("pages-requestschedule-edit.html", imagesrc=imagesrc,notifications=notifications,name=name, warn3=warn3)

        
        
    return render_template("pages-requestschedule-edit.html", imagesrc=imagesrc,notifications=notifications,name=name, success=success)

def reverse_geocode(lat, lon):
    url = f'https://nominatim.openstreetmap.org/reverse'
    params = {
        'format': 'json',
        'lat': lat,
        'lon': lon,
        'zoom': 18,
        'addressdetails': 1
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data

@app.route('/home/attendance')
@login_required
def myattendance():
    name = f"{current_user.firstname} {current_user.lastname}"

    fullname = f'{current_user.firstname} {current_user.lastname}'
    checker = db.session.query(User).filter(User.firstname +' '+ User.lastname==fullname).first()  
    if checker.profilepic:
        imagedata = base64.b64encode(checker.profilepic).decode('utf-8')
        imagesrc = f"data:image/jpeg;base64,{imagedata}"
    else:
        imagesrc = None
    
    job = f"{current_user.job}"
    notifications = Notification.query.filter_by(employeename=current_user.firstname+' '+current_user.lastname, is_Read=False).all()

    return render_template("pages-attendance-edit.html", name=name,job=job,notifications=notifications,imagesrc=imagesrc)

@app.route('/home/attendancesubmit', methods=['POST'])
@login_required
def myattendancesubmit():
    name = f"{current_user.firstname} {current_user.lastname}"

    fullname = f'{current_user.firstname} {current_user.lastname}'
    checker = db.session.query(User).filter(User.firstname +' '+ User.lastname==fullname).first()  
    if checker.profilepic:
        imagedata = base64.b64encode(checker.profilepic).decode('utf-8')
        imagesrc = f"data:image/jpeg;base64,{imagedata}"
    else:
        imagesrc = None

    if 'locationCheckbox' in request.form:
        if request.method == 'POST':
            latitude = request.form['latitude']
            longitude = request.form['longitude']
            userid = db.session.query(User).filter(User.firstname+' '+User.lastname == current_user.firstname+' '+current_user.lastname).first().id
            notifications = Notification.query.filter_by(employeename=current_user.firstname+' '+current_user.lastname, is_Read=False).all()

            if latitude and longitude:
                location_data = reverse_geocode(latitude, longitude)
                address = location_data.get('display_name', 'Address not found')

                attendance = Attendance(employeename=fullname,userid=userid, latitude=latitude, longitude=longitude,address=address)
                db.session.add(attendance)
                db.session.commit()
                success = "Location stored successfully"
                return render_template("pages-attendance-edit.html", success=success,notifications=notifications,name=name,imagesrc=imagesrc)
    warnn = "Location not stored or checkbox not checked or location unavailable"

    return render_template("pages-attendance-edit.html", warnn=warnn,notifications=notifications,name=name,imagesrc=imagesrc)

#END OF PROVIDERS FUNCTIONS


#ADMIN FUNCTIONS
@app.route('/adminhome/')
@login_required
def adminhome():
    text = f"Hello, {current_user.firstname}"
    email = f"{current_user.emailaddress}"
    name = f"{current_user.firstname} {current_user.lastname}"

    company = f"{current_user.company}"
    about = f"{current_user.about}"
    job = f"{current_user.job}"

    fullname = f'{current_user.firstname} {current_user.lastname}'
    checker = db.session.query(User).filter(User.firstname +' '+ User.lastname==fullname).first()  
    if checker.profilepic:
        imagedata = base64.b64encode(checker.profilepic).decode('utf-8')
        imagesrc = f"data:image/jpeg;base64,{imagedata}"
    else:
        imagesrc = None

    notifications = Notification.query.filter_by(employeename=fullname, is_Read=False).all()
    employees = User.query.filter(and_(User.role == 'HealthcareProvider', User.company == company)).all()
    employeecount = User.query.filter(and_(User.role == 'HealthcareProvider', User.company == company)).count()
    indexes = list(range(0,employeecount))

    return render_template("admin-profile-edit.html", name=name, email=email, text=text,job=job,notifications=notifications,
                                                    company=company,employees=employees,about=about,imagesrc=imagesrc)


@app.route('/adminhome/companyconfirm', methods=['POST'])
@login_required
def companyconfirm():
    if request.method == 'POST':
        company = request.form['company']
    
    fullname = f'{current_user.firstname} {current_user.lastname}'
    warnn = ""

    adminexists = db.session.query(exists().where(and_(User.role == 'Admin', User.company == company))).scalar()

    if adminexists:
        warnn = "An Admin for this company already exists"
            
    else:
        checker = db.session.query(User).filter(User.firstname +' '+ User.lastname==fullname).first()  
        checker.company = company  

    db.session.commit() 


    checker = db.session.query(User).filter(User.firstname +' '+ User.lastname==fullname).first()  
    if checker.profilepic:
        imagedata = base64.b64encode(checker.profilepic).decode('utf-8')
        imagesrc = f"data:image/jpeg;base64,{imagedata}"
    else:
        imagesrc = None

    company = f"{current_user.company}"
    about = f"{current_user.about}"
    job = f"{current_user.job}"
    profilepic = {current_user.profilepic}
    name = f"{current_user.firstname} {current_user.lastname}"
    email = f"{current_user.emailaddress}"
    notifications = Notification.query.filter_by(employeename=fullname, is_Read=False).all()
    
    return render_template("admin-profile-edit.html", name=name, company=company,job=job,notifications=notifications,imagesrc=imagesrc,
                                                        warnn=warnn,about=about,email=email)


@app.route('/adminhome/editprofile', methods=['POST'])
@login_required
def admiinhome():
    
    if request.method == 'POST':
        file = request.files['file']
        about = request.form['about']
        job = request.form['job']


        fullname = f'{current_user.firstname} {current_user.lastname}'
        checker = db.session.query(User).filter(User.firstname +' '+ User.lastname==fullname).first()
           
        checker.about = about
        checker.job = job
        checker.profilepic = file.read()
        #updates = User(about=about,company=company,job=job) 
        #db.session.add(updates)
        db.session.commit()

        checker = db.session.query(User).filter(User.firstname +' '+ User.lastname==fullname).first()  
        if checker.profilepic:
            imagedata = base64.b64encode(checker.profilepic).decode('utf-8')
            imagesrc = f"data:image/jpeg;base64,{imagedata}"
        else:
            imagesrc = None
    
        company = f"{current_user.company}"
        about = f"{current_user.about}"
        job = f"{current_user.job}"
        profilepic = {current_user.profilepic}
        name = f"{current_user.firstname} {current_user.lastname}"
        email = f"{current_user.emailaddress}"
        notifications = Notification.query.filter_by(employeename=fullname, is_Read=False).all()
    
    return render_template("admin-profile-edit.html", name=name, company=company,job=job,notifications=notifications,imagesrc=imagesrc,
                                                        about=about,email=email)



@app.route('/adminhome/setschedule')
@login_required
def setschedule():
    options = User.query.filter(and_(User.role == 'HealthcareProvider', User.company == current_user.company)).all()
    name = f"{current_user.firstname} {current_user.lastname}"

    fullname = f'{current_user.firstname} {current_user.lastname}'
    
    checker = db.session.query(User).filter(User.firstname +' '+ User.lastname==fullname).first()  
    if checker.profilepic:
        imagedata = base64.b64encode(checker.profilepic).decode('utf-8')
        imagesrc = f"data:image/jpeg;base64,{imagedata}"
    else:
        imagesrc = None

    job = f"{current_user.job}"

    shifts = Shift.query.all()
    notifications = Notification.query.filter_by(employeename=fullname, is_Read=False).all()
    return render_template("pages-setschedule-edit.html",name=name,job=job,shifts=shifts,notifications=notifications,imagesrc=imagesrc, options=options)

@app.route('/storeschedule', methods = ['POST'])
def storeschedule():

    if request.method == 'POST':
        if request.form['gridRadios'] == 'daily':
            employeename = request.form['employeename']
            #userid = request.form['userid']
            shiftdate = request.form['shiftdate']
            shiftstarttime = request.form['shiftstarttime']
            shiftendtime = request.form['shiftendtime']

            fullname = f'{current_user.firstname} {current_user.lastname}'
            checker = db.session.query(User).filter(User.firstname +' '+ User.lastname==fullname).first()  
            if checker.profilepic:
                imagedata = base64.b64encode(checker.profilepic).decode('utf-8')
                imagesrc = f"data:image/jpeg;base64,{imagedata}"
            else:
                imagesrc = None

            name = f"{current_user.firstname} {current_user.lastname}"

            notifications = Notification.query.filter_by(employeename=fullname, is_Read=False).all()

            dateobj = datetime.strptime(shiftdate, "%Y-%m-%d").date()
            timeobj = datetime.strptime(shiftstarttime, "%H:%M").time()
            #if db.session.query(User).filter_by(firstname=f'{current_user.firstname}'):
            if (dateobj >= date.today()):
                if (shiftendtime > shiftstarttime):
                    if (timeobj >= datetime.now().time()):
                        userid = db.session.query(User).filter(User.firstname+' '+User.lastname == current_user.firstname+' '+current_user.lastname).first().id
                        company = current_user.company
                        firstname, lastname = employeename.split(' ', 1)
                        userr = User.query.filter(
                                func.concat(User.firstname, ' ', User.lastname) == employeename
                            ).first()
                        name = f"{current_user.firstname} {current_user.lastname}"
                        approved = True
                        shift = Shift(employeename=employeename,company=company,job=userr.job,userid=userid,shiftdate=shiftdate,shiftstarttime=shiftstarttime,shiftendtime=shiftendtime,approved=approved)
                        success = f"The Shift was Set Successfully"
                        db.session.add(shift)

                        notification_message = f"New Schedule Set on {shiftdate}"
                        notification = Notification(employeename=employeename,userid=userid,message=notification_message)
                        db.session.add(notification)

                        db.session.commit()
                    else:
                        warn1 = f"Please check, Your start time selection is Overdue"
                        return render_template("pages-setschedule-edit.html", imagesrc=imagesrc,notifications=notifications,name=name, warn1=warn1)
                else:
                    warn2 = f"Please check, Your Ending time is prior to Start time"
                    return render_template("pages-setschedule-edit.html", imagesrc=imagesrc,notifications=notifications,name=name, warn2=warn2)
            else:
                warn3 = f"Your Date is invalid!, it has already pass"
                return render_template("pages-setschedule-edit.html", imagesrc=imagesrc,notifications=notifications,name=name, warn3=warn3)

            success = f"The Shift was Set Successfully"
            options = User.query.filter_by(role='HealthcareProvider').all()
            
            #return redirect(url_for('setschedule'))
        elif request.form['gridRadios'] == 'weekly':
            employeename = request.form['employeename']
            week = request.form['shiftweek']
            year, week_num = map(int, week.split('-W'))
            first_day_of_week = datetime.strptime(f'{year}-W{week_num-1}-1', '%Y-W%W-%w').date()
            
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
            for i, day in enumerate(days):
                shiftstarttime = request.form[f'{day}_shiftstarttime']
                shiftendtime = request.form[f'{day}_shiftendtime']
                shiftdate = first_day_of_week + timedelta(days=i)

                # Convert to datetime objects
                shiftstarttime = datetime.strptime(shiftstarttime, "%H:%M").time()
                shiftendtime = datetime.strptime(shiftendtime, "%H:%M").time()

                # Check user profile
                fullname = f'{current_user.firstname} {current_user.lastname}'
                checker = db.session.query(User).filter(func.concat(User.firstname, ' ', User.lastname) == fullname).first()  
                if checker.profilepic:
                    imagedata = base64.b64encode(checker.profilepic).decode('utf-8')
                    imagesrc = f"data:image/jpeg;base64,{imagedata}"
                else:
                    imagesrc = None

                name = f"{current_user.firstname} {current_user.lastname}"
                notifications = Notification.query.filter_by(employeename=fullname, is_Read=False).all()

                # Validate date and time
                if shiftdate >= date.today():
                    if shiftendtime > shiftstarttime:
                        if shiftstarttime >= datetime.now().time():
                            userid = db.session.query(User).filter(func.concat(User.firstname, ' ', User.lastname) == fullname).first().id
                            company = current_user.company
                            userr = db.session.query(User).filter(func.concat(User.firstname, ' ', User.lastname) == employeename).first()
                            
                            # Create Shift
                            shift = Shift(
                                employeename=employeename,
                                company=company,
                                job=userr.job,
                                userid=userid,
                                shiftdate=shiftdate,
                                shiftstarttime=shiftstarttime,
                                shiftendtime=shiftendtime
                            )
                            db.session.add(shift)

                            # Create Notification
                            notification_message = f"New Schedule Set on {shiftdate}"
                            notification = Notification(employeename=employeename, userid=userid, message=notification_message)
                            db.session.add(notification)

                            db.session.commit()
                        else:
                            warn1 = "Please check, Your start time selection is Overdue"
                            return render_template("pages-setschedule-edit.html", imagesrc=imagesrc, notifications=notifications, name=name, warn1=warn1)
                    else:
                        warn2 = "Please check, Your Ending time is prior to Start time"
                        return render_template("pages-setschedule-edit.html", imagesrc=imagesrc, notifications=notifications, name=name, warn2=warn2)
                else:
                    warn3 = "Your Date is invalid!, it has already passed"
                    return render_template("pages-setschedule-edit.html", imagesrc=imagesrc, notifications=notifications, name=name, warn3=warn3)

            success = "The Shift was Set Successfully"
            options = User.query.filter_by(role='HealthcareProvider').all()
            return render_template("pages-setschedule-edit.html", success=success, notifications=notifications, imagesrc=imagesrc, name=name, options=options)

    return render_template("pages-setschedule-edit.html")

@app.route('/adminhome/viewshiftrequests')
@login_required
def viewshiftrequests():
    shiftrequests = Shift.query.filter(Shift.approved==0).all()
    name = f"{current_user.firstname} {current_user.lastname}"

    fullname = f'{current_user.firstname} {current_user.lastname}'
    checker = db.session.query(User).filter(User.firstname +' '+ User.lastname==fullname).first()  
    if checker.profilepic:
        imagedata = base64.b64encode(checker.profilepic).decode('utf-8')
        imagesrc = f"data:image/jpeg;base64,{imagedata}"
    else:
        imagesrc = None

    job = f"{current_user.job}"
    notifications = Notification.query.filter_by(employeename=fullname, is_Read=False).all()
    return render_template("pages-viewrequests-edit.html", name=name,job=job,imagesrc=imagesrc,notifications=notifications, shiftrequests=shiftrequests)



@app.route('/adminhome/approverequests', methods = ['POST'])
@login_required
def approverequests():
    
    if request.method == 'POST':
        userid = request.form['userid']
        approve = request.form['approve']

        shift = Shift.query.filter_by(id=userid).first()
        employeename = shift.employeename
        user_id = shift.userid

        if shift:   
            if shift.approved == '2':
                db.session.delete()
                notification_message = f"Your requested schedule has been Declined"
                notification = Notification(employeename=employeename,userid=user_id,message=notification_message)
                db.session.add(notification)

                db.session.commit()
                return redirect(url_for('viewshiftrequests'))
            else:
                shift.approved = approve
                notification_message = f"Your requested schedule has been Approved"
                notification = Notification(employeename=employeename,userid=user_id,message=notification_message)
                db.session.add(notification)

                db.session.commit()
                return redirect(url_for('viewshiftrequests'))
        else:
            return 'False'
              
        #if db.session.query(User).filter(f'{User.firstname} {User.lastname}'==employeename):
        '''
        if db.session.query(Shift).filter(Shift.id==userid).first():
            shift = Shift(approved=approve)
            db.session.add(shift)
            db.session.commit()
            return redirect(url_for('about'))
            -schedule weekly
            -changes(swap)
            
        '''     
    shiftrequests = ShiftRequest.query.all()
    name = f"{current_user.firstname} {current_user.lastname}"
    notifications = Notification.query.filter_by(employeename=name, is_Read=False).all()
    return render_template("pages-viewrequests-edit.html", name=name,notifications=notifications,shiftrequests=shiftrequests)


@app.route('/adminhome/trackattendance')
@login_required
def trackattendance():
    attendances = Attendance.query.all()
    name = f"{current_user.firstname} {current_user.lastname}"

    fullname = f'{current_user.firstname} {current_user.lastname}'
    checker = db.session.query(User).filter(User.firstname +' '+ User.lastname==fullname).first()  
    if checker.profilepic:
        imagedata = base64.b64encode(checker.profilepic).decode('utf-8')
        imagesrc = f"data:image/jpeg;base64,{imagedata}"
    else:
        imagesrc = None

    job = f"{current_user.job}"
    notifications = Notification.query.filter_by(employeename=fullname, is_Read=False).all()
    return render_template("pages-trackattendance-edit.html", name=name,job=job, notifications=notifications,imagesrc=imagesrc,attendances=attendances)


@app.route('/adminhome/viewinsights')
@login_required
def viewinsights():
    name = f"{current_user.firstname} {current_user.lastname}"

    fullname = f'{current_user.firstname} {current_user.lastname}'
    checker = db.session.query(User).filter(User.firstname +' '+ User.lastname==fullname).first()  
    if checker.profilepic:
        imagedata = base64.b64encode(checker.profilepic).decode('utf-8')
        imagesrc = f"data:image/jpeg;base64,{imagedata}"
    else:
        imagesrc = None

    job = f"{current_user.job}"
    notifications = Notification.query.filter_by(employeename=fullname, is_Read=False).all()
    insights = Shift.query().filter_by(company=current_user.company).all()
    return render_template("pages-viewinsights.html", name=name,insights=insights,notifications=notifications,job=job, imagesrc=imagesrc)
#END OF ADMIN FUNCTIONS
#END OF ADMIN FUNCTIONS


if __name__ == '__main__':
    app.run(debug=True)
