import queries as web_queries
from flask import Flask, render_template, request
from flask.ext.restful import Resource, Api, reqparse
from subprocess import call
from flask.ext.script import Manager
import queries as web_queries
from BanzaiDB.fabfile import variants as queries
import json


__title__ = 'BanzaiVis'
__version__ = '0.0.1'
__description__   = "BanzaiVis visualises results from BanzaiDB"
__author__ = 'Marisa Emerson'
__author_email__ = 'exterminate@dalek.com.au'
__url__ = 'https://github.com/m-emerson/BanzaiVis'


app = Flask(__name__)
manager = Manager(app)
api = Api(app)

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
    """
    Handle page not found errors
    """
    return render_template('404.html'), 404


@app.route('/')
def index():
    return render_template('index.html')


class Strains(Resource):
    """
    Returns JSON list of available strains
    """
    def get(self):
        return queries.get_required_strains(None)


class StrainStats(Resource):
    """
    Returns JSON list of raw snp values according to strainid

    Example::
         [
            { "StrainID": "HVM1299",
              "deletion" : 273,
              "insertion": 82,
              "substitution": 14934,
              "total": 15289
            }
         ]

    :requires: strain identifier as 'sid' parameter
    """
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('sid', type=str, required=True,
            action='append', help='Error: requires sid parameter', location='args')
        super(StrainStats, self).__init__()

    def get(self):
        args = self.reqparse.parse_args()
        return web_queries.get_raw_strain_stats(args['sid'])


class ProductByKeyword(Resource):
    """
    Returns JSON list of products according to specified keyword
    
    Example::

         [
            {
                "product": "fatty acid metabolism regulator protein"
            }
         ] 

    :requires: search keyword as 'keyword' parameter
    """
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('keyword', type=str, required=True,
            help='Error: requires "keyword" parameter', location='args')
        super(ProductByKeyword, self).__init__()

    def get(self):
        args = self.reqparse.parse_args()
        return web_queries.get_product_by_keyword(args['keyword'])


class ProductList(Resource):
    """
    Returns JSON list of all unique gene products
    """
    def get(self):
        return web_queries.get_product_by_keyword()


class VarianceStats(Resource):
    """
    Returns JSON list of all variants for specified strain

    :requires: strainid as 'sid' parameter
    """
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('sid', type=str, required=True,
            action='append', help='Error: requires sid parameter', location='args')
        super(VarianceStats, self).__init__()
    
    def get(self):
        args = self.reqparse.parse_args()
        return web_queries.get_loci_snp_stats(args['sid'])


class VarianceLookup(Resource):
    """
    Returns JSON list of all variants for specified strain and specified locus
    """
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('sid', type=str, required=True,
            help='Error: requires sid parameter', location='args')
        self.reqparse.add_argument('locus', type=str, required=True,
            help='Error: requires locus parameter', location='args')
        super(VarianceLookup, self).__init__()

    def get(self):
        args = self.reqparse.parse_args()
        return web_queries.get_locus_details(args['sid'], args['locus'])


class DetailsByProduct(Resource):
    """
    Returns JSON list of snps within each strain for loci related to
    specified gene product
    """
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('products', type=str, action='append',
            required=True, help='No product specified', location='args')
        super(DetailsByProduct, self).__init__()

    def get(self):
        args = self.reqparse.parse_args()
        return web_queries.strain_loci_by_keyword(args['products'])


class ReferenceList(Resource):
    """
    Returns JSON list of reference features according to specified locus
   
    :requires: locustag as 'locus' parameter  
    """
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('locus', type=str, required=True,
            help='Error: requires locus parameter', location='args')
        super(ReferenceList, self).__init__()
       
    def get(self):
        args = self.reqparse.parse_args()
        return web_queries.get_reference_features(args['locus'])


class Coverage(Resource):
    """
    Returns a list of dictionaries containing locus and coverage information
      for specified strain and (optionally) locus

    :requires: strainid as 'sid' parameter
    :optional: locustag as 'locus' parameter
    """
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('sid', type=str, required=True,
            help='Error: requires sid parameter', location='args')
        self.reqparse.add_argument('locus', type=str, action='append', location='args')
        super(Coverage, self).__init__()
    
    def get(self):
        args = self.reqparse.parse_args()
        if args['locus']:
            return web_queries.get_coverage_statistics(args['sid'], args['locus'])
        else:
            return web_queries.get_coverage_statistics(args['sid'], [])


api.add_resource(Strains, '/strains/list')
api.add_resource(StrainStats, '/strains/stats')
api.add_resource(ProductByKeyword, '/products/search')
api.add_resource(VarianceStats, '/variants/list')
api.add_resource(VarianceLookup, '/variants/locus')
api.add_resource(Coverage, '/coverage/list')
api.add_resource(ReferenceList, '/reference/locus')

if __name__ == '__main__':
    manager.run()
