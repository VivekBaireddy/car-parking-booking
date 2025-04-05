import flask
from flask import session,redirect,render_template,request,Flask,url_for
from DBConnection import Db
from datetime import datetime
import requests



application=Flask(__name__)
application.secret_key='12345'


@application.route('/',methods=['GET','POST'])
def home():
    return render_template('login.html') 

@application.route('/login',methods=['GET','POST'])
def login():
    if request.method== "GET":
        return render_template('login.html')
    else:
        username = request.form['your_name']
        password = request.form['your_pass']
        db = Db()
        data = db.selectOne('select * from user_master where user_username= %s and user_password=%s',(username,password)) 
        
        if data is not None:
            user_email=data['user_email']
            user_id=data['user_id']
            session['userid'] = user_id # set the username key in the session
            session['useremail'] = user_email 
            return redirect(url_for('index'))
        else:
            return '''<script>alert('user not found');window.location="/login"</script>'''

@application.route('/register',methods=['GET','POST'])
def register():
    if request.method== "GET":
        return render_template('register.html')
    else:
        username = request.form['name']
        email = request.form['email']
        password = request.form['pass']
        confirmPassword = request.form['re_pass'] 
        db = Db()
        qry = db.insert("INSERT INTO user_master (user_username, user_email, user_password) VALUES (%s, %s, %s)", (username,  email, password))
        if qry:
            return '<script>alert("User registered"); window.location.href="/login";</script>'
        else:
            return '<script>alert("User not registered"); window.location.href="/register";</script>'
   

@application.route('/index',methods=['GET','POST'])
def index():
    if 'userid' in session:
        if request.method == 'POST':
            area = request.form.get('area')
            db = Db()
            qry = db.select("select * from parking_area_master where pa_area = %s ", (area,))
            return render_template('find_parking.html', data=qry)       
        else:
            return render_template('index.html') 
    else:
        return redirect(url_for('home'))
        

@application.route('/findparking',methods=['GET','POST'])
def findparking():
    if 'userid' in session:
        if request.method == 'POST':
            id = request.form.get('areaid')
            db = Db()
            qry = db.selectOne("select * from parking_area_master where pa_id = %s ", (id,))
            return render_template('booking_form.html', data=qry)       
        else:
            return render_template('index.html') 
    else:
        return redirect(url_for('home'))


@application.route('/book',methods=['GET','POST'])
def book():
    if 'userid' not in session :
        return redirect('/')
    
    else:
        if request.method== 'POST':
            station_name = request.form['pa_name']
            area = request.form['pa_area']
            address = request.form['pa_address']
            slot =int( request.form['slot'])
            booking_date = request.form['date']
            time_from = request.form['time_from']
            time_to = request.form['time_to']
            user_id = session['userid']
            db = Db()
            # get the current timestamp
            created_at = datetime.now().strftime('%Y-%m-%d') 

            # Calculating the duration of parking 
            to_hr,to_min=time_to.split(":")
            to_hr,to_min=int(to_hr),int(to_min)
            from_hr,from_min=time_from.split(":")
            from_hr,from_min=int(from_hr),int(from_min)
            global duration
            duration=(abs(to_hr-from_hr)*60)+(abs(to_min-from_min))

            #calling the amount calculation api
            API_URL='http://x23337818-calculateapi.eba-xdnngu8m.ap-southeast-1.elasticbeanstalk.com/calculator'
            
            json_data={"duration":duration}
            try:
                response=requests.get(API_URL,json=json_data,stream=True)
                if response.status_code == 200:
                    data = response.json()
                    calculated_amt=data.get('calculated_amt')
                    converted_usd=data.get('converted_usd')
                    print(f"generated value --------> {calculated_amt} and in usd {converted_usd}")
                    sql = "INSERT INTO booking_t ( b_user, b_parking, b_area, b_slot, b_intime, b_outime, b_bookingdate, b_bookedfor, b_duration, b_amount, b_usd) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                    booking_id = db.insert(sql, (user_id,station_name, area, slot, time_from, time_to, created_at,booking_date,duration,calculated_amt,converted_usd ))
                else:
                    print(response)
                    print("Failed to convert")
            except Exception as e:
                print(f"An error occurred: {str(e)}")
                message=f"An error occurred: {str(e)}"
                return f'<script>alert({message}); window.location.href="/";</script>'
            
            #calling mail api 
            API_URL = "http://x23324902-scalableapi.eba-euagxqry.us-west-2.elasticbeanstalk.com/email"
            try:
                subject='Booking for parking slot  '
                message=f"Your parking has been confirmed for {booking_date} at {time_from} .Total duration of {duration}min which costs € {calculated_amt}. Thankyou for reaching out!"
                email=session['useremail']
                ##translating the name
                json_data = {"subject": subject,"body":message,"email":email }
                response = requests.get(API_URL, json=json_data, stream=True)
                if response.status_code == 200:
                    
                    message="Parking booked successfully!! "
                    return render_template('index.html',message=message)
                else:
                    print(response)
                    print("Failed to email")
                    return redirect(url_for('index'))
            except Exception as e:
                converted_amt = f"An error occurred: {str(e)}"
                return redirect(url_for('index'))
            

        
        
        




@application.route('/history',methods=['GET','POST'])
def history():
    if 'userid' in session :
        user_id=session['userid']
        db = Db()
        bookings = db.select("SELECT * FROM booking_t where b_user = '%s' ORDER BY b_bookingdate DESC;", (user_id,))
        # print(bookings)  # print out the value of the bookings variable
        return render_template("history.html", bookings=bookings )
    else:
        return redirect('/') 

@application.route("/delete_booking" ,methods=["GET","POST"])
def delete_booking():
    if request.method=="POST":
        if 'userid' not in session:
            return redirect('/')
        else:
            recordid=request.form['id']
            db = Db()
            qry = db.delete("delete from booking_t where b_id = %s",(recordid,) )
            return redirect(url_for('history'))
    else:
        return redirect(url_for('history'))
        
    


@application.route('/logout')
def logout():
    session.pop('useremail',None)
    session.pop('userid',None)

    return redirect('/')

if __name__=='__main__':
    application.run(debug=True,port=5088)