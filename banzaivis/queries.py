import rethinkdb as r
import random
from BanzaiDB import database

def get_product_by_keyword(keyword):
    """
    Returns unique product name according to specified keyword
    If no keyword is specified, return all the unique products
    """
    with database.make_connection() as connection:
        if keyword is None:
            cursor = r.table('reference_features')\
                    .pluck('Product')\
                    .distinct()\
                    .run(connection)
        else:
            cursor = r.table('reference_features')\
                    .filter(lambda row:row['Product'].match(keyword))\
                    .pluck('Product')\
                    .distinct()\
                    .run(connection)
        
        return cursor

def get_raw_strain_stats(strains):
    """
    Returns raw statistics on a list of input strains
    Based off the BanzaiDB implementation but instead returns statistics in a dictonary
    format
    :param strains: list of strains e.g. ['S24EC', 'MS2493']
    """
    strainStats = []
    with database.make_connection() as connection:
        for strain in strains:
            tmp = {'StrainID' : strain}
            tmp['total'] = (r.table('determined_variants')\
                    .filter({'StrainID' : strain})\
                    .count()\
                    .run(connection))

            classes = ['substitution', 'insertion', 'deletion']
            for c in classes:
                tmp[c] = (r.table('determined_variants')\
                        .filter({'StrainID' : strain, 'Class' : c})\
                        .count()\
                        .run(connection))
            strainStats.append(tmp)

    # Correct format for JSON return
    return strainStats

def get_loci_snp_stats(strains):
    """
    Get SNP statistics for each type of variation in each locus
    Returns a dictionary in correct format to be mapped to d3.stack.layout()
    e.g. [{'class' : 'substitution', 'results' : [ {'x' : 'ECSF_0002', 'y' = 17}, { 'x' : 'ECF_0003', 'y' : 28 } ] }]
    Filtering by class and grouping by locustag is much faster than filtering by
    LocusTag and grouping by Class (Much less iterations)
    :param strains: list of strains e.g. ['S24EC', 'MS2493']
    """
    lociStats = {}

    with database.make_connection() as connection:

        # Get all possible locus tags
        tags = (r.table('reference_features')\
                .pluck('locus_tag')\
                .run(connection))

        tagList = []
        for tag in tags:
            tagList.append(tag['locus_tag'])

        filter_by = { 'Class' : ['insertion', 'deletion'],
                      'SubClass' : ['synonymous', 'non-synonymous'] }

        # Insertions and deletions
        for k, v in filter_by.items():
            for filterClass in v:
                locus_snps = list(r.table('determined_variants')\
                                .filter({'StrainID' : strains[0], k : filterClass})\
                                .group("RefFeat")\
                                .count()\
                                .ungroup()\
                                .order_by(r.row["group"])\
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
                # Rename the dictionary element with the LocusTag (rather than RefID)
                locus['group'] = stats['locus_tag']
                # Change reduction from count to frequency
                locus['reduction'] = (locus['reduction'] / locus_size)

    # Reorganise the data for use in a stacked bar chart layout (d3.js)
    layers = []
    for snpClass in lociStats:
        tLoci = []
        tmp = { 'class' : snpClass }
        tmp['values'] = []
        for locus in lociStats[snpClass]:
            if locus['group'] is None:
                continue
            tmp['values'].append( {"x" : locus['group'], "y" : locus['reduction']} )
            tLoci.append(locus['group'])
        zeroLoci = list(set(tagList) - set(tLoci)) # Locus that we've found but not in this class
        for locus in zeroLoci:
            tmp['values'].append( {"x" : locus, "y" : 0} ) # Add a zero value for the class
        tmp['values'] = sorted(tmp['values'], key=lambda k: k['x']) # Sort so all in same order
        layers.append(tmp)

    coverage = get_coverage_statistics(strains[0]) # Eventually this should actually have parameters

    return {'coverage' : coverage, 'layers' : layers }

def get_coverage_statistics(strain):
    """
    Get the coverage statistics for the specified strain
    """
    with database.make_connection() as connection:
        # All possible locus tags
        tags = list(r.table('reference_features')\
            .filter(lambda ref: 
                ref.has_fields('locus_tag')
            )
            .order_by('locus_tag')\
            .pluck('locus_tag')\
            .run(connection))
        
        coverage = list(r.table('strain_features')\
            .filter({'StrainID' : strain})\
            .has_fields('coverage', 'LocusTag')\
            .order_by('LocusTag')\
            .pluck(['LocusTag', 'coverage'])\
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
            stat = 1.0;
    
        coverage_stats.append({'x' : tag['locus_tag'], 'coverage' : float(stat)})
        numbers.append(stat)

    return coverage_stats

def strain_loci_by_keyword(products):
    """
    Takes a list of product strings, returns details about the strains
    Returns a list in a format compatible with a d3.js heatmap
    A list of dictionaries containing strainid, key and locus id
    """
    headers = ['StrainID', 'LocusTag', 'Product']
    with database.make_connection() as connection:
        result = list(r.table('determined_variants')\
                    .filter(lambda snp: r.expr(products).contains(snp['Product']))\
                    .pluck(headers)\
                    .run(connection))
    sp = {}
    
    # Get unique strains and counts
    for snp in result:
        if snp['StrainID'] in sp:
            if snp['LocusTag'] in sp[snp['StrainID']]:
                sp[snp['StrainID']][snp['LocusTag']]['count'] += 1
            if snp['LocusTag'] not in sp[snp['StrainID']]:
                sp[snp['StrainID']][snp['LocusTag']] = { 'count' : 1, 'product' : snp['Product'] }
        else:
            sp[snp['StrainID']] = { snp['LocusTag'] : { 'count' : 1, 'product' : snp['Product'] } }

    heatmap_parsed = []   
    for key in sp:
        for loci in sp[key]:
            heatmap_parsed.append( {'strain' : key, 'locus' : loci, 'count' : sp[key][loci]['count']} )

    return heatmap_parsed

def get_locus_details(strain, locus):
    """
    Gets sequence information about the specified locus
    and snp information for that locus in the specified strain

    :param strain: a string containing the strain of interest e.g. "Ec958"
    :param locus: a string containing the locus of interest e.g. "ECSF_0041"

    :returns: a dictionary containing the snps and the seq_info
    """
    with database.make_connection() as connection:
        snps = list(r.table('determined_variants')\
                    .filter({'StrainID' : strain, 'LocusTag' : locus})\
                    .order_by('Position')\
                    .run(connection))

        seq_info = list(r.table('reference_features')\
                        .filter({'locus_tag' : locus})\
                        .run(connection)) 

        result = { 'snps' : snps, 'seq_info' : seq_info }

    return result

def get_offsets(locus_tag, strain, position):
    """
    Get the offsets so the positional information is more specific
    """
    with database.make_connection() as connection:
        features = list(r.table('strain_features')\
            .filter({'StrainID' : strain})\
            .order_by('LocusTag')\
            .has_fields('indel')\
            .run(connection))

        # Get intergenetic offsets
        intergenic_regions = list(r.table('determined_variants')\
            .filter({'StrainID' : strain, 'LocusTag' : None})\
            .filter(r.row['Position'] < position)\
            .run(connection))

        intergenic_offset = 0

    for locus in features:
        if locus['LocusTag'] > locus_tag:
            break
        else:
            offset += locus['indel']

    return offset + intergenic_offset

def get_distinct_loci(query):
    with database.make_connection() as connection:
        selection = list(r.table('nesoni_report')\
            .filter(r.row['LocusTag'].match("^" + query))\
            .pluck('LocusTag')\
            .distinct()\
            .run(connection))
    
    return selection
