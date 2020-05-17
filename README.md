# periodo-reconciler-py
a Python wrapper around [periodo/periodo-reconciler: Open Refine reconciliation service for PeriodO data](https://github.com/periodo/periodo-reconciler)

# Setting up a local development environment

Get the [periodo/periodo-reconciler: Open Refine reconciliation service for PeriodO data](https://github.com/periodo/periodo-reconciler) running on your local machine. 

For example, on macOS, one can install nodejs with homebrew with

```
brew install node
``` 

and keep it updated with

```
brew upgrade node
```

and then [update npm](https://www.npmjs.com/get-npm)

```
npm install npm@latest -g
```

Finally install `periodo-reconciler`

```
npm install -g periodo-reconciler
```

Where to get the latest reconciliation data?

<http://n2t.net/ark:/99152/p0d.json>

Download the dataset and then run `periodo-reconciler` on it:

```
periodo-reconciler p0d.json
```

# How to run the CSV reconciler on the test data

```
periodo-reconciler-py --location="Context (1)" --query="Period" --start="Early BCE/CE" --stop="Late BCE/CE" --transpose-query --match_top_candidate --match_summary_output="test-summary/OpenContext/Cyprus PKAP Survey.csv"  "test-data/OpenContext/Cyprus PKAP Survey.csv" "test-output/OpenContext/Cyprus PKAP Survey.csv" 

periodo-reconciler-py --location="Context (1)" --query="Period" --start="Early BCE/CE" --stop="Late BCE/CE" --ignored_queries="Not determined" --match_top_candidate --match_summary_output="test-summary/OpenContext/European Cattle with Periods.csv" "test-data/OpenContext/European Cattle with Periods.csv" "test-output/OpenContext/European Cattle with Periods.csv"

periodo-reconciler-py --location="Context (1)" --query="Culture" --start="Early BCE/CE" --stop="Late BCE/CE" --ignored_queries="other,lb" --match_top_candidate  --match_summary_output="test-summary/OpenContext/Petra Artifacts.csv" "test-data/OpenContext/Petra Artifacts.csv" "test-output/OpenContext/Petra Artifacts.csv"
```
