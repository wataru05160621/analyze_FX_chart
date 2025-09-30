# FX Filter Analysis Tool

## Overview
This tool analyzes your Notion database entries from the past 3 weeks to identify why all trades are being filtered out. It examines which filters are triggering most frequently and provides specific recommendations for adjustments.

## Files Created
- `analyze_notion_filters.py` - Main analysis script
- `run_filter_analysis.sh` - Shell script to run analysis with virtual environment
- `README_FILTER_ANALYSIS.md` - This documentation

## How to Run

### Option 1: Using the Shell Script
```bash
./run_filter_analysis.sh
```

### Option 2: Manual Virtual Environment Activation
```bash
# Activate virtual environment
source venv/bin/activate

# Run analysis
python analyze_notion_filters.py

# Deactivate virtual environment
deactivate
```

### Option 3: Using Python from Virtual Environment
```bash
./venv/bin/python analyze_notion_filters.py
```

## What the Analysis Does

### 1. Data Fetching
- Connects to your Notion database using existing credentials
- Fetches all entries from the past 3 weeks
- Extracts relevant filter-related data

### 2. Filter Analysis
The script analyzes these filters from your `core_v2.py`:

- **ATR Filter**: Must be ≥ 7 pips
- **Spread Filter**: Must be ≤ 2 pips
- **News Window Filter**: Avoids session opens (9:00, 15:00, 22:00 JST)
- **Build-up Quality Filter**: Needs 2/3 conditions:
  - Width ≥ 10 pips
  - Bars ≥ 10
  - EMA inside range

### 3. Statistical Analysis
- Calculates trigger rates for each filter
- Identifies time-based patterns
- Analyzes setup distribution
- Computes averages and thresholds

### 4. Recommendations
Generates specific recommendations like:
- "Consider reducing ATR threshold from 7 to 5.2 pips"
- "Increase spread tolerance from 2 to 3 pips"
- "Reduce build-up width threshold from 10 to 7.5 pips"

## Output

### Console Output
The script provides a detailed console report showing:
- Total entries analyzed
- Breakdown of filter triggers (count and percentage)
- Time-based patterns
- Setup distribution
- Specific recommendations

### JSON Output
Full results are saved to `filter_analysis_results.json` with:
- Raw data and statistics
- Complete filter analysis
- Time patterns
- All recommendations

## Understanding the Results

### Critical Issues (🔴)
- Filters triggering >40% of the time
- ATR filter being too restrictive
- Build-up requirements too strict

### Important Issues (🟡)
- Filters triggering 20-40% of the time
- Spread filter being too tight
- News window restrictions too broad

### Time Patterns (⏰)
- Hours with highest no-trade rates
- Session-based filtering issues

### Overall Health (🚨)
- If >90% of entries are no-trades, filters are too restrictive

## Recommended Actions

Based on typical results, you should:

1. **Relax ATR requirements** - Often the biggest culprit
2. **Adjust build-up thresholds** - Second most restrictive
3. **Review news window logic** - May be too conservative
4. **Fine-tune spread tolerance** - Minor but consistent issue

## Implementation

After getting recommendations, update the thresholds in:
- `/Users/shinzato/programing/claude_code/analyze_FX_chart/src/analysis/core_v2.py`
- Look for the `apply_quality_gates` method (lines 220-269)

## Troubleshooting

### Environment Issues
Make sure you have:
- Notion API credentials set (`NOTION_API_KEY`, `NOTION_DB_ID`)
- Virtual environment activated
- Required dependencies installed

### No Data Found
- Check date ranges in Notion
- Verify database permissions
- Confirm entry format matches expected structure

### Permission Errors
```bash
chmod +x run_filter_analysis.sh
```

## Next Steps

1. Run the analysis
2. Review the recommendations  
3. Test with relaxed thresholds in a development environment
4. Gradually implement changes to production
5. Monitor trade frequency improvements
6. Re-run analysis weekly to track improvements