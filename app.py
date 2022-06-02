import requests
from werkzeug.utils import secure_filename
import os
from flask import Flask,render_template,redirect,request,session, url_for
from graphqlclient import GraphQLClient

app = Flask(__name__)
app.secret_key = "ma564dfw3q"
url="http://127.0.0.1:8000/graphql"
UPLOAD_FOLDER = 'D:/Python/Blog_App_with_Flask-Graphene-/static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
token=''
@app.route("/")
def index():
    return redirect(url_for('dashboard'))


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
                                            id,
                                            username
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
            print(r.json()['data']['storeToken']['token']['user']['id'],"###########")
            session['user_id']=r.json()['data']['storeToken']['token']['user']['id']
            session['username']=r.json()['data']['storeToken']['token']['user']['username']
            print(session['user_id'],"@@@@@@@")
            print(session['username'],"@@@@@@@")
            return redirect(url_for('dashboard'))
    return render_template("login.html")
#------------------Registrastion-----------------
@app.route("/register",methods=['POST', 'GET'])
def register():
    # if 'email' in session:
    #     return 'you are not allowed to registerd beacause you already login'
    if request.method=='POST':
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
    if 'username' in session:
        query='''query{
                allPost{
                        id,
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

@app.route('/blog_detail/<int:id>',methods=['GET','POST'])
def blog_detail(id):
    if 'username' in session:
        query='''query
                    {
                    post(postId:%s)
                        {
                            id
                            title
                            headerImage
                            postDate
                            tag
                            body
                            likes
                            {
                                username
                            }
                            author
                            {
                                id,
                                firstName,
                                lastName,
                                username
                            }
                            comments
                            {
                                name
                                body
                            }
        
                        }
                    }
        ''' % (id)
        headers = {'Authorization': f"JWT {session['token']}"}
        response=requests.post(url=url,json={"query":query},headers=headers)
        post=response.json()['data']['post']
        liked=response.json()['data']['post']['likes']
        liked=[d['username'] for d in liked]
        len_liked=len(liked)
    
        print(liked,"@@@@@@")
        return render_template('article_details.html',post=post,liked=liked,len_liked=len_liked)
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
        session.pop('username', None)                
        session.pop('user_id', None)
        session.pop('token', None)
        session.pop('liked', None)
        msg=response.json()['data']['logout']['msg']
        return render_template('login.html',msg=msg)


@app.route('/add_post',methods=['GET','POST'])
def add_post():
    if 'username' in session:
        if request.method=='POST':
            title=request.form['title']
            tag=request.form['tag']
            about=request.form['about']
            file = request.files['fileupload']
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image=file.filename
            author_id=session['user_id']
            query='''mutation
                    {
                        createPost(postData:
                            {
                                title:"%s",
                                tag:"%s",
                                body:"%s",
                                headerImage:"%s",
                                author:%s
                            })
                        {
                           msg
                        }
                    }''' % (title,tag,about,image,author_id)
            headers = {'Authorization': f"JWT {session['token']}"}
            response=requests.post(url=url,json={"query":query},headers=headers)
            print(response.json()) 
            return redirect(url_for('dashboard'))       
    else:
        return redirect(url_for('login'))
    
    return render_template("add_post.html")

@app.route('/update_post/<int:id>',methods=['GET','POST'])
def update_post(id):
    if 'username' in session:
        data='''
        query{
            post(postId:%s)
            {
                id
                title
                tag
                body       
            }
            }'''% (id)
        headers = {'Authorization': f"JWT {session['token']}"}
        data_res=requests.get(url=url,json={"query":data},headers=headers)
        post=data_res.json()['data']['post']
        if request.method=='POST':
            title=request.form['title']
            tag=request.form['tag']
            about=request.form['about']
            file = request.files['fileupload']
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image=file.filename
            query='''mutation updateMutation
                    {
                    updatePost(postData:{
                        id:%s,
                        title:"%s",
                        tag:"%s",
                        body:"%s",
                        headerImage:"%s",
                        })
                        {
                            msg
                    }
                    }''' % (id,title,tag,about,image)
            response=requests.post(url=url,json={"query":query},headers=headers)
            print(response.json())
            return redirect(url_for('dashboard'))
        return render_template('update_post.html',post=post)
    else:
        return redirect(url_for('login'))

@app.route('/delete_post/<int:id>',methods=['GET','POST'])
def delete_post(id):
    if 'username' in session:
        data='''
        query{
            post(postId:%s)
            {
                     id
                  title
                  author{
                      id
                  }        
            }
            }'''% (id)
        headers = {'Authorization': f"JWT {session['token']}"}
        data_res=requests.get(url=url,json={"query":data},headers=headers)
        post=data_res.json()['data']['post']
        print(post,"@@@@")
        if request.method =='POST':
            query='''mutation deleteMutation
                        {
                        deletePost(id:%s) 
                            {
                                msg
                            }
                        }'''% (id)
            response=requests.post(url=url,json={"query":query},headers=headers)
            print(response.json()['data'])
            return redirect(url_for('dashboard'))
        return render_template("delete_post.html",post=post)
    else:
        return redirect(url_for('login'))
    

@app.route('/like_post/<int:id>',methods=['GET','POST'])
def like_post(id):
    if 'username' in session:
        user_id=session['user_id']
        query='''mutation
                    {
                        createLikes(postId:%s,userId:%s)
                            {
                               
                                liked
                            }
                    }'''% (id,user_id)
        headers = {'Authorization': f"JWT {session['token']}"}
        response=requests.post(url=url,json={"query":query},headers=headers)
        liked=response.json()['data']['createLikes']['liked']
        
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

@app.route('/add_comments/<int:id>',methods=['GET','POST'])
def add_comments(id):
    if 'username' in session:
        data='''
        query{
            post(postId:%s)
            {
                     id
                  title
                  author{
                      id
                  }        
            }
            }'''% (id)
        headers = {'Authorization': f"JWT {session['token']}"}
        data_res=requests.get(url=url,json={"query":data},headers=headers)
        post=data_res.json()['data']['post']
        if request.method=='POST':
            name=request.form['name']
            body=request.form['body']
            query='''mutation{
                        createComments(commentsData:
                        {
                            post:%s,
                            name:"%s"
                            body:"%s"
                        })
                        {
                            msg
                            
                        }
                        }'''% (id,name,body)
            response=requests.post(url=url,json={"query":query},headers=headers)
            print(response.json())
            return redirect(url_for('dashboard'))
        return render_template("add_comments.html",post=post)
    else:
        return redirect(url_for('login'))

if __name__=="__main__":
    app.run(port = 5000,debug = True)