from flask import Flask,render_template,request,redirect,url_for,session  # type: ignore[import]
import mysql.connector  # type: ignore[import]
import re
from datetime import timedelta
exp=r'^\d{4}\s\d{4}\s\d{4}$'
db_connector=mysql.connector.connect(host='localhost',user='root',password='root',database='atm')
cusror=db_connector.cursor()


atm_object=Flask('__name__')
atm_object.permanent_session_lifetime=timedelta(minutes=5)
atm_object.secret_key='my secret key'
@atm_object.route('/')
def welcome():
    if 'username' in session:
        return redirect(url_for('home'))
    elif 'ac_no' in session:
        return redirect(url_for('pin'))
    return render_template('welcome.html')

@atm_object.route('/ac_details',methods=['GET','POST'])
def ac_no():
    if session:
        return redirect(url_for('home'))
    if request.method=='POST':
        ac_no=request.form['acc']
        if re.match(exp,ac_no):
            cusror.execute('select ac_no,pin from user_data where ac_no=%s;',(ac_no,))
            data=cusror.fetchone()
            if data:
                session.permanent=True
                session['ac_no']=data[0]
                session['pin']=data[1]
                return redirect(url_for('pin'))
            else:
                return render_template('/account.html',info='*account number not found\nplease enter valid account number')
        else:
            return render_template('/account.html',info='*please enter valid account number\nlike 1xxx xxxx xxx9')        

    return render_template('/account.html')
@atm_object.route('/pin',methods=['GET','POST'])
def pin():
    if 'ac_no' not in session:
        return redirect(url_for('ac_no'))
    elif 'username' in session:
        return redirect(url_for('home'))
    if request.method=='POST':
        if request.form['password']=='password':
            ac_no=session.get('ac_no')
            pin=request.form['pin']
            if int(pin)==int(session.get('pin')):
                cusror.execute('select username from user_data where ac_no=%s;',(ac_no,))
                data=cusror.fetchone()
                session['username']=data[0]
                return render_template('home.html',username=data[0])
            else:
                return render_template('pin.html',info='*incorrect pin')
    return render_template('pin.html')
@atm_object.route('/home')
def home():
    if 'ac_no' not in session:
        return redirect(url_for('ac_no'))
    elif 'username' not in session:
        return redirect(url_for('pin'))
    return render_template('home.html',username=session.get('username'))

@atm_object.route('/check_balance')
def check_balance():
    if 'ac_no' not in session:
        return redirect(url_for('ac_no'))
    elif 'username' not in session:
        return redirect(url_for('pin'))
    ac_no=session.get('ac_no')
    cusror.execute('select balance from user_data where ac_no=%s;',(ac_no,))
    data=cusror.fetchone()
    if data:
        return render_template('balance.html',balance=data[0],username=session.get('username'))

@atm_object.route('/deposit',methods=['GET','POST'])
def deposit():
    if 'ac_no' not in session:
        return redirect(url_for('ac_no'))
    elif 'username' not in session:
        return redirect(url_for('pin'))
    type='deposit'
    if request.method=='POST':
        deposit_amount=request.form['deposit']
        ac_no=session.get('ac_no')
        cusror.execute('select balance from user_data where ac_no=%s;',(ac_no,))
        b_amount=cusror.fetchone()
        b_balance=b_amount[0]
        cusror.execute('update user_data set balance=balance+%s where ac_no=%s;',(deposit_amount,ac_no))
        db_connector.commit()
        cusror.execute('select balance from user_data where ac_no=%s;',(ac_no,))
        data=cusror.fetchone()
        cusror.execute('insert into transaction(ac_no,transaction,b_balance,a_balance,transaction_amount) values(%s,%s,%s,%s,%s);',(ac_no,type,b_balance,data[0],deposit_amount))
        db_connector.commit()
        if data:
            return render_template('d_success.html',username=session.get('username'),balance=data[0])
    return render_template('deposit.html')

@atm_object.route('/withdraw',methods=['GET','POST'])
def withdraw():
    if 'ac_no' not in session:
        return redirect(url_for('ac_no'))
    elif 'username' not in session:
        return redirect(url_for('pin'))
    type='withdraw'
    if request.method=='POST':
        withdraw_amount=request.form['withdraw']
        pin=request.form['pin']
        ac_no=session.get('ac_no')
        x=session.get('pin')
        cusror.execute('select balance from user_data where ac_no=%s;',(ac_no,))
        balance=cusror.fetchone()
        if int(x)==int(pin):
            if int(withdraw_amount)<=int(balance[0]):
                cusror.execute('update user_data set balance=balance-%s where ac_no=%s and pin=%s;',(withdraw_amount,ac_no,pin))
                db_connector.commit()
                cusror.execute('select balance from user_data where ac_no=%s;',(ac_no,))
                data=cusror.fetchone()
                cusror.execute('insert into transaction(ac_no,transaction,b_balance,a_balance,transaction_amount) values(%s,%s,%s,%s,%s);',(ac_no,type,balance[0],data[0],withdraw_amount))
                db_connector.commit()
                if data:
                    return render_template('w_success.html',username=session.get('username'),balance=data[0],amount=withdraw_amount)
            else:
                return render_template('withdraw.html',info='*insufficient balance',username=session.get('username'))
        else:
            return render_template('withdraw.html',info1='*incorrect pin',username=session.get('username'))
       
    return render_template('withdraw.html',username=session.get('username'))


@atm_object.route('/change_pin',methods=['GET','POST'])
def change_pin():
    if 'ac_no' not in session:
        return redirect(url_for('ac_no'))
    elif 'username' not in session:
        return redirect(url_for('pin'))
    if request.method=='POST':
        username=request.form['name']
        ac_no1=request.form['ac_no']
        old=request.form['old']
        new=request.form['new']
        ac_no=session.get('ac_no')
        if ac_no==ac_no1:
            cusror.execute('select username from user_data where username=%s and ac_no=%s and pin=%s;',(username,ac_no,old))
            data=cusror.fetchone()
            if data:
                cusror.execute('update user_data set pin=%s where ac_no=%s;',(new,ac_no))
                db_connector.commit()
                return render_template('c_success.html')
        else:
            return render_template('change_pin.html',error_message='*invalid details',username=session.get('username'))
    return render_template('change_pin.html',username=session.get('username'))

@atm_object.route('/bank_statement')
def bank_statement():
    if 'ac_no' not in session:
        return redirect(url_for('ac_no'))
    elif 'username' not in session:
        return redirect(url_for('pin'))
    ac_no=session.get('ac_no')
    cusror.execute('select * from transaction where ac_no=%s;',(ac_no,))
    data=cusror.fetchall()
    cusror.execute('select sum(b_balance),sum(a_balance),sum(transaction_amount) from transaction where ac_no=%s;',(ac_no,))
    balances=cusror.fetchone()
    sum_b_balance=balances[0]
    sum_a_balance=balances[1]
    sum_transaction_amount=balances[2]
    return render_template('bank_statement.html',data=data,username=session.get('username'), sum_b_balance= sum_b_balance, sum_a_balance= sum_a_balance,sum_transaction_amount=sum_transaction_amount)
@atm_object.route('/logout')
def logout():
    if 'username' not in session:
        return redirect(url_for('ac_no'))

    session.clear()
    return redirect(url_for('welcome'))
if __name__=='__main__':
    atm_object.run(debug=True)