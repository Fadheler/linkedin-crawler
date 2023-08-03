#step 1
from dash import Dash, Input, Output, State, html, dcc, dash_table, callback, ctx
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
import sqlite3
import os
import threading
import urllib.parse as parse
import sys
from io import StringIO

app = Dash(__name__, external_stylesheets =[dbc.themes.BOOTSTRAP])

#
# QUESTIONS TABLE
#
def update_table():
    con = sqlite3.connect("jobs.db")
    sql_query = pd.read_sql('SELECT * FROM questions', con)
    res = pd.DataFrame(sql_query)
    con.close()
    return dbc.Container(dash_table.DataTable(res.to_dict('records'), [{"name": i, "id": i} for i in res.columns],
        editable=True,
        row_deletable=True,
        style_table={
            'maxWidth': '100%',
            'overflowX': 'scroll',
            'border': 'thin lightgrey solid',
            'textAlign': 'left'
        },
        style_cell={
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
            'maxWidth': 0,
            'textAlign': 'left'
        },
        tooltip_data=[
            {
                column: {'value': str(value), 'type': 'markdown'}
                for column, value in row.items()
            } for row in res.to_dict('records')
        ],
        tooltip_duration=None,
        id="table"))
@app.callback(Output('thetable', 'children', allow_duplicate=True),
              [Input('table', 'data_previous')],
              [State('table', 'data')]
    , prevent_initial_call=True)
def edit_questionstable(previous, current):
    if previous is None:
        print('dash exception')
        #dash.exceptions.PreventUpdate()
    else:
        identified = 0
        for row in previous:
            if row not in current:
                identified = row['id']
        for row in current:
            if row['id'] not in previous:
                if row['id'] == identified:
                    #Changed content
                    identified = 0
                    print(row)
                    con = sqlite3.connect("jobs.db")
                    cur = con.cursor()
                    cur.execute("UPDATE questions SET question=?, answer=? WHERE id=?", (row['question'], row['answer'], str(row['id'])))
                    con.commit()
                    con.close()
                    print('Row updated')
        if identified != 0:
            #Deleted row
            con = sqlite3.connect("jobs.db")
            cur = con.cursor()
            cur.execute("DELETE FROM questions WHERE id="+str(identified))
            con.commit()
            con.close()
            print('Row deleted')
    return update_table()

#
# ADD QUESTION BUTTON
#
question_input = dbc.Row([
        dbc.Label("Question"
                , html_for="question"
                , width=2),
        dbc.Col(dbc.Input(
                type="text"
                , id="question"
                , placeholder="The question answered in the column (the variable)."
            ),width=10,
        )],className="mb-3"
)
answer_input = dbc.Row([
        dbc.Label("Answer format"
                , html_for="answer"
                , width=2),
        dbc.Col(dbc.Input(
                type="text"
                , id="answer"
                , placeholder="The format you want the answer to follow (for example 'True or False', 'from 1 to 5' etc.)"
            ),width=10,
        )],className="mb-3"
)
mandatory = dbc.Row([
        dbc.Label("Mandatory condition"
                , html_for="answer"
                , width=2),
        dbc.Col(dbc.Input(
                type="text"
                , id="answer"
                , placeholder="'True' in {answer}"
            ),width=10,
        )],className="mb-3"
)
preferred = dbc.Row([
        dbc.Label("Preferred condition"
                , html_for="answer"
                , width=2),
        dbc.Col(dbc.Input(
                type="text"
                , id="answer"
                , placeholder="The format you want the answer to follow (for example 'True or False', 'from 1 to 5' etc.)"
            ),width=10,
        )],className="mb-3"
)
def add_question():
    form = html.Div([ dbc.Container([
            html.Br()
            , dbc.Card(
                dbc.CardBody([
                     dbc.Form([question_input, answer_input])
                ,html.Div(id = 'div-button', className="btndiv", children = [
                    dbc.Button('Add question'
                    , color = 'primary'
                    , id='add_question'
                    , n_clicks=0)
                ]) #end div
                ])#end cardbody
            )#end card
            , html.Br()
            , html.Br()
        ])
        ])
    return form
@app.callback(
    Output('feedback', 'children')
    , Input("add_question", 'n_clicks')
    , State("question", 'value')
    , State("answer", 'value')
    , prevent_initial_call=True
    )
def submit_question(n_clicks, question, answer):
    if question is not None and answer is not None and n_clicks > 0 and len(question) > 3 and len(answer) > 3:
        con = sqlite3.connect("jobs.db")
        cur = con.cursor()
        cur.execute("INSERT INTO questions ('question', 'answer') VALUES(?,?)", (question,answer))
        con.commit()
        con.close() 
    return add_question()

#
# QUESTIONS UPDATE BUTTON
#
update_button = dbc.Container(
    dbc.Button('Refresh questions', id="update_table", color="secondary", n_clicks=0),
    style={
        'textAlign': 'center'
    })
@app.callback(
    Output("thetable", "children")
    , Input('update_table', "n_clicks")
)
def c_updatebutton(n_clicks):
    return update_table()

#
# JOBS UPDATE BUTTON
#
jobs_button = dbc.Container(
    dbc.Button('Refresh jobs', id="update_jobstable", color="secondary", n_clicks=0),
    style={
        'textAlign': 'center'
    })
