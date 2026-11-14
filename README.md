# btc-cent-forecast

Entry for the make.fun bounty "btc-cent-forecast-01": forecast Bitcoin price 240 minutes after each
checkpoint from the 4,320 one-minute closes ending at it, scored by mean absolute error in cents.

main.py (Python 3.13, standard library only) reads every *.in case file in the input directory and
writes one *.out forecast per case.
