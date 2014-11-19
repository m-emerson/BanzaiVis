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
    return render_template('404.html'), 404


@app.route('/')
def index():
    return render_template('index.html')


# /strains/list
class Strains(Resource):
    def get(self):
        return queries.get_required_strains(None)


# /strains/stats
class StrainStats(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('sid', type=str, required=True,
            action='append', help='Error: requires sid parameter', location='args')
        super(StrainStats, self).__init__()

    def get(self):
        args = self.reqparse.parse_args()
        return web_queries.get_raw_strain_stats(args['sid'])


# /products/search  
class ProductByKeyword(Resource):
    """
    """
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('keyword', type=str, required=True,
            help='Error: requires "keyword" parameter', location='args')
        super(ProductByKeyword, self).__init__()

    def get(self):
        args = self.reqparse.parse_args()
        return web_queries.get_product_by_keyword(args['keyword'])


# /products/list
class ProductList(Resource):
    """
    """
    def get(self):
        return web_queries.get_product_by_keyword()


# /variants/list
# List all variants for specified strain
class VarianceStats(Resource):
    """
    """
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('sid', type=str, required=True,
            action='append', help='Error: requires sid parameter', location='args')
        super(VarianceStats, self).__init__()
    
    def get(self):
        args = self.reqparse.parse_args()
        return web_queries.get_loci_snp_stats(args['sid'])


# /variants/locus
# list all variants for specified strain and specified locus
class VarianceLookup(Resource):
    """
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


# localhost/product/products
class DetailsByProduct(Resource):
    """
    """
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('products', type=str, action='append',
            required=True, help='No product specified', location='args')
        super(DetailsByProduct, self).__init__()

    def get(self):
        args = self.reqparse.parse_args()
        return web_queries.strain_loci_by_keyword(args['products'])


# localhost/locus/ => Give us a list of all available locus
class DetailsByLocus(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        pass         


# /reference/locus
class ReferenceList(Resource):
    """
    """
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('locus', type=str, required=True,
            help='Error: requires sid parameter', location='args')
        super(DetailsByProduct, self).__init__()
       
    def get(self):
        args = self.reqparse.parse_args()
        return web_queries.get_reference_features(args['locus'])


# /coverage/list
class Coverage(Resource):
    """
    """
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('sid', type=str, required=True,
            help='Error: requires sid parameter', location='args')
        self.reqparse.add_argument('locus', type=str, action='append', location='args')
        super(Coverage, self).__init__()
    
    def get(self):
        args = self.reqparse.parse_args()
        print args
        if args['locus']:
            return web_queries.get_coverage_statistics(args['sid'], args['locus'])
        else:
            return web_queries.get_coverage_statistics(args['sid'], [])


# /coverage/locus
@app.route('/_get_strain_ids')
def get_all_reports():
    """
    Get all the distinct strains
    """
    strains = queries.get_required_strains(None)
    return json.dumps(strains)


@app.route('/_get_details_by_product', methods=['GET'])
def get_details_by_product():
    """
    Get strain and locus details according to specified gene product
    """
    products = json.loads(request.args.get("products"))
    results = web_queries.strain_loci_by_keyword(products)
    return json.dumps(results)


# api urls
api.add_resource(Strains, '/strains/list')
api.add_resource(StrainStats, '/strains/stats')
api.add_resource(ProductByKeyword, '/products/search')
api.add_resource(VarianceStats, '/variants/list')
api.add_resource(VarianceLookup, '/variants/locus')
api.add_resource(Coverage, '/coverage/list')

if __name__ == '__main__':
    manager.run()