@app.callback(
    Output("thejobs", "children")
    , Input('update_jobstable', "n_clicks")
)
def c_updatejobs(n_clicks):
    return update_jobstable()
#
# JOBS TABLE
#
def update_jobstable():
    con = sqlite3.connect("jobs.db")
    cur = con.cursor()
    daquery = 'SELECT jobs.id, jobs.title, jobs.description, jobs.link, jobs.recruiter, employers.name empname, locations.name locname FROM jobs LEFT JOIN employers ON jobs.employer=employers.id LEFT JOIN locations ON jobs.location = locations.id'
    sql_query = pd.read_sql(daquery, con)
    res = pd.DataFrame(sql_query)
    thebigtext = ' '.join(res['description'])
    con.close()
    return dbc.Container([dash_table.DataTable(res.to_dict('records'), [{"name": i, "id": i} for i in res.columns],
        editable=True,
        row_deletable=True,
        style_table={
            'maxWidth': '100%',
            'overflowX': 'scroll',
            'border': 'thin lightgrey solid',
            'textAlign': 'left'
        },
        style_cell={
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
            'maxWidth': 0,
            'textAlign': 'left'
        },
        tooltip_data=[
            {
                column: {'value': str(value), 'type': 'markdown'}
                for column, value in row.items()
            } for row in res.to_dict('records')
        ],
        tooltip_duration=None,
        id="jobstable")])
@app.callback(Output('thejobs', 'children', allow_duplicate=True),
              [Input('jobstable', 'data_previous')],
              [State('jobstable', 'data')]
    , prevent_initial_call=True)
def edit_jobstable(previous, current):
    if previous is None:
        print('dash exception')
        #dash.exceptions.PreventUpdate()
    else:
        identified = 0
        for row in previous:
            if row not in current:
                identified = row['id']
        for row in current:
            if row['id'] not in previous:
                if row['id'] == identified:
                    #Changed content
                    identified = 0
                    print(row)
                    con = sqlite3.connect("jobs.db")
                    cur = con.cursor()
                    cur.execute("UPDATE questions SET question=?, answer=? WHERE id=?", (row['question'], row['answer'], str(row['id'])))
                    con.commit()
                    con.close()
                    print('Row updated')
        if identified != 0:
            #Deleted row
            con = sqlite3.connect("jobs.db")
            cur = con.cursor()
            cur.execute("DELETE FROM questions WHERE id="+str(identified))
            con.commit()
            con.close()
            print('Row deleted')
    return update_jobstable()

#
# LinkedIn Crawler
#
crawler = dbc.Container(dbc.Card(dbc.CardBody(dbc.Row([dbc.Col(dbc.Input(placeholder='LinkedIn job search link', id="linkedin")), dbc.Col(dbc.Button('Start crawler', id="crawler", n_clicks=0)), html.Div('', id="crawlcol")]))))
n_linkedin = 1
@app.callback(
    Output("crawlcol", 'children')
    , Input('linkedin', 'value')
    , Input('crawler', 'n_clicks')
    , prevent_initial_call=True)

def linkedin_function(linkedin, test):
    if ctx.triggered_id == "crawler":
        os.system('python3 linkedin.py '+parse.quote(linkedin))
#
# GPT Analysis
#
def compare_command(answer, command):
    answer = answer.strip()
    if "'" not in command:
        answer = float(answer)
    final = command.replace("{answer}", str(answer))
    old_stdout = sys.stdout
    redirected_output = sys.stdout = StringIO()
    try:
        exec("print("+final+")")
    except:
        raise 
    finally: # !
        sys.stdout = old_stdout # !

    if 'True' in redirected_output.getvalue():
        return True
    else:
        return False

scanner = dbc.Container(dbc.Card(dbc.CardBody([dbc.Row([dbc.Alert("After clicking on the button, go to chatGPT tab and position the mouse on top of the text area.You can exit the scanner by moving the mouse cursor to the top left corner.", color="warning"), html.Br(), dbc.Col(dbc.Textarea(placeholder="Resume text", id="resume"))]),html.Br(),dbc.Row([dbc.Col(dbc.Button('Start scanning', id="scanner1", n_clicks=0), className="btndiv")]),html.Div('', id="scancol")])))
@app.callback(
    Output("scancol", "children")
    , Input("resume", "value")
    , Input("scanner1", "n_clicks")
)
def start_scanning(resume, n_clicks):
    if n_clicks > 0:
        if resume is None: scan_function(b'N/A')
        else: scan_function(resume)

def scan_function(resume):
    os.system('python3 scanner.py '+parse.quote(resume))
#
# APP LAYOUT
#
app.layout = html.Div([
    dbc.Container([
        html.H1(
            children='LinkedIn Job Search'
        )
        , html.Br()
        , dbc.Row([dbc.Col([html.H2('Fill columns'), html.Div(scanner)]), dbc.Col([html.H2('Add columns'), html.Div(id="feedback", children=add_question())])])
        , html.Br()
        , html.H2(
            children='Columns list'
        )
        , update_button
        , html.Br()
        , html.Div(id="thetable")
        , html.Br()
        , html.H2(
            children='LinkedIn Crawler'
        )
        , html.Br()
        , crawler
        , html.Br()
        , html.H2(
            children='Job offers list'
        )
        , jobs_button
        , html.Br()
        , html.Div(id="thejobs")
    ])
])


if __name__ == "__main__":
     app.run_server(debug = True)