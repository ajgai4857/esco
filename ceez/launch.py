import json

import flask
from flask import Flask, render_template, request, redirect

app = Flask(__name__)
orders = []


def unique(id):
    with open('usr/settings.json') as f:
        all = json.load(f)["take_profits"]
    f.close()
    for x in all.keys():
        print(all[x])
        if x == str(id):
            print(all)
            return False
    return True


@app.route("/",  methods=['GET','POST'])
def dashboard():
    with open('usr/settings.json') as f:
        settings = json.load(f) 
        all = settings['take_profits']
    f.close()
    from bin import app
    return render_template('dashboard.html', list=all, s=settings, len=not(bool(len(all))))

# @app.route('/start')
# def start():
    

@app.route('/save', methods=['GET','POST'])
def save():
    if request.method == 'POST':
        take_profit = request.form['take_profit']
        with open('usr/settings.json') as f:
            orders = dict(json.load(f))
            tf=orders['take_profits'] # list
            f.close()
        tf.append(int(take_profit))
        with open('usr/settings.json', 'w') as f:
            json.dump(orders,f)
            f.close()
    return redirect('/')


@app.route('/delete/<int:x>')
def delete(x):
    with open('usr/settings.json') as jn:
        j=dict(json.load(jn))
        tf = j['take_profit']
    jn.close()
    tf.remove(x)
    with open('usr/settings.json', 'w') as jn:
        json.dump(j, jn)
    jn.close()
    return redirect('/')


@app.route('/update', methods=['POST'])
def update():
    with open('usr/settings.json') as settings:
        s = json.load(settings)
    settings.close()
    if request.method == 'POST':
        s['auto_trade'] = request.form['auto_tradee']
        # s['margin_type'] = request.form['margin_type']
        s['type'] = request.form['type']
        s['time_in_force'] = request.form['time_in_force']
        s['enable_take_profits_upto'] = request.form['e_take_profit_l']
        s['quantity'] = request.form['quantity']
        s['quantity_per_take_profit'] = request.form['q_take_profit']
        s['stoploss_type'] = request.form['stop_loss_type']
        s['stop_loss'] = request.form['stop_loss_rate']
        try:
            x = request.form['stop_loss_switch']
            print(x)
            s['stop_loss_switch'] = ""
        except KeyError:
            s['stop_loss_switch'] = "False"
        with open('usr/settings.json', 'w') as settings:
            json.dump(s, settings)
        settings.close()
        return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
