import logging
from typing import List
from urllib.parse import quote, unquote

from flask import Flask, render_template, request, redirect, jsonify, url_for

from models.articles import Articles

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

invalid_format = f"Not a valid QID, format must be 'Q[0-9]+'"


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Handle the form submission and redirect to the appropriate route
        qid = request.form.get("qid", "")
        limit = request.form.get("limit", "10")
        cs = request.form.get("cs", "")
        csa = request.form.get("csa", "")

        # Validate the QID (add your validation logic here)
        if not qid.startswith("Q") and qid[:1].isdigit():
            return jsonify(error=invalid_format), 400

        # Redirect to the get_articles route with the provided parameters
        url = url_for('get_articles', qid=qid, limit=limit, cs=cs, csa=csa)
        logger.debug(f"url_for: {url}")
        return redirect(url, code=302)
    return render_template("index.html")


@app.route("/<qid>", methods=["GET"])
def get_articles(qid):
    if not qid:
        qid = request.args.get("qid", "")
        if not qid:
            return jsonify(f"Got no QID")
    limit_param = request.args.get("limit", "10")
    cs_string = unquote(request.args.get("cs", ""))
    cs_affix = unquote(request.args.get("csa", ""))
    if cs_string:
        logger.debug(f"got cirrussearch string: '{cs_string}'")
    if cs_affix:
        logger.debug(f"got cirrussearch affix: '{cs_affix}'")

    try:
        limit = int(limit_param)
    except ValueError:
        return jsonify(error="Limit must be an integer."), 400

    # Call the GetArticles function with the provided string and the limit
    articles = Articles(
        qid=qid, limit=limit, cirrussearch_string=cs_string, cirrussearch_affix=cs_affix
    )
    if not articles.is_valid_qid:
        return jsonify(invalid_format)
    articles.get_items()
    article_rows = articles.get_item_html_rows()
    return render_template(
        ["results.html"],
        article_rows=article_rows,
        qid=qid,
        label=articles.label,
        link=f"https://www.wikidata.org/wiki/{qid}",
        cirrussearch_url=articles.cirrussearch_url
    )


def generate_qs_commands(main_subject: str, selected_qids: List[str]):
    commands = list()
    for qid in selected_qids:
        #  based on heuristic -> inferred from title
        commands.append(f"{qid}|P921|{main_subject}|S887|Q69652283")
    return "||".join(commands)


@app.route("/add-main-subject", methods=["POST"])
def add_main_subject():
    if request.method == "POST":
        selected_qids = request.form.getlist("selected_qids[]")
        main_subject = request.form.get("main_subject")
        if selected_qids and main_subject:
            # Handle the selected_qids as needed
            print("Selected QIDs:", selected_qids)
            commands = generate_qs_commands(
                main_subject=main_subject, selected_qids=selected_qids
            )
            # https://quickstatements.toolforge.org/#/v1=%7CCREATE%7C%7C%7CLAST%7CP31%7CQ13442814%7CS248%7CQ5188229%7CS813%7C%2B2024-01-23T00%3A00%3A00Z%2F11%7C%7C%7CLAST%7CLen%7C%22Empirical%20research%20on%20parental%20alienation%3A%20A%20descriptive%20literature%20review%22%7C%7C%7CLAST%7CP304%7C%22105572%22%7CS248%7CQ5188229%7CS813%7C%2B2024-01-23T00%3A00%3A00Z%2F11%7C%7C%7CLAST%7CP356%7C%2210.1016%2FJ.CHILDYOUTH.2020.105572%22%7CS248%7CQ5188229%7CS813%7C%2B2024-01-23T00%3A00%3A00Z%2F11%7C%7C%7CLAST%7CP407%7CQ1860%7CS248%7CQ5188229%7CS813%7C%2B2024-01-23T00%3A00%3A00Z%2F11%7C%7C%7CLAST%7CP478%7C%22119%22%7CS248%7CQ5188229%7CS813%7C%2B2024-01-23T00%3A00%3A00Z%2F11%7C%7C%7CLAST%7CP577%7C%2B2020-12-01T00%3A00%3A00Z%2F10%7CS248%7CQ5188229%7CS813%7C%2B2024-01-23T00%3A00%3A00Z%2F11%7C%7C%7CLAST%7CP1433%7CQ15753235%7CS248%7CQ5188229%7CS813%7C%2B2024-01-23T00%3A00%3A00Z%2F11%7C%7C%7CLAST%7CP1476%7Cen%3A%22Empirical%20research%20on%20parental%20alienation%3A%20A%20descriptive%20literature%20review%22%7CS248%7CQ5188229%7CS813%7C%2B2024-01-23T00%3A00%3A00Z%2F11%7C%7C%7CLAST%7CP2093%7C%22T.M.%20Marques%22%7CP1545%7C%221%22%7CS248%7CQ5188229%7CS813%7C%2B2024-01-23T00%3A00%3A00Z%2F11%7C%7C%7CLAST%7CP2093%7C%22I.%20Narciso%22%7CP1545%7C%222%22%7CS248%7CQ5188229%7CS813%7C%2B2024-01-23T00%3A00%3A00Z%2F11%7C%7C%7CLAST%7CP2093%7C%22L.C.%20Ferreira%22%7CP1545%7C%223%22%7CS248%7CQ5188229%7CS813%7C%2B2024-01-23T00%3A00%3A00Z%2F11%7C%7C
            base_url = "https://quickstatements.toolforge.org"
            endpoint = f"{base_url}/#/v1="
            url = f"{endpoint}{quote(commands)}"
            return redirect(location=url, code=302)
        return f"Error: No QIDs selected."


if __name__ == "__main__":
    app.run(debug=True)
