from flask import Flask, render_template, request, make_response, redirect, url_for
from flask_bootstrap import Bootstrap5
import psycopg2
import os
import random
import uuid

app = Flask(__name__)
Bootstrap5(app)
app.config['TEMPLATES_AUTO_RELOAD'] = True

@app.route("/")
def intro():
    resp =  make_response(render_template("intro.html"))
    user_id = uuid.uuid4()
    resp.set_cookie("user", str(user_id))
    return resp

@app.route("/reset_seen")
def reset_seen():
    resp = make_response(url_for("intro"))
    resp.set_cookie("seen_ids", "")
    return resp


@app.route("/single")
def present_single_summary():
    conn = psycopg2.connect(os.getenv("SUMMDATABASE"))
    cur = conn.cursor()

    ## Get the IDs this browser has seen
    seen_ids = request.cookies.get("seen_ids") or ""
    ## Get maximum ID
    cur.execute("SELECT COUNT(id) FROM litscan_article_summaries;")
    N = cur.fetchone()[0]

    ## Query to randomly select a single summary
    selected = random.randint(0, N)
    QUERY = f"SELECT * FROM litscan_article_summaries WHERE id = {selected};"
    cur.execute(QUERY)
    summ_id, rna_id, context, summary = cur.fetchone()

    app.logger.debug(rna_id)
    resp =  make_response(render_template("single_summary.html", paragraph1=summary, rna_id=rna_id, context=context, summ_id=summ_id))
    if len(seen_ids) > 0:
        seen_ids += f"{rna_id},"
    else:
        seen_ids = f"{rna_id},"

    resp.set_cookie("seen_ids", seen_ids)

    user_id = request.cookies.get("user")
    if user_id is None:
        user_id = uuid.uuid4()
        resp.set_cookie("user", str(user_id))

    return resp

@app.route("/save_single", methods=['GET', 'POST'])
def save_single_feedback():
    conn = psycopg2.connect(os.getenv("SUMMDATABASE"))
    cur = conn.cursor()

    feedback = request.json
    
    user_id = request.cookies.get("user")
    feedback['user_id'] = str(user_id)

    print(feedback)

    cur.execute("""INSERT INTO litscan_feedback_single(user_id, summary_id, feedback, 
                                contains_hallucinations, inaccurate_text, 
                                contradictory, over_specific, bad_length, 
                                mentions_ai, short_context, false_positive) VALUES (
        %(user_id)s, %(summary_id)s, %(feedback)s, %(contains_hallucinations)s, 
        %(inaccurate_text)s, %(contradictory)s, %(over_specific)s, %(bad_length)s, 
        %(mentions_ai)s, %(short_context)s, %(false_positive)s
        )""", feedback)
    
    conn.commit()

    return url_for("present_single_summary")




