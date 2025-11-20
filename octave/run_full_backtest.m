% run_full_backtest.m
% Master Orchestration Script for Complete Backtesting Pipeline
% Runs baseline backtest, Walk-Forward Analysis, and Monte Carlo validation

function run_full_backtest(symbol, stock_type, years_back, run_wfa, run_mc)
    % Complete backtesting pipeline
    % 
    % Parameters:
    % -----------
    % symbol: string, e.g., 'SPY'
    % stock_type: 'Core' or 'Satellite'
    % years_back: number of years of data to test (default 10)
    % run_wfa: boolean, run Walk-Forward Analysis (default true)
    % run_mc: boolean, run Monte Carlo validation (default true)
    %
    % Example:
    % run_full_backtest('SPY', 'Core', 10, true, true);
    
    % Default parameters
    if nargin < 3, years_back = 10; end
    if nargin < 4, run_wfa = true; end
    if nargin < 5, run_mc = true; end
    
    fprintf('\n');
    fprintf('============================================================\n');
    fprintf('  QUANTITATIVE BACKTESTING SYSTEM - FULL ANALYSIS\n');
    fprintf('============================================================\n\n');
    
    fprintf('Symbol:          %s\n', symbol);
    fprintf('Strategy Type:   %s\n', stock_type);
    fprintf('Data Period:     %d years\n', years_back);
    fprintf('Walk-Forward:    %s\n', iif(run_wfa, 'YES', 'NO'));
    fprintf('Monte Carlo:     %s\n\n', iif(run_mc, 'YES', 'NO'));
    
    timestamp_start = now();
    fprintf('Start Time: %s\n\n', datestr(timestamp_start));
    
    % ========== STEP 0: DATA PREPARATION ==========
    fprintf('============================================================\n');
    fprintf('STEP 0: DATA PREPARATION\n');
    fprintf('============================================================\n\n');
    
    % Check if data file exists
    data_file = sprintf('%s_data.mat', symbol);
    
    if ~exist(data_file, 'file')
        fprintf('⚠️  Data file not found: %s\n', data_file);
        fprintf('Please run Python data exporter first:\n');
        fprintf('  cd ..\n');
        fprintf('  python octave/data_exporter.py\n\n');
        fprintf('Or export specific symbol:\n');
        fprintf('  python -c "from octave.data_exporter import export_for_backtest; ');
        fprintf('export_for_backtest(''%s'', %d)"\n\n', symbol, years_back);
        error('Data file missing. Please export data first.');
    end
    
    fprintf('✅ Data file found: %s\n', data_file);
    load(data_file);
    fprintf('   Data range: %s to %s\n', datestr(dates(1)), datestr(dates(end)));
    fprintf('   Total bars: %d\n\n', length(close));
    
    % ========== STEP 1: BASELINE BACKTEST ==========
    fprintf('============================================================\n');
    fprintf('STEP 1: BASELINE BACKTEST\n');
    fprintf('============================================================\n\n');
    
    % Run baseline backtest with default parameters
    baseline_results = backtest_engine(data_file, stock_type);
    
    % ========== STEP 2: WALK-FORWARD ANALYSIS ==========
    if run_wfa
        fprintf('\n');
        fprintf('============================================================\n');
        fprintf('STEP 2: WALK-FORWARD ANALYSIS\n');
        fprintf('============================================================\n');
        
        wfa_config = struct();
        wfa_config.is_window = 504;   % 2 years
        wfa_config.oos_window = 126;  % 6 months
        wfa_config.step_size = 126;   % Move forward 6 months
        
        try
            wfa_results = walk_forward_analysis(data_file, stock_type, wfa_config);
        catch err
            fprintf('\n⚠️  Walk-Forward Analysis failed: %s\n', err.message);
            fprintf('Continuing with baseline results only...\n\n');
            wfa_results = [];
        end
    else
        fprintf('\n⏩ Skipping Walk-Forward Analysis (disabled)\n\n');
        wfa_results = [];
    end
    
    % ========== STEP 3: MONTE CARLO VALIDATION ==========
    if run_mc
        fprintf('\n');
        fprintf('============================================================\n');
        fprintf('STEP 3: MONTE CARLO VALIDATION\n');
        fprintf('============================================================\n');
        
        % Run with 1000 simulations (can be reduced for faster testing)
        n_sims = 1000;
        fprintf('Running %d simulations (this may take a few minutes)...\n\n', n_sims);
        
        try
            mc_results = monte_carlo_validation(baseline_results, n_sims);
        catch err
            fprintf('\n⚠️  Monte Carlo validation failed: %s\n', err.message);
            fprintf('Continuing with baseline results only...\n\n');
            mc_results = [];
        end
    else
        fprintf('\n⏩ Skipping Monte Carlo Validation (disabled)\n\n');
        mc_results = [];
    end
    
    % ========== FINAL SUMMARY ==========
    fprintf('\n\n');
    fprintf('============================================================\n');
    fprintf('  FINAL SUMMARY\n');
    fprintf('============================================================\n\n');
    
    fprintf('Symbol: %s (%s Strategy)\n\n', symbol, stock_type);
    
    fprintf('BASELINE BACKTEST:\n');
    fprintf('  Total Return:   %+.2f%%\n', baseline_results.total_return);
    fprintf('  CAGR:           %+.2f%%\n', baseline_results.cagr);
    fprintf('  Sharpe Ratio:   %.3f\n', baseline_results.sharpe);
    fprintf('  Max Drawdown:   %.2f%%\n', baseline_results.max_drawdown);
    fprintf('  Alpha vs B&H:   %+.2f%%\n\n', baseline_results.alpha);
    
    if run_wfa && ~isempty(wfa_results)
        fprintf('WALK-FORWARD ANALYSIS:\n');
        fprintf('  Iterations:     %d\n', length(wfa_results.oos_performance));
        fprintf('  Mean OOS Return: %.2f%%\n', mean(wfa_results.oos_performance));
        fprintf('  WFA Efficiency: %.2f', mean(wfa_results.oos_performance) / mean(wfa_results.is_performance));
        if mean(wfa_results.oos_performance) / mean(wfa_results.is_performance) > 0.7
            fprintf(' ✅ Excellent\n\n');
        elseif mean(wfa_results.oos_performance) / mean(wfa_results.is_performance) > 0.5
            fprintf(' ✅ Good\n\n');
        else
            fprintf(' ⚠️  Overfitting detected\n\n');
        end
    end
    
    if run_mc && ~isempty(mc_results)
        fprintf('MONTE CARLO VALIDATION:\n');
        fprintf('  Simulations:    %d\n', mc_results.n_simulations);
        fprintf('  P-value:        %.4f', mc_results.p_value_return);
        if mc_results.is_significant
            fprintf(' ✅ Statistically Significant\n');
        else
            fprintf(' ❌ Not Significant\n');
        end
        fprintf('  95%% Max DD:     %.2f%%\n\n', prctile(mc_results.trade_shuffle_drawdowns, 95));
    end
    
    % ========== RECOMMENDATION ==========
    fprintf('------------------------------------------------------------\n');
    fprintf('🎯 RECOMMENDATION:\n');
    fprintf('------------------------------------------------------------\n');
    
    is_profitable = baseline_results.total_return > 0;
    is_positive_alpha = baseline_results.alpha > 0;
    is_good_sharpe = baseline_results.sharpe > 1.0;
    is_robust = ~run_mc || (mc_results.is_significant && mc_results.p_value_return < 0.05);
    is_not_overfit = ~run_wfa || isempty(wfa_results) || ...
                     (mean(wfa_results.oos_performance) / mean(wfa_results.is_performance) > 0.5);
    
    score = is_profitable + is_positive_alpha + is_good_sharpe + is_robust + is_not_overfit;
    
    if score >= 4
        fprintf('✅ STRONG CANDIDATE for live trading\n');
        fprintf('   Strategy shows consistent profitability with statistical edge.\n');
        fprintf('   Recommend paper trading for 3 months before going live.\n\n');
    elseif score >= 3
        fprintf('⚠️  MARGINAL strategy\n');
        fprintf('   Shows promise but needs further refinement.\n');
        fprintf('   Consider parameter optimization or different market regimes.\n\n');
    else
        fprintf('❌ NOT RECOMMENDED for live trading\n');
        fprintf('   Strategy lacks robustness or statistical significance.\n');
        fprintf('   Back to drawing board - try different approach.\n\n');
    end
    
    % ========== SAVE SUMMARY ==========
    summary_file = sprintf('%s_%s_summary.txt', symbol, stock_type);
    fid = fopen(summary_file, 'w');
    fprintf(fid, 'Backtest Summary: %s (%s Strategy)\n', symbol, stock_type);
    fprintf(fid, 'Date: %s\n\n', datestr(now()));
    fprintf(fid, 'Total Return: %.2f%%\n', baseline_results.total_return);
    fprintf(fid, 'CAGR: %.2f%%\n', baseline_results.cagr);
    fprintf(fid, 'Sharpe: %.3f\n', baseline_results.sharpe);
    fprintf(fid, 'Max Drawdown: %.2f%%\n', baseline_results.max_drawdown);
    if run_mc && ~isempty(mc_results)
        fprintf(fid, 'P-value: %.4f\n', mc_results.p_value_return);
    end
    fclose(fid);
    
    timestamp_end = now();
    elapsed = seconds(timestamp_end - timestamp_start);
    
    fprintf('⏱️  Total Execution Time: %.1f seconds\n', elapsed);
    fprintf('📁 Summary saved to: %s\n\n', summary_file);
    
    fprintf('============================================================\n');
    fprintf('  ANALYSIS COMPLETE\n');
    fprintf('============================================================\n\n');
end


function result = iif(condition, true_val, false_val)
    % Inline if-else helper
    if condition
        result = true_val;
    else
        result = false_val;
    end
end
