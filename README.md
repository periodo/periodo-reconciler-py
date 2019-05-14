# periodo-reconciler-py
a Python wrapper around [periodo/periodo-reconciler: Open Refine reconciliation service for PeriodO data](https://github.com/periodo/periodo-reconciler)

# How to run the CSV reconciler on the test data

```
periodo-reconciler-py --location="Context (1)" --query="Period" --start="Early BCE/CE" --stop="Late BCE/CE" --transpose-query --match_top_candidate --match_summary_output="test-summary/OpenContext/Cyprus PKAP Survey.csv"  "test-data/OpenContext/Cyprus PKAP Survey.csv" "test-output/OpenContext/Cyprus PKAP Survey.csv" 

periodo-reconciler-py --location="Context (1)" --query="Period" --start="Early BCE/CE" --stop="Late BCE/CE" --ignored_queries="Not determined" --match_top_candidate --match_summary_output="test-summary/OpenContext/European Cattle with Periods.csv" "test-data/OpenContext/European Cattle with Periods.csv" "test-output/OpenContext/European Cattle with Periods.csv"

periodo-reconciler-py --location="Context (1)" --query="Culture" --start="Early BCE/CE" --stop="Late BCE/CE" --ignored_queries="other,lb" --match_top_candidate  --match_summary_output="test-summary/OpenContext/Petra Artifacts.csv" "test-data/OpenContext/Petra Artifacts.csv" "test-output/OpenContext/Petra Artifacts.csv"
```
