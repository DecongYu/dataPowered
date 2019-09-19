from flask import(
    Blueprint, Flask, g, request, url_for, render_template, redirect, flash)
from shaleoptim.db import get_db
from shaleoptim.auth import login_required
from werkzeug.exceptions import abort
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import pandas as pd
import csv, math, pickle, datetime, os, threading, time
import matplotlib
# matplotlib.use('Agg')
import matplotlib.pyplot as plt, mpld3
from matplotlib import colors


bp = Blueprint('wells', __name__)

# index - display all the wells under user_id
@bp.route('/')
@login_required
def index():
    db = get_db()
    wells = db.execute(
        'SELECT w.id, well_id, on_prd_date, tvd, frac_len, cum_frac_propp, bh_long, bh_lat, latrl_len, entered, author_id, email'
        ' FROM well w JOIN user u ON w.author_id = u.id ORDER BY entered DESC'
    ).fetchall()
    return render_template('wells/index.html', wells = wells)

# create - create a new well
@bp.route('/create', methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        well_id = request.form['well_id']
        on_prd_date = request.form['on_prd_date']
        tvd = request.form['tvd']
        frac_len = request.form['frac_len']
        cum_frac_propp = request.form['cum_frac_propp']
        bh_long = request.form['bh_long']
        bh_lat = request.form['bh_lat']
        latrl_len = request.form['latrl_len']
        date_days = (datetime.datetime.strptime(str(on_prd_date), '%Y-%m-%d') - datetime.datetime.strptime(str("2013-5-1"), "%Y-%m-%d")).days + 1
        error = None

        if not well_id:
            error = 'Well ID is required.'
        if not on_prd_date:
            error = '(Planned) on-production date is required.'
        if not tvd:
            error = 'Well TVD is required.'
        if not frac_len:
            error = 'Total Frac length is required.'
        if not cum_frac_propp:
            error = '(Planned) total frac proppant tonnage is required.'
        if not bh_long:
            error = 'Well bottom hole longitude is required.'
        if not bh_lat:
            error = 'Well bottom hole latitude is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO well (well_id, on_prd_date, date_days, tvd, frac_len, cum_frac_propp, bh_long, bh_lat, latrl_len, author_id)'
                ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (well_id, on_prd_date, date_days, tvd, frac_len, cum_frac_propp, bh_long, bh_lat, latrl_len, g.user['id'])
            )
            db.commit()
            return redirect(url_for('wells.index'))
    return render_template('wells/create.html')

# get_well - get a specific well (for updating, deleting or moddeling)
def get_well(id, check_author=True):
    well = get_db().execute(
        'SELECT w.id, well_id,  on_prd_date, date_days, tvd, frac_len, cum_frac_propp, bh_long, bh_lat, latrl_len, entered, author_id, email'
        ' FROM well w JOIN user u ON w.author_id = u.id'
        ' WHERE w.id = ?', (id,)
    ).fetchone()

    if well is None:
        abort(404, "well id {0} doesn't exist.".format(id))
    if check_author and well['author_id'] != g.user['id']:
        abort(403)
    return well

# update - update/delete an existing well
@bp.route('/<int:id>/update', methods=("GET", "POST"))
@login_required
def update(id):
    well = get_well(id)
    if request.method == "POST":
        well_id = request.form['well_id']
        on_prd_date = request.form['on_prd_date']
        tvd = request.form['tvd']
        frac_len = request.form['frac_len']
        cum_frac_propp = request.form['cum_frac_propp']
        bh_long = request.form['bh_long']
        bh_lat = request.form['bh_lat']
        latrl_len = request.form['latrl_len']
        date_days = (datetime.datetime.strptime(str(on_prd_date), '%Y-%m-%d') - datetime.datetime.strptime(str("2013-5-1"), "%Y-%m-%d")).days + 1
        error = None

        if not well_id:
            error = 'Well ID is required.'
        
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE well SET well_id = ?, on_prd_date = ?, date_days=?, tvd = ?, frac_len=?, cum_frac_propp=?, bh_long=?, bh_lat=?, latrl_len=? WHERE id = ?',
                (well_id, on_prd_date, date_days, tvd, frac_len, cum_frac_propp, bh_long, bh_lat, latrl_len, id)
            )
            db.commit()
            return redirect(url_for('wells.index'))
    
    return render_template('wells/update.html', well=well)

# model a well
@bp.route('/<int:id>/run_model', methods=("GET", "POST"))
@login_required
def run_model(id):
    well = get_well(id)
    well = well
    well_id = well["well_id"]
    date_days = well["date_days"]
    tvd = well["tvd"]
    frac_len = well["frac_len"]
    #frac_propp = well["cum_frac_propp"]
    bh_long = well["bh_long"]
    bh_lat = well["bh_lat"]
    model_inputs = []
    for propp_var in range(600, 8100, 20):
        completion_param = [date_days, tvd, frac_len, propp_var, bh_long, bh_lat]
        model_inputs.append(completion_param)

    # run modeling on 5 models
    for i in [1,2,3,4,5]:
        loaded_model = pickle.load(open("./shaleoptim/success_model_archive/final_RF_model%d.sav" %(i), 'rb'))
        predict = loaded_model.predict(model_inputs)
        predict = list(predict)
        predict = [round(elem, 1) for elem in predict]
        predict = np.array(predict)
        model_inputs = np.array(model_inputs)
        predictions = list(zip([row[3] for row in model_inputs], predict))

        # sort predicted production and frac proppant order by proppant ascend
        propp_sorted_predict = predictions
        def sort_on_propp(propp_sorted_predict):
            return propp_sorted_predict[0]
        propp_sorted_predict.sort(key = sort_on_propp)
        xy = [[each_list[i] for i in range(0,2)] for each_list in propp_sorted_predict]
        xy = np.array(xy)
        propp = xy[:,0]
        preprd = pd.DataFrame(xy[:,1])

        if i>1:
            y = pd.concat([y,preprd],axis=1)
        else:
            y=pd.DataFrame(preprd)

    x = propp
    y = np.array(y)

    plt.figure()
    plt.xscale('log')
    plt.plot(x,y[:,0], linewidth=1, label = 'model 1',color='c')
    plt.plot(x,y[:,1], linewidth=1, label = 'model 2',color='r')
    plt.plot(x,y[:,2], linewidth=1, label = 'model 3',color='g')
    plt.plot(x,y[:,3], linewidth=1, label = 'model 4',color='y')
    plt.plot(x,y[:,4], linewidth=1, label = 'model 5',color='k')
    #plt.axvline(frac_propp, linewidth=3, '--r')
    plt.grid(which='both', axis='both')
    plt.xlabel('Presumed Cummulative Frac Proppant Tonage (tonnes)')
    plt.ylabel('Predicted First 12 Month Cummulative Production (boe)')
    plt.title(' {} Predicted Production vs Frac Proppant'.format(well_id))
    plt.legend()
    mpld3.show()

    return redirect(url_for('wells.index'))

# delete - delete a well
@bp.route('/<int:id>/delete', methods=("GET","POST"))
@login_required
def delete(id):
    get_well(id)
    db = get_db()
    db.execute('DELETE FROM well WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('wells.index'))
