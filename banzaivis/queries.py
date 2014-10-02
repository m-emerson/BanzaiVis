import rethinkdb as r
from BanzaiDB import database


__title__ = 'BanzaiVis'
__version__ = '0.0.1'
__description__ = "BanzaiVis manages the results of InterproScan runs"
__author__ = 'Marisa Emerson'
__author_email__ = 'exterminate@dalek.com.au'
__url__ = 'https://github.com/m-emerson/BanzaiVis'


def get_product_by_keyword(keyword):
    """
    Returns unique product name according to specified keyword

    If no keyword is specified, return all the unique products

    :param keyword: TODO

    :returns: TODO
    """
    with database.make_connection() as connection:
        if keyword is None:
            cursor = r.table('reference_features')\
                      .pluck('Product')\
                      .distinct()\
                      .run(connection)
        else:
            cursor = r.table('reference_features')\
                      .filter(lambda row: row['Product'].match(keyword))\
                      .pluck('Product')\
                      .distinct()\
                      .run(connection)
        return cursor


def get_raw_strain_stats(strains):
    """
    Returns raw statistics on a list of input strains

    Based off the BanzaiDB implementation but instead returns statistics in a
    dictonary format

    :param strains: list of strains e.g. ['S24EC', 'MS2493']

    :returns: TODO
    """
    strainStats = []
    with database.make_connection() as connection:
        for strain in strains:
            tmp = {'StrainID': strain}
            tmp['total'] = (r.table('determined_variants')
                             .filter({'StrainID': strain})
                             .count()
                             .run(connection))
            classes = ['substitution', 'insertion', 'deletion']
            for c in classes:
                tmp[c] = (r.table('determined_variants')
                           .filter({'StrainID': strain, 'Class': c})
                           .count()
                           .run(connection))
            strainStats.append(tmp)
    # Correct format for JSON return
    return strainStats


def get_loci_snp_stats(strains):
    """
    Get SNP statistics for each type of variation in each locus

    Returns a dictionary in correct format to be mapped to d3.stack.layout()

    Example::

        [{'class' : 'substitution', 'results' : [ {'x' : 'ECSF_0002', 'y' = 17}
         ,{ 'x' : 'ECF_0003', 'y' : 28 } ] }]

    .. note:: Filtering by class and grouping by LocusTag is much faster than
              filtering by LocusTag and grouping by class (much less
              iterations)

    :param strains: list of strains e.g. ['S24EC', 'MS2493']

    :returns: TODO
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
        # Insertions and deletions
        for k, v in filter_by.items():
            for filterClass in v:
                locus_snps = list(r.table('determined_variants')
                                   .filter({'StrainID': strains[0],
                                            k: filterClass})
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
    coverage = get_coverage_statistics(strains[0])
    return {'coverage': coverage, 'layers': layers}


def get_coverage_statistics(strain):
    """
    Get the coverage statistics for the specified strain

    :param strain: TODO

    :returns: TODO
    """
    with database.make_connection() as connection:
        # All possible locus tags
        tags = list(r.table('reference_features')
                     .filter(lambda ref: ref.has_fields('locus_tag'))
                     .order_by('locus_tag')
                     .pluck('locus_tag')
                     .run(connection))
        coverage = list(r.table('strain_features')
                         .filter({'StrainID': strain})
                         .has_fields('coverage', 'LocusTag')
                         .order_by('LocusTag')
                         .pluck(['LocusTag', 'coverage'])
                         .run(connection))
    coverage_stats = []
    numbers = []
    count = 0
    for tag in tags:
        if count >= len(coverage):
            break
        if tag['locus_tag'] == coverage[count]['LocusTag']:
            stat = coverage[count]['coverage']
            count += 1
        else:
            stat = 1.0
        coverage_stats.append({'x': tag['locus_tag'], 'coverage': float(stat)})
        numbers.append(stat)
    return coverage_stats


def strain_loci_by_keyword(products):
    """
    Takes a list of product strings, returns details about the strains

    Returns a list in a format compatible with a d3.js heatmap

    A list of dictionaries containing strainid, key and locus id

    :param products: TODO

    :returns: TODO
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

    :returns: a dictionary containing the snps and the seq_info
    """
    with database.make_connection() as connection:
        snps = list(r.table('determined_variants')
                     .filter({'StrainID': strain, 'LocusTag': locus})
                     .order_by('Position')
                     .run(connection))
        seq_info = list(r.table('reference_features')
                         .filter({'locus_tag': locus})
                         .run(connection))
        result = {'snps': snps, 'seq_info': seq_info}
    return result


def get_offsets(locus_tag, strain, position):
    """
    Get the offsets so the positional information is more specific

    .. warning: offset is not initialized...

    :param locus_tag: TODO

    :param strain: TODO

    :param position: TODO

    :returns: TODO
    """
    with database.make_connection() as connection:
        features = list(r.table('strain_features')
                         .filter({'StrainID': strain})
                         .order_by('LocusTag')
                         .has_fields('indel')
                         .run(connection))
        # Get intergenetic offsets
        intergenic_regions = list(r.table('determined_variants')
                                   .filter({'StrainID': strain,
                                            'LocusTag': None})
                                   .filter(r.row['Position'] < position)
                                   .run(connection))
        intergenic_offset = 0
    for locus in features:
        if locus['LocusTag'] > locus_tag:
            break
        else:
            offset += locus['indel']
    return offset + intergenic_offset


def get_distinct_loci(query):
    """
    TODO: Document me

    :param query: TODO

    :returns: TODO
    """
    with database.make_connection() as connection:
        selection = list(r.table('nesoni_report')
                          .filter(r.row['LocusTag'].match("^" + query))
                          .pluck('LocusTag')
                          .distinct()
                          .run(connection))
    return selection
