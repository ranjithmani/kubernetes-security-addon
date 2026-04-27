import sys, json

releases = json.load(sys.stdin)
if not releases:
    print('NOT_INSTALLED')
else:
    chart = releases[0].get('chart', '')
    status = releases[0].get('status', '')
    print(f'CHART={chart} STATUS={status}')
