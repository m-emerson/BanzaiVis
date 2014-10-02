import queries as web_queries
from flask import Flask, render_template, request
from subprocess import call
from flask.ext.script import Manager
import queries as web_queries
from BanzaiDB.fabfile import variants as queries
import json


__title__ = 'BanzaiVis'
__version__ = '0.0.1'
__description__ = "BanzaiVis manages the results of InterproScan runs"
__author__ = 'Marisa Emerson'
__author_email__ = 'exterminate@dalek.com.au'
__url__ = 'https://github.com/m-emerson/BanzaiVis'


app = Flask(__name__)
manager = Manager(app)

@manager.command
def init_db():
    """
    Initialises the database with BanzaiDB defaults
    """
    call(["BanzaiDB", "init"])

@manager.command
def populate(run_path):
    """
    Populate the datababase with nesoni mapping run using BanzaiDB
    :param run_path: full path as a string to the Banzai run (inclusive of $PROJECTBASE).
                     For example: /$PROJECTBASE/map/$REF.2014-04-28-mon-16-41-51
    """
    call(["BanzaiDB", "populate", "mapping", run_path])


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/_get_strain_ids')
def get_all_reports():
    """
    Get all the distinct strains
    """
    strains = queries.get_required_strains(None)
    return json.dumps(strains)


@app.route('/_get_locus_by_keyword', methods=['GET'])
def get_locus_by_keyword():
    """
    """
    if not request.args.get("keyword"):
        products = web_queries.get_product_by_keyword(None)
    else:
        products = web_queries.get_product_by_keyword(
            request.args.get("keyword"))
    return json.dumps(products)


@app.route('/_get_strain_details', methods=['GET'])
def get_strain_details():
    """
    """
    if request.args.get("StrainID") is None:
        return "No Strain Specified"
    strains = json.loads(request.args.get("StrainID"))
    if (len(strains) < 1):
        return 0
    strainStats = web_queries.get_raw_strain_stats(strains)
    return json.dumps(strainStats)


@app.route('/_get_snp_locus_details', methods=['GET'])
def get_snp_locus_details():
    """
    """
    if request.args.get("StrainID") is "":
        return 0
    strains = json.loads(request.args.get("StrainID"))
    lociStats = web_queries.get_loci_snp_stats(strains)
    return json.dumps(lociStats)


@app.route('/_get_details_by_product', methods=['GET'])
def get_details_by_product():
    """
    """
    products = json.loads(request.args.get("products"))
    results = web_queries.strain_loci_by_keyword(products)
    return json.dumps(results)


@app.route('/_get_distinct_loci', methods=['GET'])
def get_distinct_loci():
    """
    """
    selection = web_queries.get_distinct_loci(request.args.get("text"))
    return json.dumps(selection)


@app.route('/_get_locus_details', methods=['GET'])
def get_locus_details():
    """
    """
    if request.args.get('LocusTag') is None:
        return 0
    if request.args.get('StrainID') is None:
        return 0
    result = web_queries.get_locus_details(request.args.get('StrainID'), request.args.get('LocusTag'))
    return json.dumps(result)


if __name__ == '__main__':
    manager.run()
