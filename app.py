from flask import Flask, request, render_template,redirect,url_for, session, flash
import pickle
from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField
from wtforms.validators import DataRequired, Email, ValidationError
from flask_mysqldb import MySQL
import bcrypt
from werkzeug.utils import secure_filename

# data load
Animes = pickle.load(open('Processed_data/Animes_list.pkl','rb'))
similarity =  pickle.load(open('Processed_data/similarity.pkl','rb'))
tag = pickle.load(open('Processed_data/tag.pkl','rb'))
New_Anime = pickle.load(open('Processed_data/New_Anime.pkl','rb'))
# anime_name =New_Anime['Name']
# end data load

# database connection
app = Flask(__name__)
mysql = MySQL(app)


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'data'
app.secret_key = 'secret'


# end database connection

UPLOAD_FOLDER = '/C:/Users/unkno/OneDrive/Desktop/img'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
  
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
  
def allowed_file(filename):
 return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#! ---------------------------login and register----------------------

class RegisterForm(FlaskForm):
    first_name = StringField("Name",validators=[DataRequired()])
    last_name = StringField("last_name",validators=[DataRequired()])
    email = StringField("email",validators=[DataRequired(), Email()])
    password = PasswordField("password", validators=[DataRequired()])
    submit = SubmitField("register")

    def validate_email(self,field):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users where email=%s",(field.data,))
        user = cursor.fetchone()
        cursor.close()
        if user:
            raise ValidationError('Email Already Taken')
        
