import argparse
import csv
import sys

# in bst_all.txt:
#   [6:10]  AAAA  international number ID
#   [12:15] BBB   number of data lines
#   [16:20] CCCC  tropical cyclone number ID in JMA (may be blank)
#   [21:25] DDDD  international number ID, repeated
#   [26]    E     flag of the last data line
#   [28]    F     revision flag
#   [30:50] name  storm name, right-justified (blank if unnamed)
#   [64:72] date  date of the latest revision, yyyymmdd
_HDR_MIN_LEN = 72

FIELDNAMES = [
    'intl_id', 'storm_number', 'storm_name', 'last_revision_date',
    'datetime', 'year', 'month', 'day', 'hour',
    'indicator', 'grade', 'latitude', 'longitude', 'pressure', 'wind_speed',
    'dir_r50', 'r50_long', 'r50_short',
    'dir_r30', 'r30_long', 'r30_short',
    'landfall',
]


def parse_time_token(tok):
    yy, mm, dd, hh = int(tok[0:2]), int(tok[2:4]), int(tok[4:6]), int(tok[6:8])
    year = 1900 + yy if yy >= 51 else 2000 + yy
    return year, mm, dd, hh


def parse_bst(path):
    storm = None
    with open(path, encoding='utf-8', errors='replace') as f:
        for raw_line in f:
            line = raw_line.rstrip('\r\n')
            if not line.strip():
                continue

            if line.startswith('66666'):
                l2 = line.ljust(_HDR_MIN_LEN)
                intl_id = l2[6:10].strip()
                storm_number = l2[16:20].strip()
                name = l2[30:50].strip()
                rev_date = l2[64:72].strip()
                if not (intl_id.isdigit() and len(rev_date) == 8 and rev_date.isdigit()):
                    print(f"WARNING: unparsed header line: {line!r}", file=sys.stderr)
                    storm = None
                    continue
                storm = {
                    'intl_id': intl_id,
                    'storm_number': storm_number or None,
                    'storm_name': name or None,
                    'last_revision_date': rev_date,
                }
                continue

            if storm is None:
                print(f"WARNING: data line before any header, skipped: {line!r}", file=sys.stderr)
                continue

            toks = line.split()
            if len(toks) < 6:
                print(f"WARNING: too few fields, skipped: {line!r}", file=sys.stderr)
                continue

            year, month, day, hour = parse_time_token(toks[0])
            row = dict(storm)
            row.update({
                'datetime': toks[0],
                'year': year, 'month': month, 'day': day, 'hour': hour,
                'indicator': toks[1],
                'grade': toks[2],
                'latitude': toks[3],
                'longitude': toks[4],
                'pressure': toks[5],
                'wind_speed': toks[6] if len(toks) >= 7 else '',
                'dir_r50': '', 'r50_long': '', 'r50_short': '',
                'dir_r30': '', 'r30_long': '', 'r30_short': '',
                'landfall': '',
            })

            # H+IIII and K+LLLL are printed with no space between the
            # 1-digit direction and the 4-digit radius, e.g. "30180".
            if len(toks) >= 11:
                r50 = toks[7]
                r30 = toks[9]
                row['dir_r50'] = r50[0]
                row['r50_long'] = r50[1:]
                row['r50_short'] = toks[8]
                row['dir_r30'] = r30[0]
                row['r30_long'] = r30[1:]
                row['r30_short'] = toks[10]

            if len(toks) == 12:
                row['landfall'] = 'Y' if toks[11] == '#' else toks[11]

            yield row


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('input', help='raw bst_all.txt file')
    ap.add_argument('output', help='output CSV path')
    ap.add_argument('--start-year', type=int, required=True,
                    help='first year to include, e.g. 2000')
    ap.add_argument('--end-year', type=int, required=True,
                    help='last year to include, e.g. 2025')
    args = ap.parse_args()

    if args.start_year > args.end_year:
        ap.error('--start-year cannot be greater than --end-year')

    n_in = n_landfall = n_out = 0
    storms_seen = set()

    with open(args.output, 'w', newline='', encoding='utf-8') as out_f:
        writer = csv.DictWriter(out_f, fieldnames=FIELDNAMES)
        writer.writeheader()

        for row in parse_bst(args.input):
            n_in += 1

            # Keep ONLY raw BST records marked with #, which parse_bst()
            # converts to landfall='Y'.
            if row['landfall'] != 'Y':
                continue

            n_landfall += 1

            # Inclusive year filter: start year <= row year <= end year
            if args.start_year <= row['year'] <= args.end_year:
                writer.writerow(row)
                n_out += 1
                storms_seen.add((row['intl_id'], row['storm_name']))

    print(f"Parsed {n_in} raw data rows.")
    print(f"Found {n_landfall} landfall rows in the full BST file.")
    print(f"Wrote {n_out} landfall rows ({len(storms_seen)} storms) for "
          f"{args.start_year}-{args.end_year} -> {args.output}")


if __name__ == '__main__':
    main()
