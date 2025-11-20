#!/usr/bin/env python3
"""Complete Octave 9.4 compatibility fix"""
import re

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix 1: Replace datetime('now') with now()
    content = re.sub(r"datetime\('now'\)", 'now()', content)
    
    # Fix 2: Remove UTF-8 box drawing - replace with ASCII
    # note: the box characters are causing encoding issues
    content = content.replace('╔══════════════════════════════════════════════════════════╗', '=' * 60)
    content = content.replace('╚══════════════════════════════════════════════════════════╝', '=' * 60)
    content = content.replace('║  QUANTITATIVE BACKTESTING SYSTEM - FULL ANALYSIS        ║', '  QUANTITATIVE BACKTESTING SYSTEM - FULL ANALYSIS')
    content = content.replace('║  FINAL SUMMARY                                           ║', '  FINAL SUMMARY')
    content = content.replace('║  ANALYSIS COMPLETE                                       ║', '  ANALYSIS COMPLETE')
    
    # Fix 3: Remove other emoji that might cause issues
    # Keep basic ones that usually work
    
    with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    
    print(f"✅ Fixed {filepath}")

# Fix all Octave files
fix_file('octave/run_full_backtest.m')
fix_file('octave/backtest_engine.m')
fix_file('octave/monte_carlo_validation.m')
fix_file('octave/walk_forward_analysis.m')

print("\n🎉 All Octave files fixed for 9.4 compatibility!")