class LoginForm(FlaskForm):
    email = StringField("Email",validators=[DataRequired(), Email()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Admin_login")



@app.route('/register',methods=['GET','POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        first_name = form.first_name.data
        last_name = form.last_name.data
        email = form.email.data
        password = form.password.data

        hashed_password = bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())

        # store data into database 
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO users (first_name,last_name,email,password) VALUES (%s,%s,%s,%s)",(first_name,last_name,email,hashed_password))
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('Admin_login'))
    
    return render_template('register.html',form=form)

@app.route('/Admin_login', methods=['GET', 'POST'])
def Admin_login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()
        
        if user:
            if bcrypt.checkpw(password.encode('utf-8'), user[4].encode('utf-8')):
                session['user_id'] = user[0]
                return redirect(url_for('dashboard'))  # Redirect to 'index' route after successful login
            else:
                flash("Invalid email or password. Please try again.")
                return redirect(url_for('Admin_login'))  # Redirect to login page again
        else:
            flash("User not found. Please sign up.")
            return redirect(url_for('Admin_login', form=form))  # Redirect to register page if user does not exist

    return render_template('Admin_login.html', form=form)

#! -------------------------- end login and register--------------------------   


@app.route("/")
def first():
    cursor = mysql.connection.cursor()
    cursor.execute('select * from dataset')
    data=cursor.fetchall()
    cursor.close()
    return render_template("first.html", dataset=data)



# @app.route("/")
# def home():
#     return render_template("index.html")   


#! ---------------------------Recommendation----------------------

@app.route("/recommendation")
def recommendation():
    return render_template("recommendation.html")

@app.route('/Anime_recommendation',methods=['post'])
def recommend():
    anime_name = New_Anime['Name'].iloc[0:500]
    try:
        if request.form:
            user_input = request.form.get('user_input')
            Animes_index = New_Anime[New_Anime['Name'] == user_input].index[0]
            distances = similarity[Animes_index]
            Animes_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:11]
    
            recommended_animes = []  # List to store recommended anime information   
            
            for i in Animes_list:
                recommended_anime_index = New_Anime.iloc[i[0]].name
                recommended_anime_info = New_Anime.loc[recommended_anime_index].values
                recommended_animes.append(list(recommended_anime_info))

            
            return render_template('recommendation.html',recommended_animes=recommended_animes,anime_name=anime_name)

    except:
        
        error = ('"Sorry, no results were found. Check your spelling or try searching for something else."'

)
    return render_template('recommendation.html',error=error)

#! ---------------------------end Recommendation----------------------

@app.route("/Anime")
def Anime():
    cursor = mysql.connection.cursor()
    cursor.execute('select * from dataset')
    data=cursor.fetchall()

    cursor.close()
    
    return render_template('Anime.html',dataset=data)

# def contact():
#     return render_template('Anime.html',
# img_url = list(Animes['img_url'].values),
# jap_name = list(Animes['jp_name'].values),
# Synopsis = list(tag['Synopsis'].values),
# name = list(Animes['Name'].values),
# Genres  = list(tag['Genres'].values),
# Studios = list(tag['Studios'].values),
# Type = list(tag['Type'].values)    
#                            )
    
#! --------------------------- Start crud operation----------------------
   
@app.route("/anime1", methods=['GET','POST'])
def anime1():
    cursor = mysql.connection.cursor()
    cursor.execute('select * from dataset')
    data=cursor.fetchall()

    cursor.close()
    
    return render_template('anime1.html',dataset=data)


@app.route("/insert", methods=['GET','POST'])
def insert():
    if request.method == "POST":
        # flash("Data Inserted Successfully")      
        Name = request.form['Name']
        Original_Name = request.form['Original_Name']
        Genres = request.form['Genres']
        Producers = request.form['Producers']
        Studios = request.form['Studios']
        Type = request.form['Type']
        Rating = request.form['Rating']
        file = request.form['image']  
        
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO dataset (Name,jp_name,img_url,Genres,Producers,Studios,Type,Rating) VALUES (%s,%s,%s,%s,%s, %s,%s,%s)", (Name,Original_Name,file,Genres,Producers,Studios,Type,Rating))
        mysql.connection.commit()
        cursor.close()
        flash('File successfully uploaded')    
        return redirect(url_for('anime1'))



@app.route('/delete/<int:id_data>', methods=['GET', 'POST'])
def delete(id_data):
    # id_data should be passed from the HTML form as a parameter  
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM dataset WHERE anime_id = %s", (id_data,))
    mysql.connection.commit()
    cursor.close()
    flash("Record has been deleted successfully")
    return redirect(url_for('anime1'))


@app.route('/update',methods=['POST','GET'])
def update():

    if request.method == 'POST':
        id_data = request.form['id']
        Name = request.form['Name']
        Original_Name = request.form['Original_Name']
        Genres = request.form['Genres']
        Producers = request.form['Producers']
        Studios = request.form['Studios']
        Type = request.form['Type']
        Rating = request.form['Rating']
        file = request.form['image']
        cursor = mysql.connection.cursor()
        cursor.execute(""" 
                       UPDATE dataset 
                       SET Name=%s,jp_name=%s,img_url=%s,Genres=%s,Producers=%s,Studios=%s,Type=%s,Rating=%s
                       WHERE anime_id=%s""",
                       (Name,Original_Name,file,Genres,Producers,Studios,Type,Rating,id_data))
        flash("Data Updated Successfully")
        mysql.connection.commit()
        return redirect(url_for('anime1'))


#! ---------------------------end crud operation----------------------                  

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/dashboard")
def dashboard():
    cursor=mysql.connection.cursor()
    cursor.execute("SELECT anime_id FROM dataset ORDER BY anime_id DESC LIMIT 1")
    idd = cursor.fetchone()
    id=str(idd[0])
    
    cursor.execute("SELECT id FROM users ORDER BY id DESC LIMIT 1 ")
    uid=cursor.fetchone()
    uidd = str(uid[0])
    cursor.close()
    return render_template('dashboard.html',id=id,uidd=uidd)

@app.route("/detail")
def detail():
    cursor = mysql.connection.cursor()
    cursor.execute("select * from users")
    data=cursor.fetchall()
    cursor.close()
    return render_template('detail.html', users=data)

@app.route('/delete2/<int:id_data>', methods=['GET', 'POST'])
def delete2(id_data):
    # id_data should be passed from the HTML form as a parameter   
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s", (id_data,))
    mysql.connection.commit()
    cursor.close()
    flash("Record has been deleted successfully")
    return redirect(url_for('detail'))


if __name__ == "__main__":
    app.debug = True
    app.run()
