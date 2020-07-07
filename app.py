from flask import Flask, Response, render_template,request, redirect
import pickle
import pandas as pd
import numpy as np
import datetime
import pyrebase

# https://hackersandslackers.com/the-art-of-building-flask-routes/

nick_user =""

config ={
    "apiKey": "AIzaSyBXha3-IHCsplP08_J1Zo3E8GXgvuv56_M",
    "authDomain": "uflix-d786d.firebaseapp.com",
    "databaseURL": "https://uflix-d786d.firebaseio.com",
    "projectId": "uflix-d786d",
    "storageBucket": "uflix-d786d.appspot.com",
    "messagingSenderId": "1048021173687"
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()

app = Flask(__name__)

# region DATA
# -- data umum
infile_1 = open('dataframe/md_terpilih.sav', 'rb')
md_terpilih = pickle.load(infile_1)
infile_1.close()

# -- df_top_movie
infile = open('dataframe/df_top_movie.sav', 'rb')
df_top_movie = pickle.load(infile)
infile.close()
df_top_movie = df_top_movie.sort_values(by='weight_rating', ascending=False)

# -- df_sim_score_genre
infile = open('dataframe/df_sim_score_genre.sav', 'rb')
df_sim_score_genre = pickle.load(infile)
infile.close()

# -- df_sim_score_keyword
infile = open('dataframe/df_sim_score_keywords.sav', 'rb')
df_sim_score_keywords = pickle.load(infile)
infile.close()

# -- df_sim_score_cast-director
infile = open('dataframe/df_sim_gabung_CastDirector.sav', 'rb')
df_sim_mix_cast_dir = pickle.load(infile)
infile.close()

# -- df_sim_item_based
infile = open('dataframe/df_sim_item_based.sav', 'rb')
df_sim_item_based = pickle.load(infile)
infile.close()

# endregion

def based_on_genre(title):
    simpan = df_sim_score_genre[title].sort_values(ascending=False)
    simpan = simpan.drop(index=[title])
    df_head = simpan.head(10)

    val_title_idx = pd.DataFrame(df_head).index
    df_head = pd.DataFrame({
    'title' : val_title_idx
    })

    kandidat = pd.merge(md_terpilih, df_head, on='title', how='right')
    return kandidat

def based_on_keyword(title):
    simpan = df_sim_score_keywords[title].sort_values(ascending=False)
    simpan = simpan.drop(index=[title])
    df_head = simpan.head(10)

    val_title_idx = pd.DataFrame(df_head).index
    df_head = pd.DataFrame({
    'title' : val_title_idx
    })

    kandidat = pd.merge(md_terpilih, df_head, on='title', how='right')
    return kandidat

def based_on_castDirector(title):
    simpan = df_sim_mix_cast_dir[title].sort_values(ascending=False)
    simpan = simpan.drop(index=[title])
    df_head = simpan.head(10)

    val_title_idx = pd.DataFrame(df_head).index
    df_head = pd.DataFrame({
    'title' : val_title_idx
    })

    kandidat = pd.merge(md_terpilih, df_head, on='title', how='right')
    return kandidat

def cf_item_based(user_rated_movie):
    sum_movie_score = df_sim_item_based['Titanic']*(0)
    judul=[]
    for item in user_rated_movie:
        sum_movie_score += df_sim_item_based[item[0]] * (item[1]-2.5)
        judul.append(item[0])
    hasil = sum_movie_score.sort_values(ascending=False)
    hasil.drop(index=judul, inplace=True)

    df_head = pd.DataFrame({
                        'title' : hasil.head(10).index
                        })

    kandidat = pd.merge(md_terpilih, df_head, on='title', how='right')
    return kandidat


def cf_user_based(title):
    return ''


@app.route('/')
def index():
    df_pop = md_terpilih.sort_values('popularity', ascending=False)
    df_newest = md_terpilih.iloc[0:20]
    return render_template('home.html', top_mov=df_top_movie, pop_mov = df_pop, newest_mov = df_newest)

@app.route('/home_user')
def index_user():
    global nick_user
    global film_user
    xfilm_user = dict(film_user)
    print("user film:", type(film_user))
    print("user film:", xfilm_user)

    my_rate = []
    for item in film_user:
        my_rate.append([item, xfilm_user[item]])
    print("hasilll :", my_rate)
    print("hasilll :", type(my_rate))

    df_pop = md_terpilih.sort_values('popularity', ascending=False)
    df_newest = md_terpilih.iloc[0:20]

    df_rec_item  = cf_item_based(my_rate)
    return render_template('home_user.html', 
                            top_mov=df_top_movie, 
                            pop_mov = df_pop, 
                            newest_mov = df_newest,
                            rec_item_based= df_rec_item, 
                            nama_user=nick_user)

@app.route('/individual_poster')
def individ_poster():
    id = request.args.get('id')
    data = md_terpilih[md_terpilih['id'] == int(id)]
    
    print(type(data['title'].values[0]))
    
    genre_rec = based_on_genre(str(data['title'].values[0]))
    keyword_rec = based_on_keyword(str(data['title'].values[0]))
    mix_cast_dir_rec = based_on_castDirector(str(data['title'].values[0]))
    
    return render_template('individual_poster.html' , 
                            data =data, 
                            genre_rec = genre_rec,
                            key_rec=keyword_rec,
                            cast_dir_rec= mix_cast_dir_rec)





@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        global nick_user
        global film_user
        data = request.form
        data_user = data.to_dict()
        print(data_user)
        email_user = data_user['email_user']
        email_user_x = email_user.split('.')
        pass_user = data_user['pass_user']

        all_user = db.child("users").shallow().get().val()

        if(email_user_x[0] in all_user):
            ha = db.child("users").child(""+email_user_x[0]).get().val()
            if (pass_user == ha['pass']):
                # berhasil masuk
                nick_user = ha['nick']
                film_user = ha['Film']
                print("login nick: ", nick_user)
                return redirect('/home_user')
            else:
                return render_template('login.html', kondisi=True)
        else:
            return render_template('login.html', kondisi_email=True)

    return render_template('login.html')

@app.route('/signup', methods=['GET','POST'])
def signup():
    if (request.method == 'POST'):
        data = request.form
        data_user = data.to_dict()
        email_user = data_user['email_user']
        pass_user = data_user['pass_user']
        nick_user = data_user['nick_user']

        print(email_user, pass_user)

        data_user = {
            "email": str(email_user),
            "pass": str(pass_user),
            "nick" : str(nick_user),
            "id": 123
            }
        if(email_user!=""):
            child_name = "{}".format(str(email_user)).split(sep=".")
            child_name = child_name[0]
            db.child("users").child(""+child_name).set(data_user)
            return redirect('/login')
        
    return render_template('signup.html')


if __name__ =='__main__':
    app.run(port=5000, debug=True)
    