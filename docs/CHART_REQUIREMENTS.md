# Chart Generation Requirements

## Overview
This document outlines the requirements for FX chart generation based on the approved sample charts.

## Visual Design Requirements

### Color Scheme
- **Background**: Dark theme (deep navy/black) - `#0a0e27` or similar
- **Candlesticks**:
  - Bullish (up): Cyan/Teal - `#00E5FF`
  - Bearish (down): Red - `#FF5252`
- **Text**: White for all labels and axis values
- **Grid**: Light gray with low opacity

### Layout
- **Price Axis**: Right side with white text
- **Time Axis**: Bottom with white text
- **Chart Title**: Include timeframe (5m/1h) at top

## Technical Indicators

### Moving Averages (EMA)
Three exponential moving averages to be displayed:
1. **EMA25**: White line - Short-term trend
2. **EMA100**: Yellow line - Medium-term trend  
3. **EMA200**: Red line - Long-term trend

Line specifications:
- Width: 1.5px
- Style: Solid
- Opacity: 0.9

### Current Price Display
- **Horizontal Line**: Dashed line across chart at current price
- **Price Label**: Rectangle with current price value on right axis
- **Color**: Matches last candle color (cyan for up, red for down)

## Chart Elements

### Grid Lines
- **Style**: Dotted lines
- **Color**: Gray with 20% opacity
- **Frequency**: 5-6 horizontal lines, appropriate vertical lines

### Timeframe Label
- **Location**: Chart title
- **Format**: "USDJPY - 5m" or "USDJPY - 1h"
- **Font**: Bold, white color

## Data Requirements

### Price Data
- Minimum 100 candles for proper EMA calculation
- OHLC (Open, High, Low, Close) values required

### Calculation Methods
- EMA calculation using standard exponential smoothing
- All EMAs calculated on close prices

## Output Specifications

### Image Format
- **Format**: PNG
- **Resolution**: 1200x600 pixels
- **DPI**: 100

### File Naming
- Pattern: `{run_id}_{timeframe}.png`
- Example: `abc123_5m.png`

## Implementation Notes

1. Use matplotlib with dark style base
2. Customize colors after applying style
3. Ensure all text is readable on dark background
4. Add legend for EMAs if space permits
5. Handle edge cases where not enough data for EMA200

## Sample Reference
Sample charts are stored in `/chart_sample/` directory for visual reference.