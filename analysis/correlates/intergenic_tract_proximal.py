'''
intergenic_tract_proximal.py - get rho at
gene proximal sites in intergenic tracts

--split - if selected 'right', will always return
'right' 2 kb even if tracts are 2-4 kb - same goes
for if 'left' is selected

default behaviour otherwise is to split the tracts in
half, making 'left' and 'right' < 2 kb each
'''

import argparse
from tqdm import tqdm
import antr
import csv

def args():
    parser = argparse.ArgumentParser(
        description='rho at gene proximal intergenic regions', 
        usage='python3.5 intergenic_tract_proximal.py [options]')

    parser.add_argument('-f', '--fname', required=True,
                        type=str, help='Intergenic tracts tsv')
    parser.add_argument('-t', '--table', required=True,
                        type=str, help='Annotation table (txt.gz)')
    parser.add_argument('-w', '--windowsize', required=True,
                        type=int, help='Window considered gene proximal')
    parser.add_argument('-s', '--split', required=False,
                        type=str, help='Split tracts left/right? (See docs)')
    parser.add_argument('-o', '--outfile', required=True,
                        type=str, help='File to write to')

    args = parser.parse_args()

    return args.fname, args.table, args.windowsize, args.split, args.outfile

def gene_proximal_per_tract(line, table, windowsize, split):
    ''' (str, str, int, str) -> list?
    takes in a single input tract 'line' from tsv
    and calculates rho at gene proximal sites

    accounts for tracts where length < windowsize
    (ie entire tract is gene proximal) - in this case,
    splits tract into halves and calls them 'left' and 'right'
    (despite both being < windowsize) to maintain structure of outfile
    '''
    chrom, start, end = line['chrom'], int(line['start']), int(line['end'])
    tract_size = end - start
    if tract_size > (2 * windowsize):
        left_start, left_end = start, start + windowsize
        right_start, right_end = end - windowsize, end
    elif tract_size <= (2 * windowsize) and tract_size > windowsize:
        if not split:
            # split into half for 'left' + 'right'
            left_start, left_end = start, start + (tract_size / 2)
            right_start, right_end = start + (tract_size / 2), end
        elif split == 'left':
            left_start, left_end = start, start + 2000
            right_start, right_end = left_end, end
        elif split == 'right':
            right_start, right_end = end - 2000, end
            left_start, left_end = start, right_start
    elif tract_size < (2 * windowsize): # do split thing again
        # downstream script can add rho vals and count for full tract
        left_start, left_end = start, start + (tract_size / 2)
        right_start, right_end = start + (tract_size / 2), end
    left_vals, right_vals = 0.0, 0.0
    left_count, right_count = 0, 0
    p = antr.Reader(table)
    for record in p.fetch(chrom, left_start, left_end):
        if record.ld_rho != 'NA':
            left_vals += record.ld_rho
            left_count += 1
    for record in p.fetch(chrom, right_start, right_end):
        if record.ld_rho != 'NA':
            right_vals += record.ld_rho
            right_count += 1
    return left_vals, left_count, right_vals, right_count, tract_size


def parse_tracts(fname, table, windowsize, split, outfile):
    ''' (str, str, int, str) -> None
    iterates through input tract file and uses gene_proximal_per_tract
    to calculate rho in 'left gene proximal' and 'right gene proximal' regions
    '''
    with open(outfile, 'w', newline='') as f_out:
        fieldnames = ['chrom', 'start', 'end', 'tract_size', 'left_vals', 
                'left_count', 'left_window', 'right_vals', 'right_count', 
                'right_window', 'windowsize']
        writer = csv.DictWriter(f_out, delimiter='\t', fieldnames=fieldnames)
        writer.writeheader()
        with open(fname, 'r', newline='') as f_in:
            reader = csv.DictReader(f_in, delimiter='\t')
            for line in tqdm(reader):
                tract_size = int(line['tract_size'])
                if tract_size > 1:
                    left_vals, left_count, right_vals, \
                        right_count, tract_size = gene_proximal_per_tract(line,
                                table, windowsize, split)
                    writer.writerow(
                        {'chrom': line['chrom'], 'start': line['start'],
                         'end': line['end'], 'tract_size': tract_size,
                         'left_vals': left_vals, 'left_count': left_count,
                         'left_window': left_vals / left_count,
                         'right_vals': right_vals, 'right_count': right_count,
                         'right_window': right_vals / right_count,
                         'windowsize': windowsize}
                        )

def main():
    fname, table, windowsize, split, outfile = args()
    parse_tracts(fname, table, windowsize, split, outfile)

if __name__ == '__main__':
    main()

        

