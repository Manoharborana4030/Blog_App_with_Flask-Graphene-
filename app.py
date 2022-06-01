from flask import Flask
import json
import requests
from werkzeug.utils import secure_filename
import os
from flask import Flask,render_template,redirect,request,session, url_for
from graphene import ObjectType, String, Schema
from graphqlclient import GraphQLClient

app = Flask(__name__)
app.secret_key = "ma564dfw3q"
url="http://127.0.0.1:8000/graphql"
token=''
@app.route("/")
def index():
    return redirect(url_for('login'))


#--------------------LOGIN-------------------
@app.route("/login",methods=['POST','GET'])
def login():
    if request.method=='POST':
        email=request.form['email']
        password=request.form['password']
        print(email)
        print(password)
        query ='''mutation
                        {
                            storeToken(username:"%s",password:"%s")
                            {
                                token{
                                        tokenId
                                        user{
                                            id
                                        }
                                    }
                            msg
                            }
                        }''' % (email,password)       
      
        r=requests.post(url=url,json={"query":query})
        if r.json()['data']['storeToken']['token'] is None:
            msg=r.json()['data']['storeToken']['msg']
            return render_template("login.html",msg=msg)
        else:
            session['token']=r.json()['data']['storeToken']['token']['tokenId']
            session['user_id']=r.json()['data']['storeToken']['token']['user']['id']
            print(session['user_id'],"@@@@@@@")
            return redirect(url_for('dashboard'))

    return render_template("login.html")
#------------------Registrastion-----------------
@app.route("/register",methods=['POST', 'GET'])
def register():
    # if 'email' in session:
    #     return 'you are not allowed to registerd beacause you already login'
    if request.method=='POST':
        global user_info
        first_name=request.form['first_name']
        last_name=request.form['last_name']
        username=request.form['username']
        email=request.form['email']
        password=request.form['password']
        query ='''mutation{
                        createUser(username:"%s",email:"%s",password:"%s",firstName:"%s",lastName:"%s"){
                                user{
                                        id,
                                        username,
                                        email,
                                        firstName,
                                        lastName,
                                    }
                            }
                        }''' % (username,email,password,first_name,last_name)
        response=requests.post(url=url,json={"query":query})
        data=response.json()
        if response.json()['data']['createUser'] is None:
            data=response.json()
            msg=data["errors"][0]["message"]
            return render_template("register.html",msg=msg)
        else:
            session['user_id']=response.json()['data']['createUser']['user']['id']
            return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/forgot_password',methods=['POST', 'GET'])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("forgot_email")
        # check_user=User.query.filter_by(username=email).first()
        # if check_user:
        #     session['email']=request.form['forgot_email']
        #     return redirect(url_for('new_password'))
        # else:
        #     return 'User Not Found!'
    return render_template('forgetpassword.html')

@app.route("/dashboard",methods=['GET', 'POST'])
def dashboard():
    if 'email' in session:
        query='''query{
                allPost{
                        title,
                        headerImage,
                        author
                            {
                                id,
                                firstName,
                                lastName,
                                username
                            }
                        postDate,
                        body,
                        likes
                            {
                                username
                            }
                        comments
                            {
                                body
                                name
                            }
                        }
                    }'''
        headers = {'Authorization': f"JWT {session['token']}"}
        response=requests.post(url=url,json={"query":query},headers=headers)
        if response.json()['data']['allPost'] is None:
            data=response.json()
            msg=data["errors"][0]["message"]
            return render_template('login.html',msg=msg)
        else:
            blog=response.json()['data']['allPost']
        return render_template('home.html',blog=blog)
    else:
        return redirect(url_for('login'))

@app.route('/logout',methods=['GET', 'POST'])
def logout():
    id=session['user_id']
    query='''mutation{
                    logout(id:%s)
                        {
                            msg
                        }  
                    }'''% (id)
    print(query,"@@")
    response=requests.post(url=url,json={"query":query})
    print(response.json(),"@@@@@@@@@@@@@@@@@2")
    if response.json()['data']['logout'] is None:
        msg='You are not valid User kindly login again'
        return render_template('login.html',msg=msg)
    else:
        session.pop('email', None)                
        session.pop('user_id', None)
        session.pop('token', None)
        msg=response.json()['data']['logout']['msg']
        return render_template('login.html',msg=msg)



if __name__=="__main__":
    app.run(debug=True)