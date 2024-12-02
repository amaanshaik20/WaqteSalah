from flask import Flask, render_template, request, redirect, url_for, session,jsonify
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='2002',
    database='prayer_pulse'
)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/committee_login")
def committee_login():
    return render_template("committee_login.html")

@app.route("/userLogin")
def userLogin():
    return render_template("userLogin.html")

@app.route("/userSearch")
def userSearch():
    return render_template("userSearch.html")

@app.route("/search_results", methods=['POST'])
def search_results():
    search_query = request.form['search_query']
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(''' 
        SELECT ci.mosqueName, ci.address, ci.committeeHeadName, ci.phoneNumber,
               nt.fajr, nt.zuhr, nt.asr, nt.magrib, nt.isha
        FROM committee_info ci
        LEFT JOIN namaz_timings nt ON ci.userName = nt.userName
        WHERE ci.mosqueName LIKE %s OR ci.address LIKE %s
    ''', (f'%{search_query}%', f'%{search_query}%'))
    
    results = cursor.fetchall()
    return render_template('searchResults.html', results=results)

@app.route("/committee_dashboard")
def committee_dashboard():
    if 'userName' in session:
        userName = session['userName']
        cursor = conn.cursor()
        cursor.execute('''
            SELECT mosqueName FROM committee_info WHERE userName = %s
        ''', (userName,))
        mosque_name = cursor.fetchone()[0]

        # Fetch namaz timings for the logged-in mosque
        cursor.execute('''
            SELECT fajr, zuhr, asr, magrib, isha FROM namaz_timings WHERE userName = %s
        ''', (userName,))
        timings = cursor.fetchone()

        if timings:
            fajr, zuhr, asr, magrib, isha = timings
        else:
            fajr = zuhr = asr = magrib = isha = ""

        return render_template('committee_dashboard.html', mosque_name=mosque_name, fajr=fajr, zuhr=zuhr, asr=asr, magrib=magrib, isha=isha)
    else:
        return redirect(url_for('committee_login'))

@app.route("/registerNewMosque")
def registerNewMosque():
    return render_template("registerNewMosque.html")

@app.route("/modifyNamazTimings")
def modifyNamazTimings():
    if 'userName' in session:
        userName = session['userName']
        cursor = conn.cursor()

        # Fetch namaz timings for the logged-in mosque
        cursor.execute('''
            SELECT fajr, zuhr, asr, magrib, isha FROM namaz_timings WHERE userName = %s
        ''', (userName,))
        timings = cursor.fetchone()

        if timings:
            fajr, zuhr, asr, magrib, isha = timings
        else:
            fajr = zuhr = asr = magrib = isha = ""

        return render_template('modifyNamazTimings.html', fajr=fajr, zuhr=zuhr, asr=asr, magrib=magrib, isha=isha)
    else:
        return redirect(url_for('committee_login'))

@app.route("/modifyCommitteeInfo", methods=["GET", "POST"])
def modify_committee_info():
    if 'userName' in session:
        userName = session['userName']
        cursor = conn.cursor()

        if request.method == 'POST':
            # Get the updated values from the form
            committee_head_name = request.form['committeeHeadName']
            phone_number = request.form['phoneNumber']
            email = request.form['email']
            address = request.form['address']

            # Update the committee information in the database
            cursor.execute('''
                UPDATE committee_info
                SET committeeHeadName = %s, phoneNumber = %s, email = %s, address = %s
                WHERE userName = %s
            ''', (committee_head_name, phone_number, email, address, userName))

            conn.commit()

            return redirect(url_for('committee_dashboard'))

        else:
            # Fetch existing committee info from the database
            cursor.execute('''
                SELECT committeeHeadName, phoneNumber, email, address FROM committee_info WHERE userName = %s
            ''', (userName,))
            committee_info = cursor.fetchone()

            return render_template('modifyCommitteeInfo.html', committee_info=committee_info)
    else:
        return redirect(url_for('committee_login'))

@app.route('/register', methods=['POST'])
def register():
    mosque_name = request.form['mosqueName']
    address = request.form['address']
    committee_head_name = request.form['committeeHeadName']
    phone_number = request.form['phoneNumber']
    email = request.form['email']
    password = request.form['password']
    username = request.form['username']  # User's chosen username

    cursor = conn.cursor()

    # Check if the username already exists in the database
    cursor.execute('''
        SELECT * FROM committee_info WHERE userName = %s
    ''', (username,))

    existing_user = cursor.fetchone()

    if existing_user:
        # Username already exists, show an error message
        error_message = "Username already taken. Please choose a different username."
        return render_template('registerNewMosque.html', error_message=error_message)

    # If username doesn't exist, proceed with registration
    cursor.execute('''
        INSERT INTO committee_info (mosqueName, userName, address, committeeHeadName, phoneNumber, email, password)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', (mosque_name, username, address, committee_head_name, phone_number, email, password))

    conn.commit()

    return render_template('success.html')

@app.route('/login', methods=['POST'])
def login():
    userName = request.form['userName']
    password = request.form['password']

    cursor = conn.cursor()

    # Query to check if the mosque name and password match in the database
    cursor.execute('''
        SELECT mosqueName FROM committee_info WHERE userName = %s AND password = %s
    ''', (userName, password))

    result = cursor.fetchone()

    if result:
        mosque_name = result[0]
        session['userName'] = userName

        # Fetch namaz timings for the logged-in mosque
        cursor.execute('''
            SELECT fajr, zuhr, asr, magrib, isha FROM namaz_timings WHERE userName = %s
        ''', (userName,))
        timings = cursor.fetchone()

        if timings:
            fajr, zuhr, asr, magrib, isha = timings
        else:
            fajr = zuhr = asr = magrib = isha = ""

        return render_template('committee_dashboard.html', mosque_name=mosque_name, fajr=fajr, zuhr=zuhr, asr=asr, magrib=magrib, isha=isha)
    else:
        error_message = "Incorrect mosque name or password. Please try again."
        return render_template('committee_login.html', error_message=error_message)

@app.route('/updateTimings', methods=['POST'])
def update_timings():
    if 'userName' in session:
        userName = session['userName']
        fajr = request.form['fajr']
        zuhr = request.form['zuhr']
        asr = request.form['asr']
        magrib = request.form['magrib']
        isha = request.form['isha']

        cursor = conn.cursor()

        # Update the namaz timings in the database
        cursor.execute('''
            UPDATE namaz_timings
            SET fajr = %s, zuhr = %s, asr = %s, magrib = %s, isha = %s
            WHERE userName = %s
        ''', (fajr, zuhr, asr, magrib, isha, userName))

        conn.commit()

        return redirect(url_for('committee_dashboard'))
    else:
        return redirect(url_for('committee_login'))


if __name__ == "__main__":
    app.run(debug=True)
