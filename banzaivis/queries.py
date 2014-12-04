import rethinkdb as r
from BanzaiDB import database


__title__ = 'BanzaiVis'
__version__ = '0.0.1'
__description__ = "BanzaiVis visualises results from BanzaiDB"
__author__ = 'Marisa Emerson'
__author_email__ = 'exterminate@dalek.com.au'
__url__ = 'https://github.com/m-emerson/BanzaiVis'


def get_product_by_keyword(keyword=None):
    """
    Returns unique product name according to specified keyword

    If no keyword is specified, return all the unique products

    :param keyword: string containing a keyword relating to gene function e.g.
                    "metabolism"

    :returns: list of found product names matching specified keyword
    """
    with database.make_connection() as connection:
        if keyword is None:
            cursor = list(r.table('reference_features')\
                      .pluck('product')\
                      .distinct()\
                      .run(connection))
        else:
            cursor = list(r.table('reference_features')\
                      .filter(lambda row: row['product'].match(keyword))\
                      .pluck('product')\
                      .distinct()\
                      .run(connection))
        return cursor


def get_raw_strain_stats(strains):
    """
    Returns raw statistics on a list of input strains

    Based off the BanzaiDB implementation but instead returns statistics in a
    dictonary format

    :param strains: list of strains e.g. ['S24EC', 'MS2493']

    :returns: list of dictionaries with variance statistics for each strain

    Example::
        [{'StrainID': u'HVM1619', 'total': 15521, 'deletion': 259,
        'insertion': 95, 'substitution': 15167}]
    
    """
    strainStats = []
    with database.make_connection() as connection:
        for strain in strains:
            tmp = {'StrainID': strain}
            tmp['total'] = (r.table('determined_variants')
                             .get_all(strain, index='StrainID')
                             .count()
                             .run(connection))
            classes = ['substitution', 'insertion', 'deletion']
            for c in classes:
                tmp[c] = (r.table('determined_variants')
                           .get_all(strain, index='StrainID')
                           .filter({'Class': c})
                           .count()
                           .run(connection))
            strainStats.append(tmp)
    return strainStats


def get_loci_snp_stats(strains):
    """
    Get SNP statistics for each type of variation in each locus

    Returns a dictionary in correct format to be mapped to d3.stack.layout()

    Example::

        [{'class' : 'substitution', 'results' : [ {'x' : 'ECSF_0002', 'y' = 17}
         ,{ 'x' : 'ECF_0003', 'y' : 28 } ] }]

    .. note:: Group and Count uses RethinkDB's MapReduce

    :param strains: list of strains e.g. ['S24EC', 'MS2493']

    :returns: Raw statistics on the type of variants at each locus of the specified
              strains
    """
    lociStats = {}
    with database.make_connection() as connection:
        # Get all possible locus tags
        tags = (r.table('reference_features')
                 .pluck('locus_tag')
                 .run(connection))
        tagList = []
        for tag in tags:
            tagList.append(tag['locus_tag'])
        filter_by = {'Class': ['insertion', 'deletion'],
                     'SubClass': ['synonymous', 'non-synonymous']}

        for k, v in filter_by.items():
            for filterClass in v:
                locus_snps = list(r.table('determined_variants')
                                   .get_all(strains[0], index='StrainID')
                                   .filter({k: filterClass})
                                   .group("RefFeat")
                                   .count()
                                   .ungroup()
                                   .order_by(r.row["group"])
                                   .run(connection))
                lociStats[filterClass] = locus_snps

        # find locus information via ref_feat table and determine frequency
        for k in lociStats:
            for locus in lociStats[k]:
                # Skip snps that don't have a specified locus
                if locus['group'] is None:
                    continue
                stats = r.table('reference_features')\
                         .get(locus['group'])\
                         .pluck('locus_tag', 'start', 'end')\
                         .run(connection)
                locus_size = float(stats['end'] - stats['start'])
                # Rename the dictionary element with the LocusTag
                # (rather than RefID)
                locus['group'] = stats['locus_tag']
                # Change reduction from count to frequency
                locus['reduction'] = (locus['reduction'] / locus_size)
    # Reorganise the data for use in a stacked bar chart layout (d3.js)
    layers = []
    for snpClass in lociStats:
        tLoci = []
        tmp = {'class': snpClass}
        tmp['values'] = []
        for locus in lociStats[snpClass]:
            if locus['group'] is None:
                continue
            tmp['values'].append({"x": locus['group'], "y":
                                  locus['reduction']})
            tLoci.append(locus['group'])
        # Locus that we've found but not in this class
        zeroLoci = list(set(tagList) - set(tLoci))
        for locus in zeroLoci:
            # Add a zero value for the class
            tmp['values'].append({"x": locus, "y": 0})
        # Sort so all in same order
        tmp['values'] = sorted(tmp['values'], key=lambda k: k['x'])
        layers.append(tmp)

    # Eventually this should actually have parameters
    coverage = get_coverage_statistics(strains[0], [])
    return {'coverage': coverage, 'layers': layers}


def get_coverage_statistics(strain, loci):
    """
    Get the coverage statistics for the specified strain. If any loci are
    specified, return coverage statistics for those loci only, otherwise return
    coverage statistics for all loci.

    .. note:: To save space, BanzaiDB only records unusual coverage statistics
        Entries that don't exist have a coverage of 1.0
        Entries are generated with a coverage of 1.0 if no coverage field is
        recorded in the strain_features table

    :param strain: string containing strain id
    :param loci: list containing loci of interest. An empty list will return
        all coverage values in all loci

    :returns: Coverage statistics as a python dictionary in the format:
        [{ 'x': LOCUS_TAG, 'coverage': FLOAT }]
    """

    headers = ['LocusTag', 'coverage']

    with database.make_connection() as connection:
        # If a locus is specified, return only one entry
        if loci:
            tags = sorted(loci)
            coverage =  list(r.table('strain_features')
                .filter({'StrainID': strain})
                .filter(lambda feature: r.expr(loci).contains(feature['LocusTag']))
                .order_by('LocusTag')
                .run(connection))

        # Otherwise, find all locus tags in this strain and generate coverage
        # statistics for each locus in the strain        
        else:
            tags = list(r.table('reference_features')
                     .filter(lambda ref: ref.has_fields('locus_tag'))
                     .order_by('locus_tag')
                     .pluck('locus_tag')
                     .run(connection))
            coverage = list(r.table('strain_features')
                         .filter({'StrainID':strain})
                         .has_fields('coverage', 'LocusTag')
                         .order_by('LocusTag')
                         .pluck(headers)
                         .run(connection))

            # Convert tags to a list containing only locustags
            tags = [x['locus_tag'] for x in tags]

    coverage_stats = []
    count = 0
    for tag in tags:
        if count > len(coverage):
            break
        if len(coverage) == 0 or tag != coverage[count]['LocusTag']:
            stat = 1.0 
        else:
            stat = coverage[count]['coverage']
            count += 1
        coverage_stats.append({'x': tag, 'coverage': float(stat)})
    return coverage_stats


def strain_loci_by_keyword(products):
    """
    Takes a list of product strings, returns details about snps within each
    strain for loci related to those gene products
    
    :param products: list of product strings
        e.g ["putative transport protein", "hypothetical protein"]

    :returns: a list of dictionaries containing the snp count at each strain and locus
        e.g [{'count': 7, 'strain': u'S92EC', 'locus': u'ECSF_4143'}]

    """
    headers = ['StrainID', 'LocusTag', 'Product']
    with database.make_connection() as connection:
        result = list(r.table('determined_variants')
                       .filter(lambda snp: r.expr(products)
                               .contains(snp['Product']))
                       .pluck(headers)
                       .run(connection))
    sp = {}
    # Get unique strains and counts
    for snp in result:
        if snp['StrainID'] in sp:
            if snp['LocusTag'] in sp[snp['StrainID']]:
                sp[snp['StrainID']][snp['LocusTag']]['count'] += 1
            if snp['LocusTag'] not in sp[snp['StrainID']]:
                sp[snp['StrainID']][snp['LocusTag']] = {'count': 1, 'product': snp['Product']}
        else:
            sp[snp['StrainID']] = {snp['LocusTag']: {'count': 1, 'product': snp['Product']}}

    heatmap_parsed = []

    for key in sp:
        for loci in sp[key]:
            heatmap_parsed.append({'strain': key, 'locus': loci, 'count': sp[key][loci]['count']})

    return heatmap_parsed


def get_locus_details(strain, locus):
    """
    Get sequence & SNP info about the specified locus in the specified strain

    :param strain: a string containing the strain of interest e.g. "Ec958"

    :param locus: a string containing the locus of interest e.g. "ECSF_0041"

    :returns: a dictionary containing SNP data for the specified strain and locus 
    """
    with database.make_connection() as connection:
        snps = list(r.table('determined_variants')
                     .get_all(strain, index='StrainID')
                     .filter({'LocusTag': locus})
                     .has_fields('LocusTag')
                     .order_by('CDSBaseNum')
                     .run(connection))
    return snps


def get_reference_features(locus):
    """
    Get reference features for the specified locustag

    :param locus: a string containing the locus of interest e.g. "ECSF_0041"
    
    :returns: a dictionary containing reference feature data
    """
    with database.make_connection() as connection:
        seq_info = list(r.table('reference_features')
                        .filter({'locus_tag': locus})
                        .run(connection))

    return seq_info    


